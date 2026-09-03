#!/usr/bin/env python3
"""
presets.py — compact shot authoring. Instead of hand-placing every layer, a shot can say:

  {"id": "a", "dur": 5, "preset": "hero_right", "bg": "cream", "camera": "push_in",
   "cutout": "1940s British mathematician, portrait", "effects": ["bw", "old"],
   "headline": "آلان تورينغ", "sub": "فكّ شيفرة النازيين", "stamp": "ملف سري", "mark": "circle"}

and expand() turns it into the full `layers` list with good positions and staggered timing
for the project's aspect ratio. Any explicit `layers` on the shot are kept and appended.

Presets:  hero_right · hero_left · hero_center · title · quote · number · split · list · checklist ·
          stats (bar chart) · timeline · versus · callouts · note (sticky)
Extras on any preset: value/prefix/suffix (counting number), bubble, badge
Fields:   cutout, cutout2 (split), effects, headline, headline_bar (yellow|red|white|black),
          sub, stamp, mark (circle|arrow|underline|none), items (list preset), tape (bool), pin (bool)
"""

# positions are (x, y) fractions; a preset gives values per aspect family
LANDSCAPE = {
    "hero_right":  dict(cut=(0.66, 0.52, 0.34), head=(0.24, 0.20, 0.36), sub=(0.24, 0.50, 0.34), stamp=(0.30, 0.72), mark=(0.66, 0.52)),
    "hero_left":   dict(cut=(0.32, 0.52, 0.34), head=(0.72, 0.20, 0.36), sub=(0.72, 0.50, 0.34), stamp=(0.70, 0.72), mark=(0.32, 0.52)),
    "hero_center": dict(cut=(0.50, 0.50, 0.30), head=(0.50, 0.14, 0.60), sub=(0.50, 0.72, 0.5), stamp=(0.80, 0.26), mark=(0.50, 0.50)),
    "title":       dict(cut=None, head=(0.50, 0.40, 0.7), sub=(0.50, 0.58, 0.6), stamp=(0.78, 0.24), mark=(0.50, 0.40)),
    "quote":       dict(cut=None, head=(0.50, 0.42, 0.7), sub=(0.50, 0.62, 0.5), stamp=(0.22, 0.24), mark=(0.50, 0.42)),
    "number":      dict(cut=None, head=(0.30, 0.42, 0.34), sub=(0.70, 0.42, 0.4), stamp=(0.30, 0.68), mark=(0.30, 0.42)),
    "split":       dict(cut=(0.28, 0.54, 0.26), cut2=(0.72, 0.54, 0.26), head=(0.50, 0.14, 0.6), sub=(0.50, 0.74, 0.5), stamp=(0.50, 0.50), mark=(0.28, 0.54)),
    "list":        dict(cut=(0.72, 0.52, 0.28), head=(0.28, 0.13, 0.4), items_x=0.28, items_y0=0.40, items_dy=0.14, stamp=(0.72, 0.24), mark=None),
    "checklist":   dict(cut=(0.74, 0.52, 0.26), head=(0.30, 0.13, 0.44), items_x=0.34, items_y0=0.38, items_dy=0.14, stamp=(0.74, 0.24), mark=None, check_x=0.10),
    "stats":       dict(cut=None, head=(0.50, 0.12, 0.7), bars=(0.50, 0.52, 0.66, 0.5), stamp=(0.12, 0.2), mark=None),
    "timeline":    dict(cut=None, head=(0.50, 0.16, 0.7), tl=(0.50, 0.58, 0.84), stamp=(0.86, 0.3), mark=None),
    "versus":      dict(cut=(0.24, 0.52, 0.28), cut2=(0.76, 0.52, 0.28), head=(0.50, 0.12, 0.6), vs=(0.50, 0.52), lab=(0.24, 0.84), lab2=(0.76, 0.84), stamp=None, mark=None),
    "callouts":    dict(cut=(0.62, 0.52, 0.4), head=(0.20, 0.14, 0.32), sub=None, stamp=(0.20, 0.8), mark=None),
    "note":        dict(cut=(0.32, 0.52, 0.3), head=(0.72, 0.16, 0.4), sticky=(0.72, 0.5), sub=None, stamp=None, mark=None),
}
PORTRAIT = {
    "hero_right":  dict(cut=(0.50, 0.52, 0.66), head=(0.50, 0.14, 0.9), sub=(0.50, 0.70, 0.86), stamp=(0.76, 0.30), mark=(0.50, 0.52)),
    "hero_center": dict(cut=(0.50, 0.50, 0.62), head=(0.50, 0.13, 0.9), sub=(0.50, 0.71, 0.86), stamp=(0.76, 0.28), mark=(0.50, 0.50)),
    "title":       dict(cut=None, head=(0.50, 0.42, 0.9), sub=(0.50, 0.56, 0.86), stamp=(0.74, 0.28), mark=(0.50, 0.42)),
    "quote":       dict(cut=None, head=(0.50, 0.44, 0.9), sub=(0.50, 0.60, 0.8), stamp=(0.26, 0.28), mark=(0.50, 0.44)),
    "number":      dict(cut=None, head=(0.50, 0.40, 0.8), sub=(0.50, 0.56, 0.86), stamp=(0.50, 0.68), mark=(0.50, 0.40)),
    "split":       dict(cut=(0.50, 0.36, 0.5), cut2=(0.50, 0.66, 0.5), head=(0.50, 0.12, 0.9), sub=None, stamp=(0.78, 0.5), mark=(0.50, 0.36)),
    "list":        dict(cut=None, head=(0.50, 0.14, 0.9), items_x=0.50, items_y0=0.32, items_dy=0.13, stamp=(0.76, 0.28), mark=None),
    "checklist":   dict(cut=None, head=(0.50, 0.13, 0.9), items_x=0.56, items_y0=0.32, items_dy=0.12, stamp=(0.76, 0.24), mark=None, check_x=0.12),
    "stats":       dict(cut=None, head=(0.50, 0.12, 0.9), bars=(0.50, 0.46, 0.86, 0.36), stamp=(0.20, 0.24), mark=None),
    "timeline":    dict(cut=None, head=(0.50, 0.16, 0.9), tl=(0.50, 0.50, 0.9), stamp=(0.8, 0.3), mark=None),
    "versus":      dict(cut=(0.50, 0.32, 0.5), cut2=(0.50, 0.70, 0.5), head=(0.50, 0.10, 0.9), vs=(0.50, 0.51), lab=(0.50, 0.48), lab2=(0.50, 0.88), stamp=None, mark=None),
    "callouts":    dict(cut=(0.50, 0.52, 0.66), head=(0.50, 0.12, 0.9), sub=None, stamp=(0.76, 0.28), mark=None),
    "note":        dict(cut=(0.50, 0.38, 0.5), head=(0.50, 0.12, 0.9), sticky=(0.50, 0.64), sub=None, stamp=None, mark=None),
}
PORTRAIT["hero_left"] = PORTRAIT["hero_right"]

