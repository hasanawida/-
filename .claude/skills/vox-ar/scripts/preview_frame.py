#!/usr/bin/env python3
"""
preview_frame.py — GATE 2 helper: render one finished-looking still per shot (all layers in,
captions off) to out/<project>/preview/frame_<key>.png, plus a contact sheet.
Fast (seconds) — look at these before spending minutes on animate.py.

usage: python3 scripts/preview_frame.py out/<project> [--t 0.9] [--only 1a,2b]
"""
import argparse
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animate   # noqa: E402
import paperfx   # noqa: E402
import presets  # noqa: E402
import styles    # noqa: E402


def run(project_dir, t_frac=0.9, only=None):
    bpath = os.path.join(project_dir, "beats.json")
    with open(bpath, encoding="utf-8") as f:
        doc = json.load(f)
    presets.expand_doc(doc)
    W, H = styles.frame_size(doc.get("aspect", "9:16"))
    CW, CH = int(W * animate.SUPER), int(H * animate.SUPER)
    pdir = os.path.join(project_dir, "preview")
    os.makedirs(pdir, exist_ok=True)
    frames = []
    for beat in doc["beats"]:
        for shot in beat.get("shots", []):
            key = f"{beat['id']}{shot.get('id', '')}"
            if only and key not in only:
                continue
            if not shot.get("plate_path"):
                print(f"[{key}] no plate yet — run keyframes.py"); continue
            dur = float(shot.get("dur", 4))
            frame = animate.compose_still(doc, shot, dur, dur * t_frac, project_dir, W, H)
            out = os.path.join(pdir, f"frame_{key}.png")
            frame.convert("RGB").save(out)
            frames.append((key, frame))
            print(f"[{key}] → {out}")
    if frames:
        th = 480
        tiles = [f.convert("RGB").resize((int(W * th / H), th)) for _, f in frames]
        sheet = Image.new("RGB", (sum(t.width for t in tiles) + 8 * (len(tiles) + 1), th + 16), (30, 30, 30))
        x = 8
        for t in tiles:
            sheet.paste(t, (x, 8)); x += t.width + 8
        sp = os.path.join(pdir, "contact_sheet.png")
        sheet.save(sp)
        print("contact sheet →", sp)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--t", type=float, default=0.9)
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    run(os.path.abspath(a.project), a.t, set(a.only.split(",")) if a.only else None)
