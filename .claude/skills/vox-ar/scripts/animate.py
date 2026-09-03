#!/usr/bin/env python3
"""
animate.py — the "montage" stage, in code. Renders every shot to an .mp4:

  plate (still image, or a Veo clip when "motion": "veo")
    + layers (cutouts, headlines on highlight bars, stamps, pen circles/arrows, tape, pins, images)
      each with an entrance animation (pop / slam / slide / fade / stamp / draw), an idle motion
      (bob / sway), an optional exit
    + 2.5D camera: monocular depth (MiDaS, offline) splits the plate into far/mid/near bands, and every
      layer has a depth, so a push-in or pan moves every part of the picture at its own rate (parallax)
    + living effects (dust motes, light sweep), paper grain + vignette
    + burned-in captions synced to the narration (uses word timings when the TTS gives them)

Frames are streamed to ffmpeg; nothing is written to disk but the final clip.
Beat duration follows the narration: if the audio is longer than the shots, shots stretch.

usage: python3 scripts/animate.py out/<project> [--only 1a] [--preview]  (--preview = 12 fps, half size)
"""
import argparse
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageChops

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artext    # noqa: E402
import marks     # noqa: E402
import paperfx   # noqa: E402
import presets  # noqa: E402
import styles    # noqa: E402

SUPER = 1.06      # compose canvas oversize → camera moves always downsample (stay sharp)


# ------------------------------------------------------------------ easing
def ease_out_back(t, s=1.6):
    t = max(0.0, min(1.0, t)); t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def clamp01(x):
    return max(0.0, min(1.0, x))