TIMING = dict(cut=0.1, cut2=0.5, head=0.5, sub=1.8, items0=0.8, items_dt=0.8, mark=2.5, stamp=3.2, tape=0.35, pin=0.4)


def expand(shot: dict, aspect: str = "9:16") -> list:
    """Return the layer list for a compact shot spec (or its explicit layers unchanged)."""
    name = shot.get("preset")
    if not name:
        return shot.get("layers", [])
    table = LANDSCAPE if aspect in ("16:9", "21:9") else PORTRAIT
    P = table.get(name) or table["hero_right"]
    portrait = table is PORTRAIT
    L = []
    hb = shot.get("headline_bar", "yellow")
    head_size = shot.get("headline_size", 0.075 if not portrait else 0.062)
    sub_size = shot.get("sub_size", 0.052 if not portrait else 0.046)

    if shot.get("cutout") and P.get("cut"):
        x, y, w = P["cut"]
        L.append({"type": "cutout", "subject": shot["cutout"], "effects": shot.get("effects", ["bw"]),
                  "x": x, "y": y, "w": shot.get("cutout_w", w), "rot": shot.get("cutout_rot", -3), "at": TIMING["cut"]})
        if shot.get("tape"):
            L.append({"type": "tape", "x": x, "y": y - w * 0.9 * (0.55 if portrait else 1.0) * 0.5, "w": 0.12, "rot": -7, "at": TIMING["tape"]})
        if shot.get("pin"):
            L.append({"type": "pin", "x": x - w * 0.35, "y": y - w * 0.5 * (0.55 if portrait else 1.0), "at": TIMING["pin"]})
    if shot.get("cutout2") and P.get("cut2"):
        x, y, w = P["cut2"]
        L.append({"type": "cutout", "subject": shot["cutout2"], "effects": shot.get("effects2", shot.get("effects", ["bw"])),
                  "x": x, "y": y, "w": w, "rot": 3, "at": TIMING["cut2"]})
    if shot.get("headline") and P.get("head"):
        x, y, mw = P["head"]
        L.append({"type": "headline", "text": shot["headline"], "bar": hb,
                  "fill": "white" if hb in ("red", "black") else "black", "size": head_size,
                  "x": x, "y": y, "rot": -2, "max_w": mw, "in": "slam", "at": TIMING["head"]})
    if shot.get("sub") and P.get("sub"):
        x, y, mw = P["sub"]
        L.append({"type": "headline", "text": shot["sub"], "bar": shot.get("sub_bar", "white"), "size": sub_size,
                  "x": x, "y": y, "rot": 2, "max_w": mw, "in": "pop", "at": TIMING["sub"]})
    if name == "list" and shot.get("items") and "items_x" in P:
        for i, it in enumerate(shot["items"][:4]):
            L.append({"type": "headline", "text": it, "bar": ["yellow", "white", "yellow", "white"][i % 4], "size": sub_size,
                      "x": P["items_x"], "y": P["items_y0"] + i * P["items_dy"], "rot": (-2, 2)[i % 2],
                      "max_w": 0.4 if not portrait else 0.86, "in": "slam", "at": TIMING["items0"] + i * TIMING["items_dt"]})
    mark = shot.get("mark")
    if mark and mark != "none" and P.get("mark"):
        mx, my = P["mark"]
        if mark == "circle":
            cw = (P["cut"][2] * 0.9) if P.get("cut") and shot.get("cutout") else 0.3
            L.append({"type": "circle", "x": mx, "y": my, "w": cw, "h": cw * (1.78 if not portrait else 0.56) * 0.9,
                      "in": "draw", "at": TIMING["mark"], "in_dur": 0.6})
        elif mark == "underline":
            hx, hy, _ = P.get("head") or (mx, my, 0)
            L.append({"type": "underline", "x": hx, "y": hy + head_size * 0.8, "w": 0.3 if not portrait else 0.6,
                      "in": "draw", "at": TIMING["mark"]})
        elif mark == "arrow":
            hx, hy, _ = P.get("head") or (mx - 0.3, my, 0)
            L.append({"type": "arrow", "x0": hx + (0.14 if hx < mx else -0.14), "y0": hy + 0.1,
                      "x1": mx + (-0.12 if hx < mx else 0.12), "y1": my - 0.05, "in": "draw", "at": TIMING["mark"]})
    if shot.get("stamp") and P.get("stamp"):
        x, y = P["stamp"]
        L.append({"type": "stamp", "text": shot["stamp"], "x": x, "y": y, "size": 0.055 if not portrait else 0.05,
                  "rot": -12 if x < 0.5 else 10, "in": "stamp", "at": TIMING["stamp"]})
    # ---- new mark presets
    dark = shot.get("bg") in ("black", "blue")
    ink = "white" if dark else "ink"
    if name == "quote":
        L.insert(0, {"type": "bigquote", "x": 0.86 if not portrait else 0.84, "y": 0.22, "at": 0.2, "size": 0.3})
    if name == "checklist" and shot.get("items"):
        for i, it in enumerate(shot["items"][:4]):
            text, ok = (it if isinstance(it, (list, tuple)) else (it, True))
            y = P["items_y0"] + i * P["items_dy"]
            L.append({"type": "headline", "text": text, "bar": "white", "size": sub_size, "x": P["items_x"], "y": y,
                      "rot": (-1.5, 1.5)[i % 2], "max_w": 0.4 if not portrait else 0.7, "in": "slam",
                      "at": TIMING["items0"] + i * TIMING["items_dt"]})
            L.append({"type": "check" if ok else "cross", "x": P["check_x"], "y": y, "size": 0.08,
                      "at": TIMING["items0"] + i * TIMING["items_dt"] + 0.35})
    if name == "stats" and shot.get("items"):
        x, y, w, h = P["bars"]
        L.append({"type": "bars", "items": shot["items"], "x": x, "y": y, "w": w, "h": h, "at": 0.9, "ink": ink,
                  "size": 0.034 if not portrait else 0.026, "label_w": 0.26 if not portrait else 0.34,
                  "in_dur": 0.5 * len(shot["items"])})
    if name == "timeline" and shot.get("items"):
        x, y, w = P["tl"]
        L.append({"type": "timeline", "items": shot["items"], "x": x, "y": y, "w": w, "at": 0.8, "ink": ink,
                  "size": 0.03, "in_dur": 0.6 * len(shot["items"])})
    if name == "versus":
        vx, vy = P["vs"]
        L.append({"type": "vs", "x": vx, "y": vy, "at": 1.4, "size": 0.16 if not portrait else 0.12})
        for key, pos in (("left", P["lab"]), ("right", P["lab2"])):
            if shot.get(key):
                L.append({"type": "headline", "text": shot[key], "bar": "yellow" if key == "left" else "red",
                          "size": sub_size, "x": pos[0], "y": pos[1], "rot": 0, "max_w": 0.3 if not portrait else 0.8,
                          "in": "pop", "at": 2.0 if key == "left" else 2.4})
    if name == "callouts" and shot.get("callouts"):
        for i, c in enumerate(shot["callouts"][:4]):
            L.append({"type": "callout", "text": c["text"], "x": c.get("x", 0.2), "y": c.get("y", 0.3 + i * 0.16),
                      "tx": c.get("tx", 0.6), "ty": c.get("ty", 0.5), "at": 1.0 + i * 0.9, "size": 0.034 if not portrait else 0.03})
    if name == "note" and shot.get("note"):
        sx, sy = P["sticky"]
        L.append({"type": "sticky", "text": shot["note"], "x": sx, "y": sy, "rot": -4, "at": 1.4, "size": 0.045 if not portrait else 0.04})
        L.append({"type": "pin", "x": sx, "y": sy - 0.13, "at": 1.7})
    if shot.get("value") is not None:      # any preset: a counting number instead of a static headline
        hx, hy, _ = P.get("head") or (0.5, 0.4, 0)
        L = [l for l in L if not (l.get("type") == "headline" and l.get("text") == shot.get("headline"))]
        L.append({"type": "counter", "value": shot["value"], "prefix": shot.get("prefix", ""), "suffix": shot.get("suffix", ""),
                  "x": hx, "y": hy, "at": TIMING["head"], "size": head_size * 1.15, "bar": hb, "in_dur": 1.6})
    if shot.get("bubble"):
        L.append({"type": "bubble", "text": shot["bubble"], "x": shot.get("bubble_x", 0.78 if not portrait else 0.7),
                  "y": shot.get("bubble_y", 0.74 if not portrait else 0.56), "at": 2.2, "size": 0.04 if not portrait else 0.034,
                  "max_w": 0.3 if not portrait else 0.5})
    if shot.get("badge"):
        L.append({"type": "badge", "text": shot["badge"], "x": 0.9 if not portrait else 0.84, "y": 0.2, "at": 2.8, "size": 0.14 if not portrait else 0.1})
    # explicit extra layers win / append
    L += shot.get("layers", [])
    return L


