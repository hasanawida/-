#!/usr/bin/env python3
"""
qa.py — the supervisor (المراقب). Reviews a project BEFORE and AFTER rendering and writes a fix list.

Geometric / editorial checks (no API needed):
  overlap        layers whose boxes collide (headline over cutout face, stamp over headline …)
  caption_band   any layer sitting in the caption band (y 0.76–0.92 portrait / 0.80–0.94 landscape)
  offscreen      layer partly outside the frame
  text_overflow  headline wider than 92% of the frame / more than 3 lines
  pace           narration words/sec too fast (> 3.2) or too slow (< 1.6); shot < 2.5 s or > 8 s
  density        more than 7 layers in one shot, or no visual event for > 2 s
  repetition     same preset in consecutive shots; same bg for 4+ shots in a row
  missing        cutout without generated image, shot without plate
  facts          numbers in headlines that never appear in the narration (possible hallucination)
  audio          beat narration audio much longer than its shots (> +40%)

Visual review (optional, free): with GEMINI_API_KEY, sends preview/contact_sheet.png to Gemini with a rubric
and appends its notes (composition, readability, style consistency, Arabic text quality).

Output: out/<project>/qa_report.json + a readable summary. Exit code 1 if any "error"-severity issue.

usage: python3 scripts/qa.py out/<project> [--no-vision] [--fix]   (--fix applies safe auto-fixes: caption band, offscreen)
"""
import argparse
import json
import os
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presets   # noqa: E402
import styles    # noqa: E402
import artext    # noqa: E402
import paperfx   # noqa: E402


def _box(L, W, H):
    """Approximate bounding box (x0,y0,x1,y1) in frame fractions for a layer."""
    t = L.get("type")
    x, y = float(L.get("x", 0.5)), float(L.get("y", 0.5))
    if t in ("cutout", "image"):
        w = float(L.get("w", 0.4)); h = w * W / H * 1.0          # assume square-ish sticker
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    if t == "headline":
        size = float(L.get("size", 0.055)) * H
        fnt = artext.font(int(size))
        d = ImageDraw.Draw(Image.new("RGBA", (2, 2)))
        max_w = int(W * float(L.get("max_w", 0.88)))
        lines = artext.wrap(d, L["text"], fnt, max_w)
        tw = max(artext.text_width(d, ln, fnt) for ln in lines) + size * 0.7
        th = len(lines) * size * 1.35
        return (x - tw / W / 2, y - th / H / 2, x + tw / W / 2, y + th / H / 2, len(lines))
    if t == "stamp":
        size = float(L.get("size", 0.045)) * H
        n = len(L.get("text", "")) * 0.6 * size + size
        return (x - n / W / 2, y - size / H, x + n / W / 2, y + size / H)
    if t in ("circle",):
        w, h = float(L.get("w", 0.3)), float(L.get("h", 0.3))
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    if t == "bars":
        w, h = float(L.get("w", 0.5)), float(L.get("h", 0.35))
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    if t in ("sticky", "bubble", "badge", "vs", "counter", "timeline", "callout", "check", "cross"):
        s = float(L.get("size", 0.1)) * (4 if t in ("sticky", "counter") else 1.6)
        w = (float(L.get("w", 0.8)) if t == "timeline" else s * H / W)
        return (x - w / 2, y - s / 2, x + w / 2, y + s / 2)
    return None


def _inter(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    ia = (x1 - x0) * (y1 - y0)
    return ia / max(1e-6, min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1])))


