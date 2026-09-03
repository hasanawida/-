#!/usr/bin/env python3
"""
depth.py — monocular depth for 2.5D parallax, fully offline & free.

Uses MiDaS v2.1 small (ONNX, ~65 MB, MIT) through onnxruntime (already installed with rembg).
The model is fetched once from the official GitHub release into ~/.voxar/models/.
If the model can't be fetched, depth() returns None and the animator falls back to
cutout-only parallax (still moves, just without splitting the background).

depth(img) -> PIL "L" image, same size as img, 0 = far … 255 = near.
"""
import os
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageFilter

MODEL_URL = "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"
MODEL_DIR = os.path.join(os.path.expanduser("~"), ".voxar", "models")
MODEL_PATH = os.environ.get("VOXAR_DEPTH_MODEL", os.path.join(MODEL_DIR, "midas_small.onnx"))

_session = None


def _load():
    global _session
    if _session is not None:
        return _session
    if _session is False:
        return None
    try:
        if not os.path.exists(MODEL_PATH):
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            print(f"  [depth] downloading MiDaS small (65 MB) …", file=sys.stderr)
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH + ".part")
            os.replace(MODEL_PATH + ".part", MODEL_PATH)
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = max(1, (os.cpu_count() or 2) // 2)
        _session = ort.InferenceSession(MODEL_PATH, so, providers=["CPUExecutionProvider"])
        return _session
    except Exception as e:
        print(f"  [depth] unavailable ({str(e)[:80]}) — parallax limited to cutouts", file=sys.stderr)
        _session = False
        return None


def depth(img: Image.Image, smooth=6) -> Image.Image | None:
    s = _load()
    if s is None:
        return None
    w, h = img.size
    x = np.asarray(img.convert("RGB").resize((256, 256), Image.BICUBIC), dtype=np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array([0.229, 0.224, 0.225], dtype=np.float32)
    x = x.transpose(2, 0, 1)[None]
    out = s.run(None, {s.get_inputs()[0].name: x})[0][0]      # inverse depth: bigger = nearer
    lo, hi = np.percentile(out, 2), np.percentile(out, 98)
    d = np.clip((out - lo) / max(1e-6, hi - lo), 0, 1)
    dm = Image.fromarray((d * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    if smooth:
        dm = dm.filter(ImageFilter.GaussianBlur(smooth))
    return dm


def bands(depth_map: Image.Image, n=3, feather=18, split=None):
    """Split a depth map into n feathered masks from far to near (list of 'L' images) + mean depth.
    `split` (0..1) overrides the quantile edges, e.g. split=0.62 with n=2 → near band = nearest 38%."""
    d = np.asarray(depth_map, dtype=np.float32) / 255.0
    edges = np.quantile(d, [split] if (split and n == 2) else np.linspace(0, 1, n + 1)[1:-1])
    out = []
    lo = -1.0
    for i in range(n):
        hi = edges[i] if i < n - 1 else 2.0
        m = ((d > lo) & (d <= hi)).astype(np.uint8) * 255
        mask = Image.fromarray(m).filter(ImageFilter.GaussianBlur(feather))
        z = float(d[(d > lo) & (d <= hi)].mean()) if m.any() else 0.5
        out.append((mask, z))
        lo = hi
    return out


if __name__ == "__main__":
    src = sys.argv[1]
    im = Image.open(src)
    dm = depth(im)
    if dm is None:
        print("no depth")
    else:
        dm.save("/tmp/depth.png")
        print("saved /tmp/depth.png", dm.size)
