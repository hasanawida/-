#!/usr/bin/env python3
"""
artext.py — Arabic text rendering for vox-ar (RTL shaping, fonts, wrapping).

Uses Pillow's libraqm layout when available (correct Arabic shaping + RTL),
and falls back to arabic-reshaper + python-bidi on systems without raqm
(common on Windows wheels). Every other module renders Arabic through here.
"""
import os
import re

from PIL import Image, ImageDraw, ImageFont, features

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")

# Family -> (file, variation-name for bold weight or None)
FONTS = {
    "cairo":   ("Cairo.ttf", b"Black"),
    "kufi":    ("NotoKufiArabic.ttf", b"Black"),
    "tajawal": ("Tajawal-ExtraBold.ttf", None),
    "changa":  ("Changa.ttf", b"ExtraBold"),
}
DEFAULT_FAMILY = "cairo"

HAS_RAQM = features.check("raqm")
_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")

_font_cache = {}


def is_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text or ""))


def font(size: int, family: str | None = None, weight: bytes | None = "auto") -> ImageFont.FreeTypeFont:
    """Load an Arabic display font at `size`. Variable fonts get their heaviest weight."""
    family = family if family in FONTS else DEFAULT_FAMILY
    key = (family, size, weight)
    if key in _font_cache:
        return _font_cache[key]
    fname, var = FONTS[family]
    path = os.path.join(FONT_DIR, fname)
    if not os.path.exists(path):
        f = ImageFont.load_default(size=size)
    else:
        f = ImageFont.truetype(path, size)
        v = var if weight == "auto" else weight
        if v:
            try:
                f.set_variation_by_name(v)
            except Exception:
                try:
                    names = f.get_variation_names()
                    if names:
                        f.set_variation_by_name(names[-1])
                except Exception:
                    pass
    _font_cache[key] = f
    return f


def shape(text: str) -> str:
    """Return display-ready string for renderers WITHOUT raqm (reshape + bidi)."""
    if HAS_RAQM or not is_arabic(text):
        return text
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text))


def _kw(text: str) -> dict:
    """Extra kwargs for ImageDraw.text / textlength."""
    if HAS_RAQM and is_arabic(text):
        return {"direction": "rtl", "language": "ar", "features": ["kern", "liga"]}
    return {}


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt) -> float:
    return draw.textlength(shape(text), font=fnt, **_kw(text))


def text_bbox(draw: ImageDraw.ImageDraw, text: str, fnt):
    return draw.textbbox((0, 0), shape(text), font=fnt, **_kw(text))


def draw_text(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill, anchor="la", stroke_width=0, stroke_fill=None):
    draw.text(xy, shape(text), font=fnt, fill=fill, anchor=anchor,
              stroke_width=stroke_width, stroke_fill=stroke_fill, **_kw(text))


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int) -> list[str]:
    """Greedy word wrap that measures shaped Arabic correctly."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if text_width(draw, trial, fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_line(text: str, fnt, fill=(20, 20, 20, 255), pad=8, stroke=0, stroke_fill=(0, 0, 0, 255)) -> Image.Image:
    """Render one line of text into a tight RGBA image."""
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    l, t, r, b = text_bbox(d, text, fnt)
    w, h = int(r - l) + pad * 2 + stroke * 2, int(b - t) + pad * 2 + stroke * 2
    img = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_text(d, (pad + stroke - l, pad + stroke - t), text, fnt, fill,
              stroke_width=stroke, stroke_fill=stroke_fill)
    return img


if __name__ == "__main__":
    print("raqm:", HAS_RAQM)
    im = Image.new("RGB", (900, 300), "white")
    d = ImageDraw.Draw(im)
    f = font(72)
    draw_text(d, (450, 150), "الطريقة السرية لصناعة فيديوهات VOX", f, "black", anchor="mm")
    im.save("/tmp/artext_test.png")
    print("saved /tmp/artext_test.png")
