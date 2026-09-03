#!/usr/bin/env python3
"""
styles.py — prompt composition for vox-ar.

Two kinds of generated images, both WITHOUT any text (text is composited by code):
  * plate   — the full-frame collage background for a shot
  * cutout  — one isolated element (person / object / doc) on a flat white background,
              to be background-removed and animated as a paper sticker

Theme presets describe the look; `arabic-newsprint` is the تريكات / Vox-investigative
look seen in the reference video.
"""

THEMES = {
    "arabic-newsprint": {
        "plate_variant": "cream", "font": "cairo", "stamp_font": "kufi",
        "name_ar": "جريدة استقصائية",
        "base": (
            "mixed-media investigative-documentary paper collage in the style of Vox explainers: "
            "aged yellowed newsprint and torn newspaper clippings with dense Arabic newspaper columns "
            "(illegible small print, no readable words), cut-out black-and-white archival press photographs "
            "with scissor-cut white borders and soft paper drop shadows, masking tape strips, red push pins, "
            "halftone print dots, red pen annotations, faint coffee stains, photocopy grain. "
            "Flat-lay scanned look, straight-on, high contrast, tactile, hand-assembled. NOT 3D, NOT CGI."
        ),
        "palette": "aged cream newsprint, charcoal black, stamp red, highlighter yellow, faded sepia",
        "bg": "aged cream newsprint",
        "cutout_style": (
            "black-and-white archival press-photo look with visible halftone print dots and photocopy grain, "
            "high contrast, slightly faded"
        ),
        "music_hint": "tense investigative documentary underscore, ticking pulse, low strings, minimal",
        "motion": "punchy",
    },
    "retro-magazine": {
        "name_ar": "مجلة ريترو",
        "plate_variant": "cream", "font": "changa", "stamp_font": "kufi",
        "colors": {"paper": (240, 226, 196, 255), "paper_dark": (214, 196, 160, 255), "ink": (40, 30, 24, 255),
                   "red": (200, 60, 40, 255), "yellow": (230, 176, 40, 255), "white": (250, 244, 230, 255),
                   "black": (30, 24, 20, 255), "blue": (40, 120, 130, 255)},
        "base": (
            "vintage 1950s-60s magazine paper collage: bold flat retro colors, mid-century illustrated "
            "cut-out figures, torn paper edges, tape corners, Ben-Day dots, aged paper texture. "
            "Flat-lay scanned look, straight-on, high contrast. NOT 3D, NOT CGI."
        ),
        "palette": "mustard yellow, teal, cherry red, cream, sepia",
        "bg": "warm cream paper",
        "cutout_style": "mid-century printed illustration look, flat colors, halftone dots",
        "music_hint": "upbeat retro lounge, brushed drums, instrumental",
        "motion": "punchy",
    },
    "modern-editorial": {
        "name_ar": "افتتاحية حديثة",
        "base": (
            "modern editorial paper collage in the style of contemporary Vox explainers: crisp white and off-white "
            "paper, cut-out photographs with clean white scissor borders, bold flat color blocks (black, signal red, "
            "warm yellow), thin black rules, subtle paper grain, minimal, lots of negative space. Straight-on, flat-lay. "
            "NOT 3D, NOT CGI."
        ),
        "palette": "off-white, black, signal red, warm yellow",
        "bg": "off-white paper",
        "cutout_style": "clean contemporary photographic look, high contrast, slightly desaturated",
        "music_hint": "modern minimal electronic pulse, marimba, instrumental",
        "motion": "punchy",
        "plate_variant": "white", "font": "cairo", "stamp_font": "kufi",
        "colors": {"paper": (246, 243, 236, 255), "paper_dark": (225, 220, 210, 255), "ink": (18, 18, 18, 255),
                   "red": (226, 40, 40, 255), "yellow": (255, 205, 0, 255), "white": (255, 255, 255, 255),
                   "black": (10, 10, 10, 255), "blue": (20, 60, 200, 255)},
    },
    "dark-investigative": {
        "name_ar": "استقصائي داكن",
        "base": (
            "dark investigative paper collage: matte black and charcoal paper, torn newsprint fragments, "
            "black-and-white archival photographs with white scissor borders, red pen marks, red string, "
            "push pins, harsh flash-lit evidence-board feel, halftone dots, film grain. Flat-lay, straight-on. NOT 3D."
        ),
        "palette": "matte black, charcoal, bone white, blood red, dim yellow",
        "bg": "matte black paper",
        "cutout_style": "black-and-white archival press-photo look, heavy grain, high contrast",
        "music_hint": "dark tense investigative drone, low pulse, sparse piano",
        "motion": "punchy",
        "plate_variant": "black", "font": "cairo", "stamp_font": "kufi",
        "colors": {"paper": (32, 30, 28, 255), "paper_dark": (18, 17, 16, 255), "ink": (240, 236, 228, 255),
                   "red": (214, 34, 34, 255), "yellow": (236, 190, 40, 255), "white": (245, 242, 236, 255),
                   "black": (8, 8, 8, 255), "blue": (60, 90, 150, 255)},
    },
    "blueprint": {
        "name_ar": "مخططات هندسية",
        "base": (
            "technical blueprint collage: deep blue grid paper with white drafting lines, cut-out photographs and "
            "diagrams taped on, white chalk annotations, yellow paper labels, measurement arrows, halftone dots. "
            "Flat-lay, straight-on. NOT 3D."
        ),
        "palette": "blueprint blue, white, yellow, black",
        "bg": "blue grid paper",
        "cutout_style": "clean photographic look with a slight cyan tint, high contrast",
        "music_hint": "techy minimal electronic, clicks and soft synth",
        "motion": "calm",
        "plate_variant": "graph", "font": "kufi", "stamp_font": "kufi",
        "colors": {"paper": (28, 62, 122, 255), "paper_dark": (18, 44, 92, 255), "ink": (240, 246, 255, 255),
                   "red": (255, 80, 80, 255), "yellow": (255, 214, 60, 255), "white": (245, 248, 255, 255),
                   "black": (10, 20, 40, 255), "blue": (28, 62, 122, 255)},
    },
    "clean-flat": {
        "name_ar": "فلات نظيف",
        "base": (
            "clean modern flat 2D illustrated collage in Vox explainer motion-graphic style: simple "
            "bold vector-illustration cut-outs, limited contemporary palette, generous negative space, "
            "subtle paper texture. Straight-on, high contrast. NOT 3D, NOT CGI."
        ),
        "palette": "off-white, navy, coral red, mustard",
        "bg": "off-white paper",
        "cutout_style": "flat vector illustration, simple confident shapes",
        "music_hint": "light modern electronic pulse, marimba, instrumental",
        "motion": "calm",
    },
}
DEFAULT_THEME = "arabic-newsprint"

