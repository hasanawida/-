#!/usr/bin/env python3
"""
veo_clips.py — OPTIONAL, PAID. Animate the plate of shots marked "motion": "veo" with Google Veo
(Gemini API, paid tier). Layers/text are still composited by animate.py on top of the clip, so
Arabic text never touches the video model.

Only runs for shots with "motion": "veo" and no clip yet. Prints the count and asks for
confirmation unless --yes is passed.

usage: python3 scripts/veo_clips.py out/<project> [--yes]
"""
import argparse
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provider import get_provider  # noqa: E402

CAMERA_TXT = {
    "push_in": "one very slow smooth push-in", "pull_out": "one slow smooth pull-out",
    "pan_l": "one slow flat pan to the left", "pan_r": "one slow flat pan to the right", "static": "locked-off camera",
}


def prompt_for(shot, feel):
    cam = CAMERA_TXT.get(shot.get("camera", "push_in"), "one slow smooth push-in")
    motion = shot.get("veo_motion") or ("cut-out paper elements gently bob, tilt and drift; halftone dots pulse; "
                                        "paper edges flutter slightly")
    return ("Animate this still into a mixed-media paper-collage MOTION GRAPHIC, printed cut-outs, not photoreal. "
            f"CAMERA (one move only): {cam}. ELEMENT MOTION: {motion}. FEEL: {feel or 'tactile, editorial'}. "
            "CONSTRAINTS: keep the layout stable, stay flat 2D, no 3D rotation, no perspective change, "
            "no new objects, no text, rigid paper — no morph/melt.")


def run(project_dir, yes=False):
    bpath = os.path.join(project_dir, "beats.json")
    with open(bpath, encoding="utf-8") as f:
        doc = json.load(f)
    todo = [(b, s) for b in doc["beats"] for s in b.get("shots", [])
            if s.get("motion") == "veo" and not (s.get("clip_path") and os.path.exists(os.path.join(project_dir, s["clip_path"])))]
    if not todo:
        print("no veo shots pending"); return
    print(f"{len(todo)} Veo generation(s) — this is PAID on the Gemini API.")
    if not yes and input("continue? [y/N] ").strip().lower() != "y":
        return
    prov = get_provider(doc.get("provider"))
    cdir = os.path.join(project_dir, "veo")
    os.makedirs(cdir, exist_ok=True)
    for beat, shot in todo:
        key = f"{beat['id']}{shot.get('id', '')}"
        plate = Image.open(os.path.join(project_dir, shot["plate_path"]))
        out = os.path.join(cdir, f"veo_{key}.mp4")
        print(f"[{key}] veo …")
        prov.veo(prompt_for(shot, beat.get("feel")), plate, out, aspect=doc.get("aspect", "9:16"),
                 duration=int(shot.get("veo_duration", 8)))
        shot["clip_path"] = os.path.relpath(out, project_dir)
        with open(bpath, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
    print("done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    run(os.path.abspath(a.project), yes=a.yes)
