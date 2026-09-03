#!/usr/bin/env python3
"""
paperfx.py — the "newspaper collage" look, done in code.

Everything the Vox / تريكات style needs that should NOT be trusted to an image
model: paper-cutout borders + drop shadows, torn edges, red pen circles,
hand-drawn arrows, rubber stamps, highlight bars behind Arabic headlines,
censor bars, tape strips, pins, paper grain / vignette overlays.

All functions return RGBA images (or draw into one) so the animator can
transform and composite them per frame.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps

import artext

# ---------- palette (تريكات / Vox newsprint) ----------
PALETTE = {
    "paper":      (236, 226, 204, 255),   # aged newsprint cream
    "paper_dark": (214, 200, 170, 255),
    "ink":        (24, 22, 20, 255),
    "red":        (196, 30, 32, 255),     # stamp / tape red
    "yellow":     (247, 201, 44, 255),    # highlighter yellow
    "white":      (250, 247, 240, 255),
    "black":      (12, 12, 12, 255),
    "blue":       (30, 60, 120, 255),
}


THEME_NAME = "arabic-newsprint"


def rgba(c):
    if isinstance(c, str):
        return PALETTE.get(c, PALETTE["ink"])
    return tuple(c) if len(c) == 4 else tuple(c) + (255,)


# ---------- geometry helpers ----------
def _jagged_rect(w, h, jag=6, seed=0):
    """Polygon of a rectangle with torn (jagged) edges."""
    rnd = random.Random(seed)
    pts = []
    step = max(8, min(w, h) // 12)
    for x in range(0, w, step):
        pts.append((x, rnd.randint(0, jag)))
    for y in range(0, h, step):
        pts.append((w - rnd.randint(0, jag), y))
    for x in range(w, 0, -step):
        pts.append((x, h - rnd.randint(0, jag)))
    for y in range(h, 0, -step):
        pts.append((rnd.randint(0, jag), y))
    return pts


def torn_paper(w, h, color="paper", jag=None, seed=0, shadow=True):
    """A torn-edged paper rectangle (RGBA) with a soft drop shadow."""
    jag = jag or max(4, min(w, h) // 25)
    pad = 12
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(x + pad, y + pad) for x, y in _jagged_rect(w, h, jag, seed)]
    d.polygon(pts, fill=rgba(color))
    # fibrous lighter rim
    d.line(pts + [pts[0]], fill=(255, 255, 255, 90), width=2)
    if shadow:
        img = add_shadow(img, offset=(5, 7), blur=6, opacity=110)
    return img


def add_shadow(img, offset=(6, 8), blur=6, opacity=120):
    """Return img with a soft drop shadow composited underneath (canvas grows)."""
    grow = blur * 3 + max(abs(offset[0]), abs(offset[1]))
    canvas = Image.new("RGBA", (img.width + grow * 2, img.height + grow * 2), (0, 0, 0, 0))
    alpha = img.split()[3]
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(alpha.point(lambda a: a * opacity // 255))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh, (grow + offset[0], grow + offset[1]))
    canvas.alpha_composite(img, (grow, grow))
    return canvas


def cutout(img, border=10, border_color="white", shadow=True, halftone=False, bw=False):
    """Turn an RGBA sticker into a scissor-cut paper cutout: white rim + shadow."""
    img = img.convert("RGBA")
    if bw:
        g = ImageOps.grayscale(img)
        g = ImageOps.autocontrast(g, cutoff=2)
        rgb = Image.merge("RGB", (g, g, g))
        img = Image.merge("RGBA", (*rgb.split(), img.split()[3]))
    if halftone:
        img = apply_halftone(img)
    alpha = img.split()[3]
    if border > 0:
        rim = alpha.filter(ImageFilter.MaxFilter(border * 2 + 1))
        rim_img = Image.new("RGBA", img.size, rgba(border_color))
        rim_img.putalpha(rim)
        base = Image.new("RGBA", img.size, (0, 0, 0, 0))
        base.alpha_composite(rim_img)
        base.alpha_composite(img)
        img = base
    if shadow:
        img = add_shadow(img)
    return img


def apply_halftone(img, cell=6, strength=0.55):
    """Cheap halftone: multiply luminance by a dot grid (keeps alpha)."""
    w, h = img.size
    dots = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(dots)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            r = cell * 0.5 * strength
            d.ellipse((x - r, y - r, x + r, y + r), fill=int(255 * (1 - strength * 0.5)))
    rgb = img.convert("RGB")
    dots_rgb = Image.merge("RGB", (dots, dots, dots))
    out = ImageChops.multiply(rgb, dots_rgb)
    out = Image.blend(rgb, out, 0.5)
    return Image.merge("RGBA", (*out.split(), img.split()[3]))


# ---------- text blocks ----------
def highlight_text(text, size=90, family="cairo", fill="black", bar="yellow", rot=-2.0,
                   pad_x=28, pad_y=6, torn=True, seed=1, max_w=None):
    """Headline on a highlighter bar (yellow/red/white) — the signature تريكات block.
    Multi-line: each line gets its own bar. Returns RGBA."""
    fnt = artext.font(size, family)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = artext.wrap(tmp, text, fnt, max_w) if max_w else [text]
    rendered = []
    for i, ln in enumerate(lines):
        t = artext.render_line(ln, fnt, fill=rgba(fill), pad=4)
        bw, bh = t.width + pad_x * 2, t.height + pad_y * 2
        if torn:
            bar_img = torn_paper(bw, bh, color=bar, jag=max(3, size // 14), seed=seed + i, shadow=False)
        else:
            bar_img = Image.new("RGBA", (bw + 24, bh + 24), (0, 0, 0, 0))
            ImageDraw.Draw(bar_img).rectangle((12, 12, 12 + bw, 12 + bh), fill=rgba(bar))
        bar_img.alpha_composite(t, ((bar_img.width - t.width) // 2, (bar_img.height - t.height) // 2))
        rendered.append(bar_img)
    W = max(r.width for r in rendered)
    gap = int(size * 0.12)
    H = sum(r.height for r in rendered) + gap * (len(rendered) - 1)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = 0
    for r in rendered:
        out.alpha_composite(r, ((W - r.width) // 2, y))  # centered stack
        y += r.height + gap
    out = add_shadow(out, offset=(4, 6), blur=5, opacity=120)
    if rot:
        out = out.rotate(rot, resample=Image.BICUBIC, expand=True)
    return out


def stamp(text, size=64, family="kufi", color="red", rot=-12.0, seed=3, double=True):
    """Rubber stamp: bordered red text with grunge wear, rotated."""
    fnt = artext.font(size, family)
    t = artext.render_line(text, fnt, fill=rgba(color), pad=6)
    pad = int(size * 0.35)
    w, h = t.width + pad * 2, t.height + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bw = max(3, size // 14)
    d.rectangle((0, 0, w - 1, h - 1), outline=rgba(color), width=bw)
    if double:
        d.rectangle((bw * 2, bw * 2, w - 1 - bw * 2, h - 1 - bw * 2), outline=rgba(color), width=max(1, bw // 2))
    img.alpha_composite(t, (pad, pad))
    # grunge wear mask
    rnd = random.Random(seed)
    wear = Image.effect_noise((w, h), 90).point(lambda v: 255 if v > 70 else int(v * 2.2))
    wear = wear.filter(ImageFilter.GaussianBlur(0.6))
    a = ImageChops.multiply(img.split()[3], wear)
    img.putalpha(a)
    if rot:
        img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    return img


def tape(w=220, h=44, color=(255, 240, 200, 170), rot=-6.0, seed=5):
    """Translucent masking-tape strip."""
    img = Image.new("RGBA", (w + 10, h + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(x + 5, y + 5) for x, y in _jagged_rect(w, h, jag=4, seed=seed)]
    d.polygon(pts, fill=color)
    noise = Image.effect_noise((w + 10, h + 10), 40).point(lambda v: 200 + v // 5)
    img.putalpha(ImageChops.multiply(img.split()[3], noise))
    return img.rotate(rot, resample=Image.BICUBIC, expand=True)


def pin(r=16, color=(200, 40, 40, 255)):
    img = Image.new("RGBA", (r * 2 + 12, r * 2 + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((6, 6, 6 + r * 2, 6 + r * 2), fill=color)
    d.ellipse((6 + r * 0.5, 6 + r * 0.4, 6 + r * 1.1, 6 + r * 0.9), fill=(255, 255, 255, 160))
    return add_shadow(img, offset=(2, 3), blur=3)


def censor_bar(w, h):
    return Image.new("RGBA", (w, h), PALETTE["black"])


# ---------- pen marks (progressively drawable) ----------
def pen_circle(w, h, progress=1.0, color="red", width=None, seed=7):
    """Hand-drawn red circle, revealed from 0..progress (for 'draw' animation)."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    width = width or max(4, min(w, h) // 28)
    rnd = random.Random(seed)
    cx, cy, rx, ry = w / 2, h / 2, w / 2 - width * 1.5, h / 2 - width * 1.5
    n = 140
    pts = []
    for i in range(n + 1):
        a = -math.pi / 2 + i / n * math.pi * 2.15   # overlap a bit like a real pen
        wob = 1 + math.sin(i * 0.45 + seed) * 0.012 + rnd.uniform(-0.004, 0.004)
        pts.append((cx + math.cos(a) * rx * wob, cy + math.sin(a) * ry * wob))
    k = max(2, int(len(pts) * max(0.0, min(1.0, progress))))
    d.line(pts[:k], fill=rgba(color), width=width, joint="curve")
    return img


