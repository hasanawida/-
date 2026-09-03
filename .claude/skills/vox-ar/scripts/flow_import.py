#!/usr/bin/env python3
"""
flow_import.py — map files generated outside (Google Flow, Gemini app, any tool) back into the project.

Looks in <folder> for files named <shotkey>_plate.*, <shotkey>_cut<N>.*, <shotkey>_veo.mp4 (see flow_export.py),
copies them into the project and sets plate_path / cutout paths / clip_path (+ motion: veo) in beats.json.
Cutouts get background removal + trimming like generated ones. Anything not found stays as it was
(procedural plate / generated later) — so partial batches are fine.

usage: python3 scripts/flow_import.py out/<project> <folder>
"""
import glob
import json
import os
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presets  # noqa: E402
from provider import remove_background, trim  # noqa: E402

IMG = (".png", ".jpg", ".jpeg", ".webp")


def run(project_dir, folder):
    bpath = os.path.join(project_dir, "beats.json")
    doc = json.load(open(bpath, encoding="utf-8"))
    presets.expand_doc(doc)
    files = {os.path.splitext(os.path.basename(p))[0].lower(): p for p in glob.glob(os.path.join(folder, "*"))}
    kf, el, vd = (os.path.join(project_dir, d) for d in ("keyframes", "elements", "veo"))
    for d in (kf, el, vd):
        os.makedirs(d, exist_ok=True)
    n = 0
    for beat in doc["beats"]:
        for shot in beat.get("shots", []):
            key = f"{beat['id']}{shot.get('id', '')}".lower()
            p = files.get(f"{key}_plate")
            if p and p.lower().endswith(IMG):
                dest = os.path.join(kf, f"plate_{key}.png")
                Image.open(p).convert("RGB").save(dest)
                shot["plate_path"] = os.path.relpath(dest, project_dir); shot["plate_kind"] = "ai"; n += 1
            v = files.get(f"{key}_veo")
            if v and v.lower().endswith(".mp4"):
                dest = os.path.join(vd, f"veo_{key}.mp4")
                shutil.copy(v, dest)
                shot["clip_path"] = os.path.relpath(dest, project_dir); shot["motion"] = "veo"; n += 1
            for i, L in enumerate(presets.layers_of(shot)):
                c = files.get(f"{key}_cut{i}")
                if c and c.lower().endswith(IMG) and L.get("type") == "cutout":
                    img = trim(remove_background(Image.open(c).convert("RGBA")))
                    dest = os.path.join(el, f"el_{key}_{i}.png")
                    img.save(dest)
                    L["path"] = os.path.relpath(dest, project_dir); n += 1
    json.dump(doc, open(bpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"imported {n} file(s) → {bpath}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    run(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