def check(doc, project_dir):
    issues = []
    W, H = styles.frame_size(doc.get("aspect", "9:16"))
    portrait = H > W
    band = (0.76, 0.92) if portrait else (0.80, 0.94)
    cap_on = doc.get("captions", {}).get("enabled", True)
    prev_preset, bg_run, last_bg = None, 0, None

    def add(sev, code, key, msg, fix=None):
        issues.append({"severity": sev, "code": code, "shot": key, "msg": msg, **({"fix": fix} if fix else {})})

    for beat in doc["beats"]:
        shots = beat.get("shots", [])
        narr = beat.get("narration", "")
        words = len(narr.split())
        planned = sum(float(s.get("dur", 4)) for s in shots) or 1
        wps = words / planned
        if words and wps > 3.2:
            add("warn", "pace", f"{beat['id']}", f"بيت {beat['id']}: {wps:.1f} كلمة/ث — أسرع من المريح (خفّف النص أو طوّل اللقطات)")
        if words and wps < 1.6:
            add("info", "pace", f"{beat['id']}", f"بيت {beat['id']}: {wps:.1f} كلمة/ث — بطيء (قصّر اللقطات أو أضف حدثاً بصرياً)")
        ad = float(beat.get("audio_duration", 0) or 0)
        if ad and ad > planned * 1.4:
            add("warn", "audio", f"{beat['id']}", f"بيت {beat['id']}: الصوت {ad:.1f}ث مقابل لقطات {planned:.1f}ث — اللقطات ستتمدد كثيراً؛ أضف لقطة")
        nums_narr = set(re.findall(r"\d+", narr))
        for shot in shots:
            key = f"{beat['id']}{shot.get('id', '')}"
            d = float(shot.get("dur", 4))
            if d < 2.5:
                add("warn", "pace", key, f"{key}: مدة {d}ث قصيرة جداً")
            if d > 8:
                add("warn", "pace", key, f"{key}: مدة {d}ث طويلة — قسّمها")
            layers = presets.layers_of(shot)
            if len(layers) > 7:
                add("warn", "density", key, f"{key}: {len(layers)} طبقة — أكثر من 7 (ضجيج)")
            ats = sorted(float(L.get("at", 0)) for L in layers)
            gaps = [b - a for a, b in zip([0] + ats, ats + [d])]
            if gaps and max(gaps) > 2.4 and d > 3:
                add("info", "density", key, f"{key}: فجوة {max(gaps):.1f}ث بدون حدث بصري")
            if shot.get("preset") and shot.get("preset") == prev_preset:
                add("info", "repetition", key, f"{key}: نفس القالب '{prev_preset}' مرتين متتاليتين")
            prev_preset = shot.get("preset") or prev_preset
            bg = shot.get("bg", "cream")
            bg_run = bg_run + 1 if bg == last_bg else 1
            last_bg = bg
            if bg_run == 4:
                add("info", "repetition", key, f"{key}: نفس الخلفية '{bg}' في 4 لقطات متتالية")
            if not shot.get("plate_path"):
                add("info", "missing", key, f"{key}: لا لوحة بعد (شغّل keyframes)")
            boxes = []
            for L in layers:
                b = _box(L, W, H)
                if not b:
                    continue
                if L.get("type") == "cutout" and not L.get("path"):
                    add("info", "missing", key, f"{key}: قصاصة '{L.get('subject', '')[:30]}' لم تُولَّد بعد")
                if L.get("type") == "headline":
                    nlines = b[4]
                    if nlines > 3:
                        add("warn", "text_overflow", key, f"{key}: العنوان '{L['text'][:24]}…' {nlines} أسطر — قصّره", )
                    if (b[2] - b[0]) > 0.92:
                        add("warn", "text_overflow", key, f"{key}: العنوان أعرض من الإطار")
                    for n in re.findall(r"\d+", L["text"]):
                        if n not in nums_narr and len(n) >= 2:
                            add("warn", "facts", key, f"{key}: الرقم {n} في العنوان غير موجود في التعليق — تأكد منه")
                bb = b[:4]
                if bb[0] < -0.02 or bb[1] < -0.02 or bb[2] > 1.02 or bb[3] > 1.02:
                    add("warn", "offscreen", key, f"{key}: '{L.get('text') or L.get('type')}' يخرج عن الإطار", fix="clamp")
                if cap_on and L.get("type") in ("headline", "stamp", "counter", "sticky", "bubble") and bb[3] > band[0] and bb[1] < band[1]:
                    add("warn", "caption_band", key, f"{key}: '{L.get('text', L.get('type'))[:24]}' يقع في شريط الكابشن", fix="lift")
                boxes.append((L, bb))
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    La, ba = boxes[i]; Lb, bb2 = boxes[j]
                    ta, tb = La.get("type"), Lb.get("type")
                    if {ta, tb} & {"circle", "arrow", "underline", "tape", "pin", "callout", "bigquote"}:
                        continue                      # marks are meant to overlap
                    ov = _inter(ba, bb2)
                    if "headline" not in (ta, tb):
                        continue
                    both_text = ta == "headline" and tb == "headline"
                    if (both_text and ov > 0.35) or (not both_text and ov > 0.6):
                        add("warn", "overlap", key, f"{key}: '{La.get('text', ta)[:18]}' يتداخل مع '{Lb.get('text', tb)[:18]}' ({int(ov * 100)}%)")
                    elif ov > 0.35:
                        add("info", "overlap", key, f"{key}: '{La.get('text', ta)[:18]}' فوق '{Lb.get('text', tb)[:18]}' ({int(ov * 100)}%) — مقصود؟")
    return issues


