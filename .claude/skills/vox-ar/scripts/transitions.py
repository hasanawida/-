#!/usr/bin/env python3
"""
transitions.py — paper transitions between shots, rendered in code from the last frame of shot A and
the first frame of shot B (both are near-still at the cut, so this reads exactly like an editor's transition).

  tear    A is torn away along a jagged diagonal, revealing B (paper fibre edge + shadow)      ← default
  slide   B slides in as a sheet of paper over A (with drop shadow), slight overshoot
  flip    A folds/flips away horizontally like a page, B underneath
  wipe    torn-edge wipe left→right (RTL-friendly: right→left)
  cut     no transition
  Each one is ~0.45 s, and assemble.py drops a paper whoosh SFX on it.

render(a_png, b_png, kind, out_mp4, fps, W, H, dur) → out_mp4
"""
import math
import random
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageChops

import paperfx


def _ease(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def _tear_mask(W, H, progress, seed=3, angle=-0.35):
    """Mask (L) where 255 = show B. A jagged diagonal front sweeps across the frame."""
    rnd = random.Random(seed)
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    span = W + H * abs(math.tan(angle)) + 80
    x = -40 + span * progress
    pts = [(x + 200, -50), (x + 200 + H * math.tan(angle), H + 50)]
    # jagged front
    front = []
    steps = 28
    for i in range(steps + 1):
        y = -50 + (H + 100) * i / steps
        jag = rnd.uniform(-1, 1) * 22 + math.sin(i * 1.7) * 10
        front.append((x + y * math.tan(angle) + jag, y))
    poly = front + [(-200, H + 50), (-200, -50)]
    d.polygon(poly, fill=255)
    return m, front


def render(a_png, b_png, kind, out_mp4, fps=30, W=1920, H=1080, dur=0.45):
    A = Image.open(a_png).convert("RGBA").resize((W, H))
    B = Image.open(b_png).convert("RGBA").resize((W, H))
    n = max(4, int(round(dur * fps)))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-pix_fmt", "yuv420p", out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    fibre = Image.effect_noise((W, H), 60).point(lambda v: 255 if v > 150 else 0)
    for i in range(n):
        p = _ease((i + 1) / n)
        if kind == "slide":
            frame = A.copy()
            over = 1.04 if p > 0.85 else 1.0
            x = int(W * (1 - p) * over)
            sheet = paperfx.add_shadow(B, offset=(-14, 0), blur=14, opacity=160)
            frame.alpha_composite(sheet, (x - (sheet.width - W) // 2, -(sheet.height - H) // 2))
        elif kind == "flip":
            frame = B.copy()
            # A shrinks horizontally toward its left edge like a page folding away, with darkening
            w = max(2, int(W * (1 - p)))
            page = A.resize((w, H), Image.BILINEAR)
            dark = Image.new("RGBA", page.size, (0, 0, 0, int(140 * p)))
            page.alpha_composite(dark)
            page = paperfx.add_shadow(page, offset=(18, 0), blur=16, opacity=150)
            frame.alpha_composite(page, (-(page.width - w) // 2, -(page.height - H) // 2))
        elif kind == "wipe":
            frame = A.copy()
            m = Image.new("L", (W, H), 0)
            x = int(W * (1 - p))
            pts = [(x + i2 * 0 + (18 if (j % 2) else 0), y) for j, y in enumerate(range(0, H + 40, 40)) for i2 in (0,)]
            poly = [(W + 10, -10)] + [(x + (16 if j % 2 else -16), y) for j, y in enumerate(range(-20, H + 40, 40))] + [(W + 10, H + 10)]
            ImageDraw.Draw(m).polygon(poly, fill=255)
            frame = Image.composite(B, A, m)
            edge = m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(2))
            fl = Image.new("RGBA", (W, H), (255, 250, 236, 255)); fl.putalpha(ImageChops.multiply(edge, fibre))
            frame.alpha_composite(fl)
        elif kind == "tear":
            m, front = _tear_mask(W, H, p)
            frame = Image.composite(B, A, m)
            # torn white fibre edge (thin band along the front) + soft shadow falling on A
            soft = m.filter(ImageFilter.GaussianBlur(6))
            band = ImageChops.subtract(soft, m).point(lambda v: min(255, v * 4))        # just outside the front (A side)
            fl = Image.new("RGBA", (W, H), (255, 250, 236, 255))
            fl.putalpha(ImageChops.multiply(band, fibre.point(lambda v: 150 + v // 3)))
            frame.alpha_composite(fl)
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sh.putalpha(ImageChops.subtract(m.filter(ImageFilter.GaussianBlur(18)), m).point(lambda v: min(120, v * 2)))
            frame.alpha_composite(sh)
        else:  # cut
            frame = B.copy()
        proc.stdin.write(frame.tobytes())
    proc.stdin.close(); proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg failed for transition")
    return out_mp4


def last_frame(mp4, out_png):
    # decode the last ~0.5 s and keep overwriting one PNG → the file ends up holding the final frame
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.5", "-i", mp4, "-update", "1", out_png], check=True)
    return out_png


def first_frame(mp4, out_png):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-frames:v", "1", "-update", "1", out_png], check=True)
    return out_png


if __name__ == "__main__":
    import sys
    a, b, kind, out = sys.argv[1:5]
    print(render(a, b, kind, out))