# ------------------------------------------------------------------ layer prep
class Layer:
    """A prepared (pre-rendered) layer + its animation params. Coordinates are frame-relative."""

    def __init__(self, spec, W, H, project_dir, fps):
        self.spec = spec
        self.type = spec.get("type", "cutout")
        self.x, self.y = spec.get("x", 0.5), spec.get("y", 0.5)
        self.rot = spec.get("rot", 0.0)
        self.at = float(spec.get("at", 0.0))
        self.anim = spec.get("in", {"cutout": "pop", "headline": "slam", "stamp": "stamp",
                                     "circle": "draw", "arrow": "draw", "underline": "draw",
                                     "tape": "fade", "pin": "pop", "image": "pop",
                                     "callout": "draw", "counter": "draw", "check": "draw", "cross": "draw",
                                     "bars": "draw", "timeline": "draw", "bubble": "pop", "sticky": "pop",
                                     "vs": "pop", "badge": "pop", "bigquote": "fade"}.get(self.type, "pop"))
        self.in_dur = float(spec.get("in_dur", {"draw": 0.55, "stamp": 0.18, "slam": 0.28, "fade": 0.35}.get(self.anim, 0.42)))
        if self.type in ("counter", "bars", "timeline"):
            self.in_dur = float(spec.get("in_dur", 1.6))
        self.until = spec.get("until")           # exit time (s) or None
        self.out = spec.get("out", "fade")
        self.idle = spec.get("idle", "bob" if self.type in ("cutout", "image", "pin") else
                             ("sway" if self.type == "headline" else "none"))
        self.idle_amp = float(spec.get("idle_amp", 1.0))
        self.opacity = float(spec.get("opacity", 1.0))
        self.depth = float(spec.get("z", {"cutout": 0.72, "image": 0.72, "pin": 0.8, "tape": 0.78,
                                             "headline": 0.9, "stamp": 0.9, "censor": 0.75, "bigquote": 0.6,
                                             "sticky": 0.8, "bubble": 0.85}.get(self.type, 0.85)))
        self.W, self.H = W, H
        self.img = None       # static render (RGBA) for non-progressive layers
        self.progressive = self.type in ("circle", "arrow", "underline", "callout", "counter", "check", "cross", "bars", "timeline")
        self.offset = (0, 0)  # for arrow (canvas offset)
        self._build(project_dir)

    def _px_w(self, key="w", default=0.4):
        return int(self.W * float(self.spec.get(key, default)))

    def _build(self, project_dir):
        s, W, H = self.spec, self.W, self.H
        t = self.type
        if t in ("cutout", "image"):
            p = s.get("path") or s.get("image")
            p = p if os.path.isabs(p) else os.path.join(project_dir, p)
            img = Image.open(p).convert("RGBA")
            tw = self._px_w("w", 0.45)
            img = img.resize((tw, max(1, int(img.height * tw / img.width))), Image.LANCZOS)
            self.img = paperfx.cutout(img, border=int(W * 0.006) if s.get("border", True) else 0,
                                      shadow=s.get("shadow", True), halftone=s.get("halftone", False),
                                      bw="bw" in (s.get("effects") or []) and t == "image")
        elif t == "headline":
            size = int(H * float(s.get("size", 0.055)))
            self.img = paperfx.highlight_text(s["text"], size=size, family=s.get("font", "cairo"),
                                              fill=s.get("fill", "black" if s.get("bar", "yellow") != "red" else "white"),
                                              bar=s.get("bar", "yellow"), rot=0,
                                              torn=s.get("torn", True), max_w=int(W * float(s.get("max_w", 0.88))),
                                              seed=hash(s["text"]) & 0xff)
        elif t == "stamp":
            size = int(H * float(s.get("size", 0.045)))
            self.img = paperfx.stamp(s["text"], size=size, family=s.get("font", "kufi"),
                                     color=s.get("color", "red"), rot=0)
        elif t == "tape":
            self.img = paperfx.tape(w=self._px_w("w", 0.22), h=int(H * float(s.get("h", 0.022))), rot=0)
        elif t == "pin":
            self.img = paperfx.pin(r=int(H * float(s.get("size", 0.009))))
        elif t == "censor":
            self.img = paperfx.censor_bar(self._px_w("w", 0.2), int(H * float(s.get("h", 0.03))))
        elif t == "circle":
            self.cw, self.ch = self._px_w("w", 0.3), int(H * float(s.get("h", s.get("w", 0.3) * W / H)))
        elif t == "arrow":
            self.pts = (int(s["x0"] * W), int(s["y0"] * H), int(s["x1"] * W), int(s["y1"] * H))
        elif t == "underline":
            self.cw = self._px_w("w", 0.3)
        elif t == "callout":
            self.size = int(H * float(s.get("size", 0.036)))
            self.target = (int(s.get("tx", 0.5) * W), int(s.get("ty", 0.5) * H))
        elif t == "counter":
            self.size = int(H * float(s.get("size", 0.08)))
        elif t in ("check", "cross"):
            self.size = int(H * float(s.get("size", 0.12)))
        elif t == "bars":
            self.cw, self.ch = self._px_w("w", 0.5), int(H * float(s.get("h", 0.35)))
        elif t == "timeline":
            self.cw = self._px_w("w", 0.8)
            self.size = int(H * float(s.get("size", 0.03)))
        elif t == "bubble":
            self.img = marks.bubble(s["text"], int(H * float(s.get("size", 0.04))), int(W * float(s.get("max_w", 0.34))),
                                    tail=s.get("tail", "bl"))
        elif t == "sticky":
            self.img = marks.sticky(s["text"], int(H * float(s.get("size", 0.045))), rot=0)
        elif t == "vs":
            self.img = marks.vs_badge(int(H * float(s.get("size", 0.16))))
        elif t == "badge":
            self.img = marks.badge(s["text"], int(H * float(s.get("size", 0.16))), color=s.get("color", "red"))
        elif t == "bigquote":
            self.img = marks.bigquote(int(H * float(s.get("size", 0.3))))
        else:
            raise ValueError(f"unknown layer type {t}")

    # ---- per-frame
    def render(self, t, cam_s=1.0):
        """Return (img, (cx, cy)) for time t — img already scaled by the camera factor cam_s,
        (cx, cy) in canvas coordinates. None if not visible."""
        if t < self.at:
            return None
        if self.until is not None and t > self.until + 0.4:
            return None
        p = clamp01((t - self.at) / self.in_dur) if self.in_dur > 0 else 1.0
        scale, alpha, dx, dy, drot = 1.0, 1.0, 0.0, 0.0, 0.0
        a = self.anim
        if a == "pop":
            scale = ease_out_back(p)
        elif a == "slam":
            scale = 1.0 + (1 - ease_out_cubic(p)) * 0.9
            alpha = min(1.0, p * 3)
            if p < 1:
                dx, dy = math.sin(p * 40) * 6 * (1 - p), math.cos(p * 37) * 6 * (1 - p)
        elif a == "stamp":
            scale = 1.0 + (1 - ease_out_cubic(p)) * 0.6
            alpha = min(1.0, p * 2.5)
        elif a == "fade":
            alpha = ease_out_cubic(p)
        elif a.startswith("slide"):
            e = 1 - ease_out_cubic(p)
            d = {"slide_l": (-1, 0), "slide_r": (1, 0), "slide_up": (0, 1), "slide_down": (0, -1)}.get(a, (-1, 0))
            dx, dy = d[0] * e * self.W * 0.6, d[1] * e * self.H * 0.4
        elif a == "draw":
            pass
        # idle motion
        if p >= 1 and self.idle != "none":
            k = self.idle_amp
            ph = (self.x * 7 + self.y * 13)
            if self.idle == "bob":
                dy += math.sin(t * 1.6 + ph) * self.H * 0.004 * k
                drot += math.sin(t * 1.1 + ph) * 0.8 * k
            elif self.idle == "sway":
                drot += math.sin(t * 1.3 + ph) * 0.6 * k
                dx += math.sin(t * 0.9 + ph) * self.W * 0.002 * k
            elif self.idle == "float":
                dx += math.sin(t * 0.7 + ph) * self.W * 0.006 * k
                dy += math.cos(t * 0.9 + ph) * self.H * 0.005 * k
        # exit
        if self.until is not None and t > self.until:
            q = clamp01((t - self.until) / 0.4)
            if self.out == "fade":
                alpha *= 1 - q
            elif self.out == "shrink":
                scale *= 1 - ease_in_out(q); alpha *= 1 - q
            elif self.out.startswith("slide"):
                d = {"slide_l": (-1, 0), "slide_r": (1, 0), "slide_up": (0, -1), "slide_down": (0, 1)}.get(self.out, (1, 0))
                dx += d[0] * ease_in_out(q) * self.W; dy += d[1] * ease_in_out(q) * self.H
        alpha *= self.opacity

        # progressive pen layers
        if self.progressive:
            prog = ease_in_out(p) if self.anim == "draw" else 1.0
            if self.type == "circle":
                img = paperfx.pen_circle(self.cw, self.ch, prog, color=self.spec.get("color", "red"))
                cx, cy = self.x * self.W, self.y * self.H
            elif self.type == "arrow":
                img, (ox, oy) = paperfx.pen_arrow(*self.pts, progress=prog, color=self.spec.get("color", "red"),
                                                  width=max(4, int(self.W * 0.006)), head=int(self.W * 0.025))
                cx, cy = ox + img.width / 2, oy + img.height / 2
            elif self.type == "underline":
                img = paperfx.underline(self.cw, prog, color=self.spec.get("color", "red"), width=max(4, int(self.H * 0.005)))
                cx, cy = self.x * self.W, self.y * self.H
            elif self.type == "callout":
                img, (ox, oy) = marks.callout(self.spec["text"], self.size, self.x * self.W, self.y * self.H,
                                              self.target[0], self.target[1], prog, bar=self.spec.get("bar", "white"),
                                              color=self.spec.get("color", "red"), width=max(3, int(self.W * 0.0025)))
                cx, cy = ox + img.width / 2, oy + img.height / 2
            elif self.type == "counter":
                img = marks.counter(float(self.spec.get("value", 100)), prog, self.size, prefix=self.spec.get("prefix", ""),
                                    suffix=self.spec.get("suffix", ""), bar=self.spec.get("bar", "red"),
                                    decimals=int(self.spec.get("decimals", 0)))
                cx, cy = self.x * self.W, self.y * self.H
            elif self.type == "check":
                img = marks.check(self.size, prog); cx, cy = self.x * self.W, self.y * self.H
            elif self.type == "cross":
                img = marks.cross(self.size, prog); cx, cy = self.x * self.W, self.y * self.H
            elif self.type == "bars":
                img = marks.bars([(i[0], float(i[1])) for i in self.spec["items"]], self.cw, self.ch, prog,
                                 size=int(self.H * float(self.spec.get("size", 0.032))), ink=self.spec.get("ink", "ink"),
                                 label_w=float(self.spec.get("label_w", 0.26)))
                cx, cy = self.x * self.W, self.y * self.H
            else:  # timeline
                img = marks.timeline(list(self.spec["items"]), self.cw, prog, size=self.size, ink=self.spec.get("ink", "ink"))
                cx, cy = self.x * self.W, self.y * self.H
            return self._finish(img, cx + dx, cy + dy, cam_s, alpha, self.rot + drot)

        return self._finish(self.img, self.x * self.W + dx, self.y * self.H + dy, scale * cam_s, alpha, self.rot + drot)

    def _finish(self, img, cx, cy, scale, alpha, rot):
        if scale <= 0.01 or alpha <= 0.01:
            return None
        # quantize so idle motion re-uses cached transforms (rotation is the #1 render cost)
        qs = round(scale, 3)
        qr = round(rot * 4) / 4.0
        key = (id(img), qs, qr)
        cache = self.__dict__.setdefault("_xcache", {})
        out = cache.get(key)
        if out is None:
            out = img
            if abs(qs - 1.0) > 0.005:
                out = out.resize((max(1, int(out.width * qs)), max(1, int(out.height * qs))), Image.BILINEAR)
            if abs(qr) > 0.05:
                out = out.rotate(qr, resample=Image.BILINEAR if abs(qr) < 3 else Image.BICUBIC, expand=True)
            if len(cache) > 160:
                cache.clear()
            cache[key] = out
        if alpha < 0.995:
            a = out.split()[3].point(lambda v: int(v * alpha))
            out = out.copy(); out.putalpha(a)
        return out, (cx, cy)


