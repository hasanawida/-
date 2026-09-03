#!/usr/bin/env python3
"""
beats_from_script.py — turn a compact script file into beats.json (the story wizard's output format).

Script format (UTF-8 text):

    # project: zodiac | aspect: 16:9 | theme: dark-investigative | persona: documentary_male | mood: tense
    # plates: procedural | provider: gemini
    ---
    [hero_right | bg=black | cutout=1960s police officer, chest up | headline=خبر عاجل | stamp=ملف سري | mark=circle | sfx=police siren]
    الرابع من ديسمبر 1966. مدينة فاليخو، كاليفورنيا. شرطي دورية يمر بجانب سيارة متوقفة قرب مدرسة مغلقة.
    ---
    [title | bg=red | headline=رسائل مشفّرة | sub=موقّعة بدائرة وصليب | transition=slide]
    [stats | headline=الشفرات الأربع | items=الأولى:1, الثانية:1, الثالثة:1, الرابعة:0]
    الصحف تنشر ثلاثاً من أصل أربع شفرات؛ الرابعة تبقى لغزاً لعقود.

Rules: blocks separated by `---`; each `[...]` line is one shot (preset first, then key=value pairs
separated by `|`); the remaining lines are the beat's narration. `items` = "label:value, …" (or plain
labels for list/timeline; "text:true/false" for checklist). Any key not listed is passed through to
the shot (camera, plate, dur, effects, sfx_hint, transition, image, …).
If a beat has no `[...]` line, a preset is chosen automatically (rotating) with the first 4 words as headline.

usage: python3 scripts/beats_from_script.py script.txt out/<project>
"""
import json
import os
import re
import sys

ROTATION = ["hero_right", "title", "hero_left", "number", "hero_center", "quote"]
LIST_KEYS = {"effects", "effects2", "fx"}
NUM_KEYS = {"dur", "value", "parallax", "camera_strength", "headline_size", "sub_size", "cutout_w", "cutout_rot", "density"}
BOOL_KEYS = {"tape", "pin", "flat"}


def _val(key, v):
    v = v.strip()
    if key in LIST_KEYS:
        return [s.strip() for s in v.split(",") if s.strip()]
    if key in NUM_KEYS:
        try:
            return float(v) if "." in v else int(v)
        except ValueError:
            return v
    if key in BOOL_KEYS:
        return v.lower() in ("1", "true", "yes", "نعم")
    if key == "items":
        out = []
        for it in v.split(","):
            it = it.strip()
            if ":" in it:
                a, b = it.rsplit(":", 1)
                b = b.strip()
                if b.lower() in ("true", "false"):
                    out.append([a.strip(), b.lower() == "true"])
                else:
                    try:
                        out.append([a.strip(), float(b) if "." in b else int(b)])
                    except ValueError:
                        out.append([a.strip(), b])
            elif it:
                out.append(it)
        return out
    if key == "callouts":   # text@x,y>tx,ty ; text@...
        out = []
        for c in v.split(";"):
            m = re.match(r"\s*(.+?)@([\d.]+),([\d.]+)>([\d.]+),([\d.]+)", c)
            if m:
                out.append({"text": m.group(1).strip(), "x": float(m.group(2)), "y": float(m.group(3)),
                            "tx": float(m.group(4)), "ty": float(m.group(5))})
        return out
    if key == "sfx":
        return v
    return v


def parse_shot(line):
    inner = line.strip()[1:-1]
    parts = [p.strip() for p in inner.split("|")]
    shot = {}
    if parts and "=" not in parts[0]:
        shot["preset"] = parts[0]
        parts = parts[1:]
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            k = k.strip()
            if k == "sfx":
                shot["sfx_hint"] = v.strip()
            else:
                shot[k] = _val(k, v)
    return shot


def parse(text):
    header = {}
    body = []
    for ln in text.splitlines():
        if ln.startswith("#") and not body and "|" in ln or (ln.startswith("#") and ":" in ln and not body):
            for p in ln.lstrip("#").split("|"):
                if ":" in p:
                    k, v = p.split(":", 1)
                    header[k.strip()] = v.strip()
        else:
            body.append(ln)
    blocks = [b.strip() for b in "\n".join(body).split("---") if b.strip()]
    beats = []
    for i, b in enumerate(blocks, 1):
        shots, narr = [], []
        for ln in b.splitlines():
            if re.match(r"^\s*\[.*\]\s*$", ln):
                shots.append(parse_shot(ln))
            elif ln.strip():
                narr.append(ln.strip())
        narration = " ".join(narr)
        if not shots:
            words = narration.split()
            shots = [{"preset": ROTATION[(i - 1) % len(ROTATION)], "headline": " ".join(words[:4])}]
        for j, s in enumerate(shots):
            s.setdefault("id", "abcdefgh"[j])
            s.setdefault("dur", 4.5 if len(shots) > 1 else min(7.0, max(3.5, len(narration.split()) / 2.4)))
            s.setdefault("camera", ["push_in", "pan_r", "pull_out", "pan_l", "static", "drift"][(i + j) % 6])
        beats.append({"id": i, "narration": narration, "shots": shots})
    return header, beats


def build(script_path, project_dir):
    text = open(script_path, encoding="utf-8").read()
    header, beats = parse(text)
    name = header.get("project") or os.path.basename(project_dir.rstrip("/\\"))
    doc = {
        "project": name,
        "topic": header.get("topic", name),
        "language": "ar",
        "aspect": header.get("aspect", "16:9"),
        "fps": 30,
        "theme": header.get("theme", "arabic-newsprint"),
        "provider": header.get("provider", "gemini"),
        "plates": header.get("plates", "procedural"),
        "parallax": 1.0,
        "fx": ["dust", "sweep"],
        "transitions": {"default": header.get("transition", "tear"), "dur": 0.5},
        "tts": {"engine": header.get("tts", "edge"), "persona": header.get("persona", "documentary_male")},
        "music": {"path": header.get("music", "auto"), "mood": header.get("mood", "investigative"), "gain_db": -18},
        "captions": {"enabled": True, "style": "highlight", "bar": "white", "fill": "black",
                     "size": 0.05 if header.get("aspect", "16:9") == "16:9" else 0.034,
                     "position": 0.86 if header.get("aspect", "16:9") == "16:9" else 0.82, "max_words": 5},
        "beats": beats,
    }
    os.makedirs(project_dir, exist_ok=True)
    out = os.path.join(project_dir, "beats.json")
    json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    words = sum(len(b["narration"].split()) for b in beats)
    shots = sum(len(b["shots"]) for b in beats)
    print(f"{len(beats)} beats · {shots} shots · {words} words (~{words / 2.4:.0f}s) → {out}")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    build(sys.argv[1], os.path.abspath(sys.argv[2]))