def pen_arrow(x0, y0, x1, y1, progress=1.0, color="red", width=6, head=26, pad=40):
    """Hand-drawn arrow from (x0,y0) to (x1,y1) in a canvas that fits both, returns (img, (ox,oy))."""
    minx, miny = min(x0, x1) - pad, min(y0, y1) - pad
    w, h = int(abs(x1 - x0) + pad * 2), int(abs(y1 - y0) + pad * 2)
    img = Image.new("RGBA", (max(w, 2), max(h, 2)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ax, ay, bx, by = x0 - minx, y0 - miny, x1 - minx, y1 - miny
    # slight curve via a control point
    mx, my = (ax + bx) / 2 + (by - ay) * 0.15, (ay + by) / 2 - (bx - ax) * 0.15
    n = 60
    pts = [((1 - t) ** 2 * ax + 2 * (1 - t) * t * mx + t ** 2 * bx,
            (1 - t) ** 2 * ay + 2 * (1 - t) * t * my + t ** 2 * by) for t in [i / n for i in range(n + 1)]]
    k = max(2, int(len(pts) * max(0.0, min(1.0, progress))))
    d.line(pts[:k], fill=rgba(color), width=width, joint="curve")
    if progress >= 0.97:
        ang = math.atan2(pts[-1][1] - pts[-4][1], pts[-1][0] - pts[-4][0])
        for s in (+1, -1):
            a2 = ang + math.pi + s * 0.5
            d.line([pts[-1], (pts[-1][0] + math.cos(a2) * head, pts[-1][1] + math.sin(a2) * head)],
                   fill=rgba(color), width=width)
    return img, (int(minx), int(miny))


def underline(w, progress=1.0, color="red", width=8):
    img = Image.new("RGBA", (w, width * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = int(w * progress)
    if k > 2:
        d.line([(0, width * 2), (k, width * 2 + 2)], fill=rgba(color), width=width)
    return img


# ---------- full-frame overlays ----------
_grain_cache = {}


def grain_overlay(w, h, strength=22, seed=0):
    """Paper grain + vignette as an RGBA layer to composite over each frame (cached)."""
    key = (w, h, strength, seed)
    if key in _grain_cache:
        return _grain_cache[key]
    noise = Image.effect_noise((w, h), strength + seed * 0.37).filter(ImageFilter.GaussianBlur(0.4))
    # convert to signed-ish overlay: mid grey = transparent
    a = noise.point(lambda v: abs(v - 128) * 2)
    col = noise.point(lambda v: 255 if v > 128 else 0)
    layer = Image.merge("RGBA", (col, col, col, a.point(lambda v: v // 3)))
    # vignette
    vig = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vig).ellipse((-w * 0.25, -h * 0.25, w * 1.25, h * 1.25), fill=255)
    vig = ImageOps.invert(vig.filter(ImageFilter.GaussianBlur(min(w, h) // 5))).point(lambda v: v // 4)
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dark.putalpha(vig)
    layer.alpha_composite(dark)
    _grain_cache[key] = layer
    return layer


def paper_background(w, h, color="paper", seed=0):
    """Procedural aged-newsprint background (fallback / placeholder plate)."""
    base = Image.new("RGB", (w, h), rgba(color)[:3])
    fib = Image.effect_noise((w, h), 30).filter(ImageFilter.GaussianBlur(1.2))
    fib = Image.merge("RGB", (fib, fib, fib))
    base = Image.blend(base, ImageChops.multiply(base, fib), 0.35)
    rnd = random.Random(seed)
    d = ImageDraw.Draw(base)
    for _ in range(18):   # faint coffee/age blotches
        x, y, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(40, 220)
        blot = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
        ImageDraw.Draw(blot).ellipse((0, 0, r * 2 - 1, r * 2 - 1), fill=(150, 120, 70, 22))
        blot = blot.filter(ImageFilter.GaussianBlur(r // 3))
        base.paste(blot, (x - r, y - r), blot)
    # faint fake newspaper columns
    col_w = w // 6
    for cx in range(col_w // 2, w, col_w):
        for ly in range(int(h * 0.05), h, 14):
            if rnd.random() < 0.85:
                ln = rnd.randint(int(col_w * 0.4), int(col_w * 0.8))
                d.line([(cx, ly), (cx + ln, ly)], fill=(120, 110, 90, 255), width=2)
    base = Image.blend(base, Image.new("RGB", (w, h), rgba(color)[:3]), 0.7)
    return base.convert("RGBA")


if __name__ == "__main__":
    W, H = 1080, 1080
    bg = paper_background(W, H)
    bg.alpha_composite(highlight_text("خبر عاجل", 110, bar="red", fill="white"), (80, 80))
    bg.alpha_composite(highlight_text("الطريقة السرية لصناعة الفيديو", 80, bar="yellow", max_w=800), (100, 300))
    bg.alpha_composite(stamp("سري للغاية", 70), (620, 120))
    bg.alpha_composite(pen_circle(300, 300, 0.8), (700, 600))
    arr, off = pen_arrow(200, 900, 600, 700)
    bg.alpha_composite(arr, off)
    bg.alpha_composite(tape(), (420, 40))
    bg.alpha_composite(grain_overlay(W, H))
    bg.save("/tmp/paperfx_test.png")
    print("saved /tmp/paperfx_test.png")
