#!/usr/bin/env python3
"""
flow_export.py — the "no API key" path: export every prompt the project needs as numbered text files
you can paste (or batch-run with a Flow automation extension) in Google Flow / Gemini / any image tool.

  out/<project>/flow/prompts_images.txt   one plate prompt per shot (16:9 or 9:16), text-free
  out/<project>/flow/prompts_cutouts.txt  one prompt per cutout element (white background, for bg removal)
  out/<project>/flow/prompts_motion.txt   one image-to-video prompt per shot (for Veo in Flow: 6 s, one clip)
  out/<project>/flow/README.txt           naming rules so flow_import.py can map files back

Naming rule for downloads:  <shotkey>_plate.*  ·  <shotkey>_cut<N>.*  ·  <shotkey>_veo.mp4   (e.g. 3a_plate.png)

usage: python3 scripts/flow_export.py out/<project> [--seconds 6]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presets  # noqa: E402
import styles   # noqa: E402

CAMERA_TXT = {
    "push_in": "one very slow smooth push-in", "pull_out": "one slow smooth pull-out",
    "pan_l": "one slow flat pan to the left", "pan_r": "one slow flat pan to the right",
    "pan_up": "one slow tilt up", "pan_down": "one slow tilt down", "static": "locked-off camera", "drift": "gentle floating drift",
}


def motion_prompt(shot, feel, seconds):
    cam = CAMERA_TXT.get(shot.get("camera", "push_in"), "one slow push-in")
    motion = shot.get("veo_motion") or ("paper cut-out elements gently bob, tilt and drift at different speeds; "
                                        "halftone dots pulse; torn edges flutter slightly; nothing morphs")
    return (f"{seconds}-second paper-collage motion graphic, printed cut-outs, NOT photoreal. CAMERA (one move only): {cam}. "
            f"ELEMENT MOTION: {motion}. FEEL: {feel or 'tactile, editorial'}. "
            "Keep the layout stable, flat 2D, no 3D rotation, no new objects, no text, rigid paper.")


def run(project_dir, seconds=6):
    bpath = os.path.join(project_dir, "beats.json")
    doc = json.load(open(bpath, encoding="utf-8"))
    presets.expand_doc(doc)
    theme = doc.get("theme", styles.DEFAULT_THEME)
    aspect = doc.get("aspect", "16:9")
    fdir = os.path.join(project_dir, "flow")
    os.makedirs(fdir, exist_ok=True)
    plates, cuts, motions = [], [], []
    for beat in doc["beats"]:
        for shot in beat.get("shots", []):
            key = f"{beat['id']}{shot.get('id', '')}"
            subjects = [L["subject"] for L in presets.layers_of(shot) if L.get("type") == "cutout" and L.get("subject")]
            scene = shot.get("plate") or (", ".join(subjects) + " arranged as an editorial collage with related props"
                                          if subjects else "abstract editorial paper collage with torn clippings and props")
            plates.append(f"[{key}_plate]\n" + styles.plate_prompt(scene, theme, bg=shot.get("bg") if shot.get("bg") not in
                          ("cream", "white", "graph", "red", "black", "yellow", "blue", "grey") else None,
                          aspect=aspect, feel=beat.get("feel")) + "\n")
            for i, L in enumerate(presets.layers_of(shot)):
                if L.get("type") == "cutout" and L.get("subject"):
                    cuts.append(f"[{key}_cut{i}]\n" + styles.apply_effects_to_prompt(
                        styles.cutout_prompt(L["subject"], theme, extra=L.get("extra")), L.get("effects")) + "\n")
            motions.append(f"[{key}_veo]  (upload {key}_plate image, image-to-video, {seconds}s)\n" +
                           motion_prompt(shot, beat.get("feel"), seconds) + "\n")
    open(os.path.join(fdir, "prompts_images.txt"), "w", encoding="utf-8").write("\n".join(plates))
    open(os.path.join(fdir, "prompts_cutouts.txt"), "w", encoding="utf-8").write("\n".join(cuts))
    open(os.path.join(fdir, "prompts_motion.txt"), "w", encoding="utf-8").write("\n".join(motions))
    open(os.path.join(fdir, "README.txt"), "w", encoding="utf-8").write(
        "vox-ar Flow bridge\n"
        "1) Generate each prompt in Google Flow (Nano Banana) or any image tool. Save with the bracketed name,\n"
        "   e.g. 3a_plate.png, 3a_cut0.png, 3a_veo.mp4 (image-to-video, optional).\n"
        "2) Put all files in one folder and run:  python scripts/flow_import.py out/<project> <that folder>\n"
        "3) Then: python run.py out/<project>\n"
        f"Aspect: {aspect} · Theme: {theme} · plates: {len(plates)} · cutouts: {len(cuts)} · motion clips (optional): {len(motions)}\n")
    print(f"exported → {fdir}  ({len(plates)} plates, {len(cuts)} cutouts, {len(motions)} motion prompts)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--seconds", type=int, default=6)
    a = ap.parse_args()
    run(os.path.abspath(a.project), a.seconds)
