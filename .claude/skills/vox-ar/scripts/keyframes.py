#!/usr/bin/env python3
"""
keyframes.py — generate the image assets for every shot:
  * one text-free PLATE (full-frame collage background) per shot
  * one CUTOUT sticker (background removed) per `cutout` layer

Skips anything already on disk, so re-running is cheap. Writes paths back into beats.json.

usage: python3 scripts/keyframes.py out/<project> [--only 1a,2b] [--force]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presets  # noqa: E402
import styles  # noqa: E402
import paperfx  # noqa: E402
import newsprint  # noqa: E402
from provider import get_provider, remove_background, trim  # noqa: E402


def shot_key(beat, shot):
    return f"{beat['id']}{shot.get('id', '')}"


def load(project_dir):
    p = os.path.join(project_dir, "beats.json")
    with open(p, encoding="utf-8") as f:
        return p, json.load(f)


def save(path, doc):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)


def resolve(project_dir, p):
    return p if os.path.isabs(p) else os.path.join(project_dir, p)


def run(project_dir, only=None, force=False):
    bpath, doc = load(project_dir)
    presets.expand_doc(doc)
    aspect = doc.get("aspect", "9:16")
    theme = doc.get("theme", styles.DEFAULT_THEME)
    prov = get_provider(doc.get("provider"))
    kf_dir = os.path.join(project_dir, "keyframes")
    el_dir = os.path.join(project_dir, "elements")
    os.makedirs(kf_dir, exist_ok=True)
    os.makedirs(el_dir, exist_ok=True)
    print(f"provider={prov.name} theme={theme} aspect={aspect}")

    for beat in doc["beats"]:
        for shot in beat.get("shots", []):
            key = shot_key(beat, shot)
            if only and key not in only:
                continue
            # ---- plate
            plate_path = os.path.join(kf_dir, f"plate_{key}.png")
            if shot.get("plate_path") and os.path.exists(resolve(project_dir, shot["plate_path"])) and not force:
                pass
            elif shot.get("plate_image"):           # user-supplied background image
                shot["plate_path"] = shot["plate_image"]
                shot["plate_kind"] = "image"
            elif shot.get("plate") and shot["plate"] != "auto" and doc.get("plates", "procedural") == "ai" \
                    and prov.name != "placeholder":
                prompt = styles.plate_prompt(shot["plate"], theme, bg=shot.get("bg"), aspect=aspect,
                                             feel=beat.get("feel"))
                shot["plate_prompt"] = prompt
                print(f"[{key}] plate (AI) …")
                img = prov.image(prompt, aspect=aspect)
                img.convert("RGB").save(plate_path, quality=92)
                shot["plate_path"] = os.path.relpath(plate_path, project_dir)
                shot["plate_kind"] = "ai"
            else:                                    # procedural Arabic newsprint — free, instant
                w, h = styles.frame_size(aspect)
                variant = shot.get("bg") or styles.theme(theme).get("plate_variant", "cream")
                variant = variant if variant in ("cream", "white", "graph", "red", "black", "yellow", "blue", "grey") else "cream"
                print(f"[{key}] plate (procedural {variant})")
                newsprint.plate(w, h, variant, seed=abs(hash(key)) % 1000,
                                density=float(shot.get("density", 1.0))).convert("RGB").save(plate_path, quality=92)
                shot["plate_path"] = os.path.relpath(plate_path, project_dir)
                shot["plate_kind"] = "procedural"

            # ---- cutouts
            for i, layer in enumerate(presets.layers_of(shot)):
                if layer.get("type") != "cutout":
                    continue
                dest = os.path.join(el_dir, f"el_{key}_{i}.png")
                if layer.get("path") and os.path.exists(resolve(project_dir, layer["path"])) and not force:
                    continue
                if layer.get("image"):               # user-supplied photo → just key/trim it
                    src = resolve(project_dir, layer["image"])
                    from PIL import Image
                    img = Image.open(src).convert("RGBA")
                    if layer.get("remove_bg", True):
                        img = remove_background(img)
                else:
                    prompt = styles.apply_effects_to_prompt(
                        styles.cutout_prompt(layer["subject"], theme, extra=layer.get("extra")),
                        layer.get("effects"))
                    layer["prompt"] = prompt
                    print(f"[{key}] cutout {i}: {layer['subject'][:50]} …")
                    img = prov.image(prompt, aspect="1:1")
                    img = remove_background(img)
                img = trim(img)
                img.save(dest)
                layer["path"] = os.path.relpath(dest, project_dir)
            save(bpath, doc)
    print("done →", bpath)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--only", default=None, help="comma list of shot keys e.g. 1a,2b")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    run(os.path.abspath(a.project), only=set(a.only.split(",")) if a.only else None, force=a.force)