NO_TEXT = (
    " Absolutely NO text, NO letters, NO numbers, NO logos, NO watermarks anywhere in the image "
    "(newspaper columns must be abstract illegible print texture only)."
)


def theme(name):
    return THEMES.get(name or DEFAULT_THEME, THEMES[DEFAULT_THEME])


_BASE_PALETTE = None


def apply_theme(name):
    """Switch the global look (paperfx palette + default fonts) to a theme. Safe to call repeatedly."""
    import paperfx
    import artext
    global _BASE_PALETTE
    if _BASE_PALETTE is None:
        _BASE_PALETTE = dict(paperfx.PALETTE)
    t = theme(name)
    paperfx.PALETTE.clear()
    paperfx.PALETTE.update(_BASE_PALETTE)
    paperfx.PALETTE.update(t.get("colors", {}))
    artext.DEFAULT_FAMILY = t.get("font", "cairo")
    paperfx.THEME_NAME = name or DEFAULT_THEME
    return t


def plate_prompt(scene, theme_name=DEFAULT_THEME, bg=None, aspect="9:16", feel=None, negative_space=True):
    t = theme(theme_name)
    bg = bg or t["bg"]
    ns = (" Leave clear negative space (plain paper areas) for headlines to be added later — "
          "keep the busiest details in the outer third, the center-top band mostly calm.") if negative_space else ""
    feel_s = f" Mood: {feel}." if feel else ""
    return (f"{t['base']} Palette: {t['palette']}. Background: bold flat {bg} paper. "
            f"SCENE as layered paper cut-outs: {scene}.{feel_s}{ns}{NO_TEXT} Aspect ratio {aspect}.")


def cutout_prompt(subject, theme_name=DEFAULT_THEME, extra=None):
    """One isolated element for background removal."""
    t = theme(theme_name)
    ex = f" {extra}." if extra else ""
    return (f"A single isolated {subject}, {t['cutout_style']}, rendered as a printed paper cutout "
            f"with a thin white scissor-cut border, centered, fully inside the frame, on a plain "
            f"pure white background, no shadow, no other objects.{ex}{NO_TEXT}")


CUTOUT_EFFECTS = {
    "censor_eyes": "a solid black rectangular censor bar covers the eyes",
    "bw": "strictly black-and-white",
    "torn": "the photo edges are roughly torn",
    "old": "heavily aged, creased and faded",
}


def apply_effects_to_prompt(prompt, effects):
    parts = [CUTOUT_EFFECTS[e] for e in (effects or []) if e in CUTOUT_EFFECTS]
    return prompt + (" " + ", ".join(parts) + "." if parts else "")


ASPECTS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}


def frame_size(aspect):
    return ASPECTS.get(aspect, ASPECTS["9:16"])