# ------------------------------------------------------------------ captions
def phrase_captions(narration, words, total, max_words=5):
    """Split narration into caption phrases with (start, end, text).
    `words` = [(s,e,word)] from TTS if available, else evenly spaced."""
    toks = narration.split()
    if not toks:
        return []
    if not words or len(words) < len(toks) * 0.6:
        step = total / len(toks)
        words = [(i * step, (i + 1) * step, w) for i, w in enumerate(toks)]
    # group into phrases: break on punctuation or max_words
    phrases, cur = [], []
    for (s, e, w) in words:
        cur.append((s, e, w))
        if len(cur) >= max_words or w.rstrip()[-1:] in "،,.؟?!:؛":
            phrases.append(cur); cur = []
    if cur:
        phrases.append(cur)
    out = []
    for i, ph in enumerate(phrases):
        s = ph[0][0]
        e = phrases[i + 1][0][0] if i + 1 < len(phrases) else max(ph[-1][1], total)
        out.append((s, e, " ".join(w for _, _, w in ph)))
    return out


class CaptionTrack:
    def __init__(self, phrases, W, H, cfg):
        self.items = []
        size = int(H * float(cfg.get("size", 0.036)))
        style = cfg.get("style", "highlight")
        for s, e, text in phrases:
            if style == "highlight":
                img = paperfx.highlight_text(text, size=size, family=cfg.get("font", "cairo"),
                                             fill=cfg.get("fill", "black"), bar=cfg.get("bar", "white"),
                                             rot=0, torn=True, max_w=int(W * 0.86), seed=len(text))
            else:  # plain white with black stroke
                fnt = artext.font(size, cfg.get("font", "cairo"))
                lines = artext.wrap(ImageDraw.Draw(Image.new("RGBA", (2, 2))), text, fnt, int(W * 0.86))
                ims = [artext.render_line(ln, fnt, fill=(255, 255, 255, 255), stroke=max(2, size // 12)) for ln in lines]
                w = max(i.width for i in ims); h = sum(i.height for i in ims)
                img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
                for i in ims:
                    img.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height
            self.items.append((s, e, img))
        self.y = float(cfg.get("position", 0.80)) * H
        self.W = W

    def render(self, t):
        for s, e, img in self.items:
            if s <= t < e:
                p = clamp01((t - s) / 0.15)
                sc = 0.9 + 0.1 * ease_out_cubic(p)
                if sc < 0.999:
                    img = img.resize((int(img.width * sc), int(img.height * sc)), Image.BILINEAR)
                return img, (self.W / 2, self.y)
        return None


# ------------------------------------------------------------------ plate sources
def _cover(img, W, H):
    s = max(W / img.width, H / img.height)
    img = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    l, t = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((l, t, l + W, t + H))


class Camera:
    """Camera on the compose canvas + depth-aware mapping (2.5D parallax).

    map(t, d) → (s, ox, oy): a canvas point p at depth d (0 far … 1 near) lands at p*s + (ox, oy)
    in the output frame. Near things zoom/pan more than far things → parallax."""

    def __init__(self, move, dur, CW, CH, W, H, strength=1.0, parallax=1.0):
        self.move, self.dur, self.CW, self.CH, self.W, self.H = move, max(dur, 0.01), CW, CH, W, H
        self.zmax = 1.0 + 0.10 * strength
        self.par = parallax

    def state(self, t):
        p = ease_in_out(t / self.dur)
        m = self.move
        z = {"push_in": 1.0 + (self.zmax - 1) * p, "pull_out": self.zmax - (self.zmax - 1) * p,
             "static": 1.0 + 0.012 * p, "pan_l": 1.035, "pan_r": 1.035, "pan_up": 1.035, "pan_down": 1.035,
             "drift": 1.02}.get(m, 1.0)
        cx, cy = self.CW / 2, self.CH / 2
        bw, bh = self.CW / z, self.CH / z
        sx, sy = (self.CW - bw) / 2, (self.CH - bh) / 2
        if m == "pan_l":
            cx -= sx * (2 * p - 1)
        elif m == "pan_r":
            cx += sx * (2 * p - 1)
        elif m == "pan_up":
            cy -= sy * (2 * p - 1)
        elif m == "pan_down":
            cy += sy * (2 * p - 1)
        elif m == "drift":
            cx += sx * 0.6 * math.sin(t * 0.5); cy += sy * 0.6 * math.cos(t * 0.37)
        return z, cx, cy

    def map(self, t, d=0.5):
        z, cx, cy = self.state(t)
        k = 1.0 + self.par * (d - 0.5) * 1.0
        z_d = 1.0 + (z - 1.0) * k
        c0x, c0y = self.CW / 2, self.CH / 2
        cdx, cdy = c0x + (cx - c0x) * k, c0y + (cy - c0y) * k
        s = self.W * z_d / self.CW
        return s, self.W / 2 - cdx * s, self.H / 2 - cdy * s


def blit(frame, img, s, ox, oy, bx=0, by=0):
    """Composite `img` (canvas-space, origin bx,by) onto `frame` under mapping (s, ox, oy)."""
    W, H = frame.size
    x0, y0 = bx * s + ox, by * s + oy
    x1, y1 = x0 + img.width * s, y0 + img.height * s
    vx0, vy0, vx1, vy1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if vx1 - vx0 < 1 or vy1 - vy0 < 1:
        return
    # source crop in img pixels
    sx0, sy0 = (vx0 - x0) / s, (vy0 - y0) / s
    sx1, sy1 = (vx1 - x0) / s, (vy1 - y0) / s
    src = img.crop((int(sx0), int(sy0), int(math.ceil(sx1)), int(math.ceil(sy1))))
    tw, th = int(round(vx1 - vx0)), int(round(vy1 - vy0))
    if tw < 1 or th < 1:
        return
    if src.size != (tw, th):
        src = src.resize((tw, th), Image.BILINEAR)
    frame.alpha_composite(src, (int(vx0), int(vy0)))


class ParallaxPlate:
    """Still plate split by depth into base (far) + up to 2 floating bands (mid, near)."""

    def __init__(self, path, CW, CH, grain=22, parallax=1.0, flat=False):
        img = _cover(Image.open(path).convert("RGB"), CW, CH).convert("RGBA")
        if grain > 0:
            img.alpha_composite(paperfx.grain_overlay(CW, CH, strength=grain))
        self.base, self.bands, self.base_d = img, [], 0.35
        if parallax <= 0 or flat:
            return
        import depth as depthmod
        dm = depthmod.depth(img)
        if dm is None:
            return
        bl = depthmod.bands(dm, n=2, feather=10, split=0.62)
        self.base_d = bl[0][1]
        union = Image.new("L", (CW, CH), 0)
        for mask, d in bl[1:]:
            bbox = mask.point(lambda v: 255 if v > 12 else 0).getbbox()
            if not bbox:
                continue
            layer = img.crop(bbox)
            layer.putalpha(ImageChops.multiply(layer.split()[3], mask.crop(bbox)))
            self.bands.append((layer, bbox[0], bbox[1], d))
            union = ImageChops.lighter(union, mask)
        if self.bands:   # soft "inpaint" under the floating bands so parallax never shows a hard hole
            blurred = img.filter(ImageFilter.GaussianBlur(28))
            self.base = Image.composite(blurred, img, union.filter(ImageFilter.MaxFilter(9)))

    def draw(self, frame, cam, t):
        s, ox, oy = cam.map(t, self.base_d)
        box = (-ox / s, -oy / s, (frame.width - ox) / s, (frame.height - oy) / s)
        b = tuple(int(round(v)) for v in box)
        base = self.base.crop(b).resize(frame.size, Image.BILINEAR)
        frame.paste(base)
        for layer, bx, by, d in self.bands:
            s, ox, oy = cam.map(t, d)
            blit(frame, layer, s, ox, oy, bx, by)


class VideoPlate:
    """Decode a Veo clip with ffmpeg into raw frames at the render fps (held on the last frame)."""

    def __init__(self, path, CW, CH, fps):
        cmd = ["ffmpeg", "-loglevel", "error", "-i", path, "-vf",
               f"fps={fps},scale={CW}:{CH}:force_original_aspect_ratio=increase,crop={CW}:{CH}",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        n = CW * CH * 3
        self.frames = [Image.frombytes("RGB", (CW, CH), raw[i:i + n]).convert("RGBA") for i in range(0, len(raw) - n + 1, n)]
        self.fps, self.bands, self.base_d = fps, [], 0.35

    def draw(self, frame, cam, t):
        img = self.frames[min(len(self.frames) - 1, int(t * self.fps))]
        s, ox, oy = cam.map(t, self.base_d)
        b = tuple(int(round(v)) for v in (-ox / s, -oy / s, (frame.width - ox) / s, (frame.height - oy) / s))
        frame.paste(img.crop(b).resize(frame.size, Image.BILINEAR))


# ------------------------------------------------------------------ living effects
class FX:
    """Cheap full-frame life: drifting dust motes and a soft light sweep across the paper."""

    def __init__(self, names, W, H, dur, seed=0):
        import random
        rnd = random.Random(seed)
        self.W, self.H, self.dur = W, H, dur
        self.dust = []
        if "dust" in names:
            for _ in range(int(W * H / 130000)):
                r = rnd.randint(2, 5)
                dot = Image.new("RGBA", (r * 6, r * 6), (0, 0, 0, 0))
                ImageDraw.Draw(dot).ellipse((r * 2, r * 2, r * 4, r * 4), fill=(255, 250, 235, rnd.randint(70, 140)))
                dot = dot.filter(ImageFilter.GaussianBlur(r * 0.8))
                self.dust.append((dot, rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(-8, 8), rnd.uniform(-18, -4),
                                  rnd.uniform(0, 6.28)))
        self.sweep = None
        if "sweep" in names:
            band = Image.new("L", (W * 2, H), 0)
            d = ImageDraw.Draw(band)
            for i in range(0, W // 2, 4):   # soft diagonal highlight
                a = int(34 * (1 - abs(i - W / 4) / (W / 4)) ** 2)
                d.line([(W // 2 + i, 0), (i, H)], fill=a, width=5)
            self.sweep = Image.new("RGBA", (W * 2, H), (255, 252, 240, 0))
            self.sweep.putalpha(band)

    def draw(self, frame, t):
        if self.sweep is not None:
            p = clamp01(t / self.dur)
            x = int(-self.W * 1.2 + p * self.W * 2.2)
            vx0, vx1 = max(0, x), min(self.W, x + self.sweep.width)
            if vx1 > vx0:
                frame.alpha_composite(self.sweep.crop((vx0 - x, 0, vx1 - x, self.H)), (vx0, 0))
        for dot, x, y, vx, vy, ph in self.dust:
            px = (x + vx * t + math.sin(t * 0.9 + ph) * 12) % (self.W + 40) - 20
            py = (y + vy * t) % (self.H + 40) - 20
            frame.alpha_composite(dot, (int(px), int(py)))


# ------------------------------------------------------------------ render one shot
def render_shot(doc, beat, shot, shot_dur, t0_in_beat, captions, out_path, project_dir, fps, W, H, preview=False):
    CW, CH = int(W * SUPER), int(H * SUPER)
    plate_path = os.path.join(project_dir, shot["plate_path"]) if not os.path.isabs(shot["plate_path"]) else shot["plate_path"]
    g = int(doc.get("grain", 22))
    parallax = float(shot.get("parallax", doc.get("parallax", 1.0)))
    if shot.get("motion") == "veo" and shot.get("clip_path"):
        cp = shot["clip_path"] if os.path.isabs(shot["clip_path"]) else os.path.join(project_dir, shot["clip_path"])
        plate = VideoPlate(cp, CW, CH, fps)
    else:
        flat = shot.get("plate_kind") == "procedural" or shot.get("flat", False)
        plate = ParallaxPlate(plate_path, CW, CH, grain=g, parallax=parallax, flat=flat)
    layers = [Layer(l, CW, CH, project_dir, fps) for l in presets.layers_of(shot)]
    cam = Camera(shot.get("camera", "push_in"), shot_dur, CW, CH, W, H,
                 float(shot.get("camera_strength", 1.0)), parallax)
    fx = FX(shot.get("fx", doc.get("fx", ["dust", "sweep"])), W, H, shot_dur, seed=hash(out_path) & 0xff)
    n = int(round(shot_dur * fps))

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "24" if preview else "19", "-pix_fmt", "yuv420p", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frame = Image.new("RGBA", (W, H))
    for i in range(n):
        t = i / fps
        plate.draw(frame, cam, t)
        for L in layers:
            s, ox, oy = cam.map(t, L.depth)
            r = L.render(t, s)
            if r:
                img, (cx, cy) = r
                frame.alpha_composite(img, (int(cx * s + ox - img.width / 2), int(cy * s + oy - img.height / 2)))
        fx.draw(frame, t)
        if captions:
            r = captions.render(t0_in_beat + t)
            if r:
                img, (cx, cy) = r
                frame.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {out_path}")


def compose_still(doc, shot, shot_dur, t, project_dir, W, H, parallax=False):
    """One finished-looking frame of a shot at time t (used by preview_frame.py)."""
    CW, CH = int(W * SUPER), int(H * SUPER)
    plate_path = os.path.join(project_dir, shot["plate_path"]) if not os.path.isabs(shot["plate_path"]) else shot["plate_path"]
    plate = ParallaxPlate(plate_path, CW, CH, grain=int(doc.get("grain", 22)),
                          parallax=(float(shot.get("parallax", doc.get("parallax", 1.0))) if parallax else 0),
                          flat=shot.get("plate_kind") == "procedural")
    layers = [Layer(l, CW, CH, project_dir, 30) for l in presets.layers_of(shot)]
    cam = Camera(shot.get("camera", "push_in"), shot_dur, CW, CH, W, H, float(shot.get("camera_strength", 1.0)),
                 float(shot.get("parallax", doc.get("parallax", 1.0))))
    frame = Image.new("RGBA", (W, H))
    plate.draw(frame, cam, t)
    for L in layers:
        s, ox, oy = cam.map(t, L.depth)
        r = L.render(t, s)
        if r:
            img, (cx, cy) = r
            frame.alpha_composite(img, (int(cx * s + ox - img.width / 2), int(cy * s + oy - img.height / 2)))
    return frame


def _job(args):
    doc, beat, shot, d, t0, phrases, out, project_dir, fps, W, H, preview, cap_cfg = args
    styles.apply_theme(doc.get("theme"))      # worker processes start fresh — re-apply the palette/fonts
    captions = CaptionTrack(phrases, W, H, cap_cfg) if phrases else None
    render_shot(doc, beat, shot, d, t0, captions, out, project_dir, fps, W, H, preview)
    return out


def run(project_dir, only=None, preview=False, workers=None, force=False):
    bpath = os.path.join(project_dir, "beats.json")
    with open(bpath, encoding="utf-8") as f:
        doc = json.load(f)
    presets.expand_doc(doc)
    W, H = styles.frame_size(doc.get("aspect", "9:16"))
    fps = int(doc.get("fps", 30))
    if preview:
        W, H, fps = W // 2, H // 2, 12
    cap_cfg = doc.get("captions", {"enabled": True})
    clip_dir = os.path.join(project_dir, "clips")
    os.makedirs(clip_dir, exist_ok=True)
    jobs = []
    tr_cfg = doc.get("transitions", {"default": "tear", "dur": 0.45})
    tr_default, tr_dur = tr_cfg.get("default", "tear"), float(tr_cfg.get("dur", 0.45))
    first_shot = True

    for beat in doc["beats"]:
        shots = beat.get("shots", [])
        if not shots:
            continue
        planned = sum(float(s.get("dur", 4)) for s in shots)
        audio_d = float(beat.get("audio_duration", 0) or 0)
        target = max(planned, audio_d + float(doc.get("beat_tail", 0.35))) if audio_d else planned
        k = target / planned
        durs = [float(s.get("dur", 4)) * k for s in shots]
        beat["render_duration"] = round(target, 3)
        phrases = None
        if cap_cfg.get("enabled", True) and beat.get("narration"):
            phrases = phrase_captions(beat["narration"], beat.get("word_timings"), audio_d or target,
                                      max_words=int(cap_cfg.get("max_words", 5)))
        t0 = 0.0
        for shot, d in zip(shots, durs):
            key = f"{beat['id']}{shot.get('id', '')}"
            # a transition (rendered by assemble.py) occupies the first `td` seconds of this shot's slot
            kind = shot.get("transition", tr_default)
            td = 0.0 if (first_shot or kind in ("cut", "none", None)) else min(tr_dur, d * 0.25)
            first_shot = False
            shot["transition_kind"] = kind if td > 0 else "cut"
            shot["transition_dur"] = round(td, 3)
            shot["render_duration"] = round(d, 3)          # full slot (transition + clip)
            clip_d = d - td
            if only and key not in only:
                t0 += d; continue
            out = os.path.join(clip_dir, f"shot_{key}{'_preview' if preview else ''}.mp4")
            import hashlib
            shot_core = {k: v for k, v in shot.items() if k not in ("clip_sig", "clip_render", "render_duration",
                                                                     "transition_kind", "transition_dur")}
            sig = hashlib.md5(json.dumps([shot_core, clip_d, t0 + td, phrases, fps, W, H, doc.get("theme"), doc.get("fx"),
                                          doc.get("parallax"), doc.get("grain"), cap_cfg], sort_keys=True,
                                         ensure_ascii=False, default=str).encode()).hexdigest()[:12]
            if not force and os.path.exists(out) and shot.get("clip_sig") == sig:
                print(f"  [{key}] up to date")
            else:
                jobs.append((doc, beat, shot, clip_d, t0 + td, phrases, out, project_dir, fps, W, H, preview, cap_cfg))
            shot["clip_render"] = os.path.relpath(out, project_dir)
            shot["clip_sig"] = sig
            t0 += d
    import multiprocessing as mp
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    print(f"rendering {len(jobs)} shots with {workers} worker(s) …")
    if workers == 1:
        for j in jobs:
            print(" ", os.path.basename(_job(j)))
    else:
        with mp.get_context("spawn").Pool(workers) as pool:
            for out in pool.imap_unordered(_job, jobs):
                print(" ", os.path.basename(out))
    with open(bpath, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("done →", clip_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--only", default=None)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--workers", type=int, default=None, help="parallel shots (default: CPU cores - 1)")
    ap.add_argument("--force", action="store_true", help="re-render even if a clip is up to date")
    a = ap.parse_args()
    run(os.path.abspath(a.project), only=set(a.only.split(",")) if a.only else None, preview=a.preview,
        workers=a.workers, force=a.force)
