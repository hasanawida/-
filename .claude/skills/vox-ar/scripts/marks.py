#!/usr/bin/env python3
"""
marks.py — modern explainer marks drawn in code (all RGBA, all animatable):

  callout   label on a bar + hand-drawn leader line to a point (progressive)
  counter   number that counts up (0 → value) on a bar, with prefix/suffix
  bubble    speech bubble with text and a tail
  sticky    sticky note with a short handwritten-style text + pin
  check     green ✓ / cross  red ✗, drawn progressively
  bars      animated bar chart (labels + values), bars grow in sequence
  timeline  horizontal line with pinned year labels appearing one by one
  vs        two labels with a "VS" badge
  badge     round badge with short text
  bigquote  giant quotation marks behind a quote

Each function takes progress 0..1 where it makes sense.
"""
import math

from PIL import Image, ImageDraw, ImageFilter

import artext
import paperfx
from paperfx import rgba


def _text_bar(text, size, bar="yellow", fill=None, family="cairo", max_w=None, rot=0):
    fill = fill or ("white" if bar in ("red", "black", "blue") else "black")
    return paperfx.highlight_text(text, size=size, family=family, fill=fill, bar=bar, rot=rot, torn=True, max_w=max_w)


# ---------------------------------------------------------------- callout
def callout(text, size, x, y, tx, ty, progress=1.0, bar="white", color="red", width=5):
    """Return (img, (ox, oy)): label centered at (x,y) with a leader line to (tx,ty). Canvas coords."""
    label = _text_bar(text, size, bar=bar)
    pad = 40
    minx, miny = min(x - label.width / 2, tx) - pad, min(y - label.height / 2, ty) - pad
    maxx, maxy = max(x + label.width / 2, tx) + pad, max(y + label.height / 2, ty) + pad
    img = Image.new("RGBA", (int(maxx - minx), int(maxy - miny)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lx, ly = x - minx, y - miny
    px, py = tx - minx, ty - miny
    # leader: from label edge toward target, drawn progressively, with an elbow
    ex = lx + (label.width / 2 + 6) * (1 if px > lx else -1)
    pts = [(ex, ly), (ex + (px - ex) * 0.45, ly), (px, py)]
    n = 40
    path = []
    for i in range(n + 1):
        u = i / n
        if u < 0.5:
            a, b, uu = pts[0], pts[1], u * 2
        else:
            a, b, uu = pts[1], pts[2], (u - 0.5) * 2
        path.append((a[0] + (b[0] - a[0]) * uu, a[1] + (b[1] - a[1]) * uu))
    k = max(2, int(len(path) * min(1, progress * 1.4)))
    d.line(path[:k], fill=rgba(color), width=width, joint="curve")
    if progress > 0.75:
        r = width * 1.6
        d.ellipse((px - r, py - r, px + r, py + r), fill=rgba(color))
        d.ellipse((px - r * 2.2, py - r * 2.2, px + r * 2.2, py + r * 2.2), outline=rgba(color), width=max(2, width // 2))
    lab_alpha = min(1.0, progress * 3)
    if lab_alpha < 1:
        a = label.split()[3].point(lambda v: int(v * lab_alpha)); label = label.copy(); label.putalpha(a)
    img.alpha_composite(label, (int(lx - label.width / 2), int(ly - label.height / 2)))
    return img, (int(minx), int(miny))


# ---------------------------------------------------------------- counter
def counter(value, progress, size, prefix="", suffix="", bar="red", decimals=0):
    v = value * (1 - (1 - min(1, progress)) ** 3)
    txt = f"{prefix}{v:,.{decimals}f}{suffix}" if decimals else f"{prefix}{int(round(v)):,}{suffix}"
    return _text_bar(txt, size, bar=bar)


# ---------------------------------------------------------------- bubble
def bubble(text, size, max_w, tail="bl", fill=(250, 247, 240, 255), ink="black", family="cairo"):
    fnt = artext.font(size, family)
    tmp = ImageDraw.Draw(Image.new("RGBA", (2, 2)))
    lines = artext.wrap(tmp, text, fnt, max_w)
    ims = [artext.render_line(ln, fnt, fill=rgba(ink), pad=2) for ln in lines]
    tw, th = max(i.width for i in ims), sum(i.height for i in ims)
    pad = int(size * 0.55)
    w, h = tw + pad * 2, th + pad * 2
    tail_h = int(size * 0.8)
    img = Image.new("RGBA", (w + 20, h + tail_h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((10, 10, 10 + w, 10 + h), radius=int(size * 0.6), fill=fill, outline=rgba("ink"), width=3)
    tx = 10 + (w * 0.25 if tail == "bl" else w * 0.75)
    d.polygon([(tx - size * 0.4, 10 + h - 2), (tx + size * 0.4, 10 + h - 2), (tx - size * 0.1, 10 + h + tail_h)],
              fill=fill, outline=rgba("ink"))
    d.line([(tx - size * 0.4, 10 + h - 2), (tx + size * 0.4, 10 + h - 2)], fill=fill, width=4)
    y = 10 + pad
    for i in ims:
        img.alpha_composite(i, (10 + (w - i.width) // 2, y)); y += i.height
    return paperfx.add_shadow(img, offset=(4, 6), blur=5, opacity=110)


# ---------------------------------------------------------------- sticky
def sticky(text, size, color=(255, 236, 120, 255), rot=-4, family="changa"):
    fnt = artext.font(size, family)
    tmp = ImageDraw.Draw(Image.new("RGBA", (2, 2)))
    side = int(size * 6.2)
    lines = artext.wrap(tmp, text, fnt, side - size)
    img = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, side - 1, side - 1), fill=color)
    # slightly darker strip at top (glue) + curled corner
    d.rectangle((0, 0, side - 1, int(side * 0.12)), fill=tuple(max(0, c - 18) for c in color[:3]) + (255,))
    d.polygon([(side - int(side * 0.16), side - 1), (side - 1, side - 1), (side - 1, side - int(side * 0.16))],
              fill=tuple(max(0, c - 40) for c in color[:3]) + (255,))
    y = int(side * 0.22)
    for ln in lines[:4]:
        artext.draw_text(d, (side // 2, y), ln, fnt, rgba("ink"), anchor="ma")
        y += int(size * 1.35)
    img = paperfx.add_shadow(img, offset=(6, 8), blur=7, opacity=120)
    if rot:
        img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    return img


# ---------------------------------------------------------------- check / cross
def check(size, progress=1.0, color=(34, 150, 80, 255), width=None):
    width = width or max(6, size // 9)
    img = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(size * 0.12, size * 0.55), (size * 0.4, size * 0.85), (size * 0.92, size * 0.18)]
    pts = [(x + 10, y + 10) for x, y in pts]
    seg = [pts[0], pts[1], pts[2]]
    path = []
    for i in range(2):
        a, b = seg[i], seg[i + 1]
        for j in range(21):
            u = j / 20
            path.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    k = max(2, int(len(path) * min(1, progress)))
    d.line(path[:k], fill=color, width=width, joint="curve")
    return img


def cross(size, progress=1.0, color="red", width=None):
    width = width or max(6, size // 9)
    img = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    p1 = [(10 + size * 0.15, 10 + size * 0.15), (10 + size * 0.85, 10 + size * 0.85)]
    p2 = [(10 + size * 0.85, 10 + size * 0.15), (10 + size * 0.15, 10 + size * 0.85)]
    q = min(1, progress * 2)
    d.line([p1[0], (p1[0][0] + (p1[1][0] - p1[0][0]) * q, p1[0][1] + (p1[1][1] - p1[0][1]) * q)], fill=rgba(color), width=width)
    if progress > 0.5:
        q = min(1, (progress - 0.5) * 2)
        d.line([p2[0], (p2[0][0] + (p2[1][0] - p2[0][0]) * q, p2[0][1] + (p2[1][1] - p2[0][1]) * q)], fill=rgba(color), width=width)
    return img


# ---------------------------------------------------------------- bars
def bars(items, w, h, progress=1.0, size=None, colors=("red", "yellow", "ink", "blue"), family="cairo", ink="ink", label_w=0.26):
    """items = [(label, value), ...]. Horizontal bars growing right→left (RTL) in sequence."""
    size = size or max(18, h // (len(items) * 3))
    fnt = artext.font(size, family)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    vmax = max(v for _, v in items) or 1
    row = h / len(items)
    label_w = int(w * label_w)
    value_w = int(size * 3.2)
    for i, (label, v) in enumerate(items):
        p = min(1, max(0, progress * len(items) - i * 0.8))
        p = 1 - (1 - p) ** 3
        y0 = int(i * row + row * 0.15); y1 = int(i * row + row * 0.85)
        bar_w = int((w - label_w - value_w) * (v / vmax) * p)
        col = rgba(colors[i % len(colors)])
        # RTL: label at right, bar grows leftwards
        artext.draw_text(d, (w - 4, (y0 + y1) // 2), label, fnt, rgba(ink), anchor="rm")
        x1 = w - label_w
        d.rectangle((x1 - bar_w, y0, x1, y1), fill=col)
        if p > 0.95:
            vt = f"{v:g}"
            artext.draw_text(d, (x1 - bar_w - 8, (y0 + y1) // 2), vt, fnt, rgba(ink), anchor="rm")
    return paperfx.add_shadow(img, offset=(3, 4), blur=4, opacity=90)


# ---------------------------------------------------------------- timeline
def timeline(labels, w, progress=1.0, size=28, color="red", family="cairo", ink="ink"):
    """Horizontal line with pins; labels appear right→left as progress grows."""
    fnt = artext.font(size, family)
    h = int(size * 3.4)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = int(h * 0.62)
    n = len(labels)
    k = min(1, progress)
    d.line([(w - 10, y), (w - 10 - (w - 20) * k, y)], fill=rgba(ink), width=max(3, size // 8))
    for i, lab in enumerate(labels):
        u = (i + 0.5) / n
        if u > k + 0.02:
            continue
        x = w - 10 - (w - 20) * u
        r = size * 0.32
        d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(color))
        bar = _text_bar(lab, size, bar="white")
        img.alpha_composite(bar, (int(x - bar.width / 2), int(y - r - bar.height - 4)))
    return img


# ---------------------------------------------------------------- vs / badge / bigquote
def vs_badge(size):
    fnt = artext.font(int(size * 0.55), "changa")
    img = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 10 + size, 10 + size), fill=rgba("black"))
    d.ellipse((16, 16, 4 + size, 4 + size), outline=rgba("yellow"), width=max(3, size // 24))
    artext.draw_text(d, (10 + size / 2, 10 + size / 2), "VS", fnt, rgba("yellow"), anchor="mm")
    return paperfx.add_shadow(img)


def badge(text, size, color="red", fill="white", family="cairo"):
    fs = int(size * 0.42)
    tmp = ImageDraw.Draw(Image.new("RGBA", (2, 2)))
    while fs > 10 and artext.text_width(tmp, text, artext.font(fs, family)) > size * 0.78:
        fs -= 2
    fnt = artext.font(fs, family)
    img = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 10 + size, 10 + size), fill=rgba(color))
    d.ellipse((18, 18, 2 + size, 2 + size), outline=rgba(fill), width=max(2, size // 40))
    artext.draw_text(d, (10 + size / 2, 10 + size / 2), text, fnt, rgba(fill), anchor="mm")
    return paperfx.add_shadow(img)


def bigquote(size, color=(196, 30, 32, 160)):
    fnt = artext.font(size, "changa")
    return artext.render_line("”", fnt, fill=color, pad=4)
