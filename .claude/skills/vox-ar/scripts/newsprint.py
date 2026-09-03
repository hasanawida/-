#!/usr/bin/env python3
"""
newsprint.py — procedural Arabic newspaper plates. Zero API calls, ~1s each.

A plate = aged paper + real (but meaningless) Arabic column text in tiny type + faded
headline blocks + halftone "photo" rectangles + rules, creases, stains, vignette.
Variants: "cream" (default), "red", "black", "yellow", "blue" (bold flat paper with a
torn newsprint window) — use the bold ones for emphasis beats.

Because the text is real Arabic set in a real font it reads as authentic newsprint,
which is exactly what the image models struggle to fake without garbling letters.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps

import artext
import paperfx

WORDS = ("في من على إلى عن أن هذا هذه التي الذي كان كانت بعد قبل بين خلال حتى عند مع لكن ثم أو لم لا ما "
         "الحكومة الوزارة المجلس الرئيس الوزير المدينة الدولة الشعب العالم السنة اليوم الأسبوع الشهر "
         "الاقتصاد السوق الشركة البنك الأسعار النفط التجارة الصناعة الزراعة التعليم الجامعة المدرسة "
         "الطلاب المعلم الصحة المستشفى الطبيب العلاج الدواء البحث العلم التقنية الحاسوب الإنترنت "
         "الأخبار الصحيفة المراسل التقرير البيان المؤتمر الاجتماع القرار القانون المحكمة القاضي "
         "الشرطة الأمن الجيش الحرب السلام الاتفاق المفاوضات الحدود السفر المطار الطريق السيارة "
         "القطار البحر الجبل النهر المطر الشمس الليل النهار الصباح المساء الأسرة الأطفال الأم الأب "
         "البيت الشارع الحي السكان العمل الوظيفة الراتب الضرائب الميزانية الأرقام النسبة الزيادة "
         "الانخفاض التطور المستقبل الماضي التاريخ الثقافة الفن السينما الموسيقى الرياضة الفريق "
         "المباراة البطولة الهدف اللاعب المدرب الجمهور النتيجة الفوز الخسارة قال أضاف أكد أوضح أشار "
         "ذكر أعلن كشف طالب دعا رفض وافق بدأ انتهى استمر تراجع ارتفع بلغ وصل").split()

HEADS = ["تطورات جديدة في الملف", "مصادر تكشف التفاصيل", "بيان رسمي صادر اليوم", "الأرقام تتحدث",
         "ما وراء الخبر", "قرار مرتقب الأسبوع المقبل", "تقرير خاص", "من الأرشيف", "أزمة صامتة",
         "الحقيقة الكاملة", "شهادات من الداخل", "على خطى التاريخ"]


def _filler(rnd, n):
    return " ".join(rnd.choice(WORDS) for _ in range(n))


def _column(draw, x, y0, y1, col_w, font, rnd, ink):
    """Justified-looking tiny Arabic text lines inside a column (right aligned)."""
    lh = int(font.size * 1.55)
    y = y0
    while y + lh <= y1:
        # paragraph break now and then
        if rnd.random() < 0.06:
            y += lh // 2
            continue
        line = _filler(rnd, rnd.randint(4, 8))
        # trim to width
        while artext.text_width(draw, line, font) > col_w and " " in line:
            line = line.rsplit(" ", 1)[0]
        artext.draw_text(draw, (x + col_w, y), line, font, ink, anchor="ra")
        y += lh


def _halftone_photo(w, h, rnd):
    """Grey halftone 'photo' block — a plausible newspaper picture without any content."""
    base = Image.effect_noise((w // 4, h // 4), 64).resize((w, h), Image.BILINEAR)
    base = base.filter(ImageFilter.GaussianBlur(6))
    # a couple of dark blobs (figures/buildings)
    d = ImageDraw.Draw(base)
    for _ in range(rnd.randint(2, 4)):
        bx, by = rnd.randint(0, w), rnd.randint(h // 3, h)
        bw, bh = rnd.randint(w // 5, w // 2), rnd.randint(h // 3, h)
        d.ellipse((bx - bw // 2, by - bh, bx + bw // 2, by + bh // 3), fill=rnd.randint(40, 110))
    base = base.filter(ImageFilter.GaussianBlur(3))
    base = ImageOps.autocontrast(base, cutoff=4).point(lambda v: 60 + v * 0.6)
    rgb = Image.merge("RGB", (base, base, base)).convert("RGBA")
    rgb = paperfx.apply_halftone(rgb, cell=5, strength=0.7)
    return rgb


def plate(w, h, variant="cream", seed=0, density=1.0, window=True):
    """Return an RGBA newspaper plate of size w×h."""
    rnd = random.Random(seed)
    paper_col = {"cream": paperfx.PALETTE["paper"], "red": paperfx.PALETTE["red"],
                 "black": (28, 26, 24, 255), "yellow": paperfx.PALETTE["yellow"],
                 "blue": (52, 78, 120, 255), "grey": (150, 150, 145, 255)}.get(variant, paperfx.PALETTE["paper"])
    if variant == "cream":
        img = _newspaper(w, h, rnd, density)
    elif variant == "white":          # modern editorial: clean off-white paper, faint rules, one halftone block
        img = Image.new("RGBA", (w, h), paperfx.PALETTE["paper"])
        fib = Image.effect_noise((w, h), 14).filter(ImageFilter.GaussianBlur(1.2))
        fib = Image.merge("RGB", (fib, fib, fib)).convert("RGBA")
        img = Image.blend(img, ImageChops.multiply(img, fib), 0.18)
        d = ImageDraw.Draw(img)
        ink = tuple(paperfx.PALETTE["ink"][:3]) + (60,)
        m = int(w * 0.04)
        d.line((m, int(h * 0.08), w - m, int(h * 0.08)), fill=ink, width=3)
        d.line((m, h - int(h * 0.08), w - m, h - int(h * 0.08)), fill=ink, width=2)
        if rnd.random() < 0.7:
            pw, ph = int(w * 0.22), int(h * 0.3)
            photo = _halftone_photo(pw, ph, rnd)
            photo.putalpha(photo.split()[3].point(lambda v: v * 45 // 255))
            img.alpha_composite(photo, (int(w * rnd.uniform(0.04, 0.7)), int(h * rnd.uniform(0.15, 0.55))))
    elif variant == "graph":          # blueprint: grid paper
        img = Image.new("RGBA", (w, h), paperfx.PALETTE["paper"])
        d = ImageDraw.Draw(img)
        line = tuple(paperfx.PALETTE["ink"][:3]) + (34,)
        strong = tuple(paperfx.PALETTE["ink"][:3]) + (70,)
        step = max(24, w // 48)
        for x in range(0, w, step):
            d.line((x, 0, x, h), fill=strong if (x // step) % 5 == 0 else line, width=1)
        for y in range(0, h, step):
            d.line((0, y, w, y), fill=strong if (y // step) % 5 == 0 else line, width=1)
        fib = Image.effect_noise((w, h), 18).filter(ImageFilter.GaussianBlur(1.0))
        fib = Image.merge("RGB", (fib, fib, fib)).convert("RGBA")
        img = Image.blend(img, ImageChops.multiply(img, fib), 0.2)
    else:
        # bold flat paper with a torn newspaper window
        img = Image.new("RGBA", (w, h), paper_col)
        fib = Image.effect_noise((w, h), 26).filter(ImageFilter.GaussianBlur(1.0))
        fib = Image.merge("RGB", (fib, fib, fib)).convert("RGBA")
        img = Image.blend(img, ImageChops.multiply(img, fib), 0.25)
        if window:
            nw, nh = int(w * rnd.uniform(0.45, 0.6)), int(h * rnd.uniform(0.5, 0.7))
            news = _newspaper(nw, nh, random.Random(seed + 7), density)
            torn = paperfx.torn_paper(nw, nh, color="paper", jag=max(8, nw // 30), seed=seed + 3, shadow=True)
            # paste newspaper inside the torn shape
            mask = torn.split()[3]
            canvas = Image.new("RGBA", torn.size, (0, 0, 0, 0))
            off = ((torn.width - nw) // 2, (torn.height - nh) // 2)
            canvas.alpha_composite(torn)
            newsl = Image.new("RGBA", torn.size, (0, 0, 0, 0))
            newsl.alpha_composite(news, off)
            newsl.putalpha(ImageChops.multiply(newsl.split()[3], mask))
            canvas.alpha_composite(newsl)
            canvas = canvas.rotate(rnd.uniform(-4, 4), resample=Image.BICUBIC, expand=True)
            img.alpha_composite(canvas, (int(w * rnd.uniform(0.05, 0.4)) - 20, int(h * rnd.uniform(0.08, 0.25)) - 20))
    img.alpha_composite(paperfx.grain_overlay(w, h, strength=18, seed=seed % 3))
    return img


def _newspaper(w, h, rnd, density=1.0):
    img = paperfx.paper_background(w, h, seed=rnd.randint(0, 999))
    d = ImageDraw.Draw(img)
    ink = (96, 88, 80, 255)          # deliberately soft: the plate must never compete with real headlines
    ink_head = (78, 72, 66, 255)
    unit = min(w, h)
    small = artext.font(max(10, int(unit * 0.013)), "kufi", weight=b"Regular")
    head = artext.font(int(unit * 0.05), "cairo")
    sub = artext.font(int(unit * 0.024), "cairo", weight=b"Bold")
    margin = int(w * 0.04)
    ncols = 5 if w >= h else 3
    gutter = int(w * 0.016)
    col_w = (w - margin * 2 - gutter * (ncols - 1)) // ncols
    top = int(h * 0.05)
    # masthead rule
    d.line((margin, top, w - margin, top), fill=ink_head, width=3)
    d.line((margin, top + 6, w - margin, top + 6), fill=ink_head, width=1)
    top += int(unit * 0.03)
    # headline block spanning 2-3 columns, right side (RTL)
    span = rnd.randint(2, min(3, ncols))
    hx1 = w - margin
    hx0 = hx1 - (col_w * span + gutter * (span - 1))
    ht = rnd.choice(HEADS)
    artext.draw_text(d, (hx1, top), ht, head, ink_head, anchor="ra")
    hy = top + int(head.size * 1.5)
    artext.draw_text(d, (hx1, hy), _filler(rnd, 7), sub, ink, anchor="ra")
    hy += int(sub.size * 1.8)
    # photo block under the headline (in the rightmost column pair)
    if rnd.random() < 0.85:
        pw, ph = col_w * 2 + gutter, int(h * rnd.uniform(0.18, 0.28))
        photo = _halftone_photo(pw, ph, rnd)
        img.alpha_composite(photo, (hx1 - pw, hy))
        d.rectangle((hx1 - pw, hy, hx1, hy + ph), outline=ink, width=1)
        photo_bottom = hy + ph + int(unit * 0.015)
    else:
        photo_bottom = hy
    # columns
    bottom = h - int(h * 0.05)
    for c in range(ncols):
        x = w - margin - col_w - c * (col_w + gutter)
        y0 = top
        if x + col_w > hx0 - 1:          # under headline block
            y0 = photo_bottom if x + col_w > hx1 - (col_w * 2 + gutter) - 1 else hy
        # occasional sub-head inside a column
        if rnd.random() < 0.5 and y0 < bottom - unit * 0.2:
            artext.draw_text(d, (x + col_w, y0), rnd.choice(HEADS), sub, ink_head, anchor="ra")
            y0 += int(sub.size * 1.9)
        _column(d, x, y0, bottom, col_w, small, rnd, ink)
        if c < ncols - 1:
            xr = x - gutter // 2
            d.line((xr, top, xr, bottom), fill=(150, 140, 125, 255), width=1)
    # bottom rule
    d.line((margin, bottom + 6, w - margin, bottom + 6), fill=ink_head, width=2)
    # fade the whole print a little (aged) and add a crease
    img = Image.blend(img, paperfx.paper_background(w, h, seed=rnd.randint(0, 999)), min(0.85, 0.5 * (2 - density)))
    crease = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(crease)
    cy = int(h * rnd.uniform(0.3, 0.7))
    cd.line((0, cy, w, cy + rnd.randint(-20, 20)), fill=(90, 70, 40, 40), width=3)
    crease = crease.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(crease)
    return img


if __name__ == "__main__":
    import sys
    for i, v in enumerate(["cream", "red", "black", "yellow"]):
        plate(1920, 1080, v, seed=i).convert("RGB").save(f"/tmp/np_{v}.jpg", quality=88)
    print("saved /tmp/np_*.jpg")