def apply_fixes(doc, issues):
    n = 0
    band_lift = {}
    for it in issues:
        if it.get("fix") == "lift":
            band_lift[it["shot"]] = True
    for beat in doc["beats"]:
        for shot in beat.get("shots", []):
            key = f"{beat['id']}{shot.get('id', '')}"
            for L in presets.layers_of(shot):
                y = float(L.get("y", 0.5))
                if key in band_lift and L.get("type") in ("headline", "stamp", "counter", "sticky", "bubble") and y > 0.72:
                    L["y"] = 0.70; n += 1
                for k in ("x", "y"):
                    v = float(L.get(k, 0.5))
                    if v < 0.06 or v > 0.94:
                        L[k] = min(0.94, max(0.06, v)); n += 1
            if shot.get("preset") and key in band_lift:   # freeze this shot's layers so the fix survives re-expansion
                shot["layers"] = presets.layers_of(shot)
                shot["frozen_preset"] = shot.pop("preset")
                shot.pop("_layers", None)
    return n


def vision_review(project_dir, doc):
    sheet = os.path.join(project_dir, "preview", "contact_sheet.png")
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key or not os.path.exists(sheet):
        return None
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
        img = Image.open(sheet)
        if img.width > 3000:
            img = img.resize((3000, int(img.height * 3000 / img.width)))
        import io
        buf = io.BytesIO(); img.save(buf, "JPEG", quality=85)
        rubric = (
            "You are a senior motion-graphics art director reviewing frames of an Arabic Vox-style paper-collage explainer. "
            "Each tile is one shot. Review for: (1) readability of Arabic headlines (size, contrast, overlap), "
            "(2) composition balance and negative space, (3) style consistency across tiles, (4) any garbled or "
            "mirrored Arabic letters, (5) cut-outs that look cheap or off-topic, (6) caption band clutter at the bottom. "
            "Return STRICT JSON: {\"score\": 0-10, \"issues\": [{\"tile\": n, \"severity\": \"warn|error|info\", "
            "\"msg\": \"...\"}], \"praise\": [\"...\"], \"top_fixes\": [\"...\"]}. Messages in Arabic.")
        resp = client.models.generate_content(
            model=os.environ.get("VOXAR_VISION_MODEL", "gemini-2.5-flash"),
            contents=[types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"), rubric],
            config=types.GenerateContentConfig(response_mime_type="application/json"))
        return json.loads(resp.text)
    except Exception as e:
        return {"error": str(e)[:200]}


def run(project_dir, vision=True, fix=False):
    bpath = os.path.join(project_dir, "beats.json")
    doc = json.load(open(bpath, encoding="utf-8"))
    presets.expand_doc(doc)
    issues = check(doc, project_dir)
    report = {"issues": issues, "counts": {s: sum(1 for i in issues if i["severity"] == s) for s in ("error", "warn", "info")}}
    if fix:
        report["auto_fixed"] = apply_fixes(doc, issues)
        json.dump(doc, open(bpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if vision:
        v = vision_review(project_dir, doc)
        if v:
            report["vision"] = v
    json.dump(report, open(os.path.join(project_dir, "qa_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"QA: {report['counts']['error']} error · {report['counts']['warn']} warn · {report['counts']['info']} info"
          + (f" · auto-fixed {report.get('auto_fixed', 0)}" if fix else ""))
    for it in issues:
        if it["severity"] != "info":
            print(f"  [{it['severity']}] {it['msg']}")
    if report.get("vision") and "score" in report["vision"]:
        v = report["vision"]
        print(f"  vision score {v.get('score')}/10 — top fixes: " + " | ".join(v.get("top_fixes", [])[:3]))
    return 1 if report["counts"]["error"] else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--no-vision", action="store_true")
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()
    sys.exit(run(os.path.abspath(a.project), vision=not a.no_vision, fix=a.fix))