def layers_of(shot: dict) -> list:
    """The layers the pipeline should render: expanded preset layers (`_layers`) or explicit `layers`."""
    return shot.get("_layers") if shot.get("preset") else shot.get("layers", [])


def _key(l):
    return (l.get("type"), l.get("subject") or l.get("text") or l.get("image") or "", round(float(l.get("x", 0)), 2))


def expand_doc(doc: dict) -> dict:
    """Re-expand every preset shot on each load (so preset improvements apply), keeping generated
    asset paths from the previous expansion so images are never regenerated needlessly."""
    aspect = doc.get("aspect", "9:16")
    import styles
    styles.apply_theme(doc.get("theme"))
    for beat in doc.get("beats", []):
        for shot in beat.get("shots", []):
            if not shot.get("preset"):
                continue
            old = {_key(l): l for l in shot.get("_layers", [])}
            new = expand(shot, aspect)
            for l in new:
                o = old.get(_key(l))
                if o:
                    for k in ("path", "prompt"):
                        if k in o and k not in l:
                            l[k] = o[k]
            shot["_layers"] = new
            shot.pop("_expanded", None)
    return doc


if __name__ == "__main__":
    import json, sys
    demo = {"id": "a", "dur": 5, "preset": "hero_right", "cutout": "1940s mathematician portrait",
            "headline": "آلان تورينغ", "sub": "فكّ شيفرة النازيين", "stamp": "ملف سري", "mark": "circle", "tape": True}
    print(json.dumps(expand(demo, "16:9"), ensure_ascii=False, indent=1))
