#!/usr/bin/env python3
"""Generate advertising cards for the six stations (DE + EN).

    python3 setup/make_station_cards.py
    → assets/stations/<station>_<lang>.png   (1600×900 each)
    → assets/stations/overview_<lang>.png    (all six in one banner)
    → assets/stations/contact_<lang>.png     (preview sheet)

Design language mirrors the exhibit UI: dark background, per-station accent
colour, a mock "live screen" showing what visitors experience there, the
SKILL logo. Text is minimal on purpose — these are teasers, the manuals
carry the explanations.

NOTE: runs on macOS (uses the system's Helvetica Neue and Apple Color
Emoji). The generated PNGs are committed, so the Pi never needs this.
"""

import base64
import io
import math
import os
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit(
        "Missing dependency: pillow\n\n"
        "Easiest fix — the helper sets up a local venv and runs this for you:\n"
        "    bash setup/tools.sh stations        # add --editable for layer exports\n\n"
        "Or by hand (system Python refuses pip installs, PEP 668):\n"
        "    python3 -m venv .venv-tools\n"
        "    .venv-tools/bin/pip install -r dev/requirements-tools.txt\n"
        "    .venv-tools/bin/python3 setup/make_station_cards.py")

ROOT = Path(__file__).parent.parent
OUT = ROOT / "assets" / "stations"
LOGO = ROOT / "app" / "static" / "logo.png"
LOGO2 = ROOT / "app" / "static" / "logo2.png"   # aiwareness Lab

W, H = 1600, 900          # final card size
S = 2                     # supersampling factor for crisp vector shapes

BG = (13, 17, 23)
BG2 = (22, 27, 39)
TEXT = (230, 237, 243)
MUTED = (139, 148, 158)

EMOJI_FONT = "/System/Library/Fonts/Apple Color Emoji.ttc"
TEXT_FONT = "/System/Library/Fonts/HelveticaNeue.ttc"


# ---------------------------------------------------------------- fonts ----

def _find_face(name_part):
    for idx in range(14):
        try:
            f = ImageFont.truetype(TEXT_FONT, 40, index=idx)
            if name_part.lower() in f.getname()[1].lower():
                return idx
        except Exception:
            break
    return 0


BOLD_IDX = _find_face("bold")
MED_IDX = _find_face("medium")


def font(size, weight="regular"):
    idx = {"bold": BOLD_IDX, "medium": MED_IDX}.get(weight, 0)
    return ImageFont.truetype(TEXT_FONT, size, index=idx)


def emoji(char, size):
    """Render an emoji at its native 160 px strike, then scale."""
    f = ImageFont.truetype(EMOJI_FONT, 160)
    img = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((10, 10), char, font=f, embedded_color=True)
    box = img.getbbox()
    img = img.crop(box) if box else img
    ratio = size / max(img.size)
    return img.resize((max(1, int(img.width * ratio)),
                       max(1, int(img.height * ratio))), Image.LANCZOS)


# ------------------------------------------------------------- helpers -----

def rounded(draw, xy, radius, **kw):
    draw.rounded_rectangle(xy, radius=radius, **kw)


def chip(canvas, draw, x, y, text, fill, fg, size=30, pad=14, lead_emoji=None):
    """Pill chip. Helvetica has no emoji/✓ glyphs — an optional leading
    emoji is pasted as a bitmap instead of set as text."""
    f = font(size * S, "bold")
    tw = draw.textlength(text, font=f)
    esz = int(size * 1.15) * S if lead_emoji else 0
    egap = 10 * S if lead_emoji else 0
    box = [x, y, x + esz + egap + tw + 2 * pad * S, y + (size + 18) * S]
    rounded(draw, box, radius=int((size + 18) * S / 2), fill=fill)
    if lead_emoji:
        paste_emoji(canvas, lead_emoji, size * 1.15,
                    x + pad * S + esz / 2, y + (size + 18) * S / 2)
    draw.text((x + pad * S + esz + egap, y + 8 * S), text, font=f, fill=fg)
    return box


def label_box(canvas, draw, box, text, accent):
    """Detection-style bounding box + label chip, like the real overlay."""
    rounded(draw, box, radius=6 * S, outline=accent, width=3 * S)
    f = font(26 * S, "bold")
    tw = draw.textlength(text, font=f)
    lx, ly = box[0], box[1] - 46 * S
    rounded(draw, [lx, ly, lx + tw + 20 * S, ly + 40 * S], radius=8 * S, fill=accent)
    draw.text((lx + 10 * S, ly + 5 * S), text, font=f, fill=(10, 12, 16))


def paste_emoji(canvas, char, size, cx, cy):
    img = emoji(char, size * S)
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def glow(canvas, cx, cy, radius, rgb, alpha=70):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=rgb + (alpha,))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius / 2)))


# ------------------------------------------------------------- scenes ------
# Each scene draws inside the "screen" rect (sx0, sy0, sx1, sy1) on the
# supersampled canvas. lang is "de" or "en".

def scene_detektiv(cv, d, r, accent, lang):
    x0, y0, x1, y1 = r
    w, h = x1 - x0, y1 - y0
    paste_emoji(cv, "☕", 130, x0 + w * 0.24, y0 + h * 0.62)
    # closed book: the open-book emoji shows readable English microtext,
    # which would leak into the German card
    paste_emoji(cv, "📕", 140, x0 + w * 0.55, y0 + h * 0.68)
    paste_emoji(cv, "🍌", 120, x0 + w * 0.82, y0 + h * 0.55)
    t = {"de": ("Tasse 92%", "Buch 88%", "Banane 76%"),
         "en": ("Cup 92%", "Book 88%", "Banana 76%")}[lang]
    label_box(cv, d, [x0 + w * 0.13, y0 + h * 0.42, x0 + w * 0.36, y0 + h * 0.82], t[0], accent)
    label_box(cv, d, [x0 + w * 0.42, y0 + h * 0.44, x0 + w * 0.68, y0 + h * 0.90], t[1], accent)
    label_box(cv, d, [x0 + w * 0.73, y0 + h * 0.38, x0 + w * 0.92, y0 + h * 0.72], t[2], accent)


def scene_trainer(cv, d, r, accent, lang):
    x0, y0, x1, y1 = r
    w, h = x1 - x0, y1 - y0
    # capture frame + object
    fx0, fy0 = x0 + w * 0.30, y0 + h * 0.22
    fx1, fy1 = x0 + w * 0.70, y0 + h * 0.78
    rounded(d, [fx0, fy0, fx1, fy1], radius=10 * S, outline=(255, 200, 80), width=4 * S)
    for cx, cy in ((fx0, fy0), (fx1, fy0), (fx0, fy1), (fx1, fy1)):
        d.ellipse([cx - 7 * S, cy - 7 * S, cx + 7 * S, cy + 7 * S], fill=(255, 200, 80))
    paste_emoji(cv, "🍎", 150, (fx0 + fx1) / 2, (fy0 + fy1) / 2)
    pred = {"de": "Ich glaube: Apfel (94%)", "en": "I think: apple (94%)"}[lang]
    chip(cv, d, x0 + w * 0.26, y0 + h * 0.05, pred, (36, 44, 36), (155, 232, 155), size=30)
    a = {"de": "Ding A · 6/6", "en": "Thing A · 6/6"}[lang]
    b = {"de": "Ding B · 3/5", "en": "Thing B · 3/5"}[lang]
    chip(cv, d, x0 + w * 0.20, y1 - h * 0.16, a, accent, (12, 10, 18), size=26)
    chip(cv, d, x0 + w * 0.54, y1 - h * 0.16, b, (48, 42, 66), TEXT, size=26)


def scene_schild(cv, d, r, accent, lang):
    x0, y0, x1, y1 = r
    w, h = x1 - x0, y1 - y0
    rng = random.Random(7)
    for i, fx in enumerate((0.30, 0.64)):
        cx, cy = x0 + w * fx, y0 + h * 0.48
        size = 180 if i == 0 else 150
        paste_emoji(cv, "🧑" if i == 0 else "👩", size, cx, cy)
        # pixel mosaic over the eye/nose region only — hair and chin stay
        # visible, so it clearly reads as a *pixelated face*
        px = 13 * S
        bx0, by0 = int(cx - size * S * 0.30), int(cy - size * S * 0.26)
        bx1, by1 = int(cx + size * S * 0.30), int(cy + size * S * 0.16)
        for yy in range(by0, by1, px):
            for xx in range(bx0, bx1, px):
                tone = rng.choice([(198, 164, 138), (172, 140, 118),
                                   (150, 120, 100), (214, 182, 154)])
                d.rectangle([xx, yy, xx + px - S, yy + px - S], fill=tone)
        # accent detection frame around each face, like the real overlay
        rounded(d, [int(cx - size * S * 0.42), int(cy - size * S * 0.45),
                    int(cx + size * S * 0.42), int(cy + size * S * 0.38)],
                radius=8 * S, outline=accent, width=3 * S)
    paste_emoji(cv, "🛡️", 100, x0 + w * 0.87, y0 + h * 0.22)
    t = {"de": "2 Gesichter geschützt", "en": "2 faces protected"}[lang]
    chip(cv, d, x0 + w * 0.26, y1 - h * 0.17, t, accent, (8, 20, 14), size=28)


def scene_spur(cv, d, r, accent, lang):
    x0, y0, x1, y1 = r
    w, h = x1 - x0, y1 - y0
    # faint floor grid for spatial context (same idea as the pose scene)
    for gx in range(int(x0), int(x1), 42 * S):
        d.line([gx, y0, gx, y1], fill=(34, 30, 24), width=S)
    for gy in range(int(y0), int(y1), 42 * S):
        d.line([x0, gy, x1, gy], fill=(34, 30, 24), width=S)
    heat = [(0.28, 0.60, 130, (255, 60, 40)), (0.52, 0.40, 100, (255, 140, 40)),
            (0.72, 0.66, 115, (255, 90, 40)), (0.85, 0.35, 70, (255, 190, 60))]
    for fx, fy, rad, rgb in heat:
        for mult, alpha in ((2.0, 40), (1.4, 70), (0.8, 110)):
            glow(cv, x0 + w * fx, y0 + h * fy, rad * S * mult, rgb, alpha)
    d = ImageDraw.Draw(cv)
    # walking path: dashed line through the points, dots on top
    pts = [(0.15, 0.80), (0.28, 0.62), (0.42, 0.52), (0.52, 0.40),
           (0.63, 0.52), (0.72, 0.64), (0.85, 0.38)]
    coords = [(x0 + w * fx, y0 + h * fy) for fx, fy in pts]
    for (ax, ay), (bx, by) in zip(coords, coords[1:]):
        seg = math.hypot(bx - ax, by - ay)
        steps = max(1, int(seg / (26 * S)))
        for i in range(steps):
            f0, f1 = i / steps, (i + 0.55) / steps
            d.line([(ax + (bx - ax) * f0, ay + (by - ay) * f0),
                    (ax + (bx - ax) * f1, ay + (by - ay) * f1)],
                   fill=(255, 255, 255, 130), width=3 * S)
    for cx, cy in coords:
        d.ellipse([cx - 6 * S, cy - 6 * S, cx + 6 * S, cy + 6 * S],
                  fill=(255, 255, 255, 220))
    t = {"de": "sammelt seit 42 Min …", "en": "collecting for 42 min …"}[lang]
    chip(cv, d, x0 + w * 0.08, y0 + h * 0.06, t, (52, 40, 22), (255, 200, 120), size=28)


def scene_trick(cv, d, r, accent, lang):
    x0, y0, x1, y1 = r
    w, h = x1 - x0, y1 - y0
    paste_emoji(cv, "🧍", 190, x0 + w * 0.32, y0 + h * 0.55)
    paste_emoji(cv, "🍌", 120, x0 + w * 0.72, y0 + h * 0.62)
    t = {"de": ("??? 8%", "Person 91%"), "en": ("??? 8%", "Person 91%")}[lang]
    label_box(cv, d, [x0 + w * 0.20, y0 + h * 0.30, x0 + w * 0.45, y0 + h * 0.88], t[0], accent)
    label_box(cv, d, [x0 + w * 0.62, y0 + h * 0.44, x0 + w * 0.84, y0 + h * 0.80], t[1], accent)


def scene_pose(cv, d, r, accent, lang):
    x0, y0, x1, y1 = r
    w, h = x1 - x0, y1 - y0
    # ghost-mode grid
    for gx in range(int(x0), int(x1), 42 * S):
        d.line([gx, y0, gx, y1], fill=(36, 30, 26), width=S)
    for gy in range(int(y0), int(y1), 42 * S):
        d.line([x0, gy, x1, gy], fill=(36, 30, 26), width=S)
    # skeleton, both hands up
    cx, cy = x0 + w * 0.5, y0 + h * 0.28
    u = h / 10   # feet (ankle at 6.3 u + dot radius) must stay inside the panel
    pts = {
        "head": (cx, cy), "neck": (cx, cy + u), "hip": (cx, cy + 3.4 * u),
        "ls": (cx - u * 0.9, cy + 1.2 * u), "rs": (cx + u * 0.9, cy + 1.2 * u),
        "le": (cx - u * 1.6, cy + 0.4 * u), "re": (cx + u * 1.6, cy + 0.4 * u),
        "lw": (cx - u * 1.9, cy - 0.8 * u), "rw": (cx + u * 1.9, cy - 0.8 * u),
        "lh": (cx - u * 0.5, cy + 3.4 * u), "rh": (cx + u * 0.5, cy + 3.4 * u),
        "lk": (cx - u * 0.7, cy + 4.9 * u), "rk": (cx + u * 0.7, cy + 4.9 * u),
        "la": (cx - u * 0.8, cy + 6.3 * u), "ra": (cx + u * 0.8, cy + 6.3 * u),
    }
    bones = [("neck", "ls"), ("neck", "rs"), ("ls", "le"), ("le", "lw"),
             ("rs", "re"), ("re", "rw"), ("neck", "hip"), ("hip", "lh"),
             ("hip", "rh"), ("lh", "lk"), ("lk", "la"), ("rh", "rk"),
             ("rk", "ra")]
    for a, b in bones:
        d.line([pts[a], pts[b]], fill=accent, width=6 * S)
    for name, (px, py) in pts.items():
        rad = (16 if name == "head" else 8) * S
        if name == "head":
            d.ellipse([px - 26 * S, py - 26 * S, px + 26 * S, py + 26 * S],
                      outline=accent, width=5 * S)
        else:
            d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=accent)
    t = {"de": "Beide Hände hoch!", "en": "Both hands up!"}[lang]
    box = chip(cv, d, x0 + w * 0.08, y0 + h * 0.08, t, (16, 42, 40),
               (140, 240, 230), size=28, lead_emoji="🙌")
    # progress bar under the chip
    bx0, by0 = box[0], box[3] + 12 * S
    bw = (box[2] - box[0])
    rounded(d, [bx0, by0, bx0 + bw, by0 + 12 * S], radius=6 * S, fill=(255, 255, 255, 30))
    rounded(d, [bx0, by0, bx0 + bw * 0.7, by0 + 12 * S], radius=6 * S, fill=accent)


STATIONS = [
    ("detektiv", "🔍", (78, 168, 255), scene_detektiv,
     {"de": ("Objekt-Detektiv", "Was sieht die KI?"),
      "en": ("Object Detective", "What does the AI see?")}),
    ("trainer", "🧠", (181, 123, 255), scene_trainer,
     {"de": ("Trainiere die KI", "Du bist der Coach"),
      "en": ("Train the AI", "You are the coach")}),
    ("schild", "🛡️", (247, 242, 232), scene_schild,
     {"de": ("Privatsphäre-Schild", "Schutz eingebaut"),
      "en": ("Privacy Shield", "Protection built in")}),
    ("spur", "🗺️", (255, 179, 71), scene_spur,
     {"de": ("Die Datenspur", "Was Kameras sammeln"),
      "en": ("The Data Trail", "What cameras collect")}),
    ("trick", "🎭", (255, 93, 143), scene_trick,
     {"de": ("Täusche die KI", "Finde ihre Grenzen"),
      "en": ("Fool the AI", "Find its limits")}),
    ("pose", "🤸", (45, 212, 191), scene_pose,
     {"de": ("Skelett-Spiegel", "Spiel ohne Bild"),
      "en": ("Skeleton Mirror", "Play without pictures")}),
]

LIVE = {"de": "LIVE", "en": "LIVE"}
FOOT = {"de": "aiwarenesslab.io",
        "en": "aiwarenesslab.io"}


# ---------------------------------------------------------------- card -----

# Layout constants shared by the raster renderer and the SVG export, so an
# edited SVG lines up with the exported layer PNGs.
LX = 90 * S                 # left column x
BADGE_Y = 130 * S
BADGE = 190 * S
LOGO_H = 56 * S
LOGO_GAP = 36 * S
LOGO_Y = H * S - 150 * S
TITLE_Y = BADGE_Y + BADGE + 70 * S
TITLE_MAX = 660 * S
TAG_GAP = 18 * S

LAYERS = ("bg", "screen", "icon", "text", "logos")


def title_font(title):
    """Same shrink-to-fit logic for raster and SVG."""
    tf = font(88 * S, "bold")
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while probe.textlength(title, font=tf) > TITLE_MAX:
        tf = font(int(tf.size * 0.93), "bold")
    return tf


def screen_rect():
    cw, ch = W * S, H * S
    return [int(cw * 0.52), int(ch * 0.16), int(cw * 0.945), int(ch * 0.84)]


def logo_images():
    out = []
    for path in (LOGO, LOGO2):
        if path.exists():
            im = Image.open(path).convert("RGBA")
            out.append((path, im.resize(
                (int(im.width * LOGO_H / im.height), LOGO_H), Image.LANCZOS)))
    return out


def render_card(icon, accent, scene, names, lang, layers=LAYERS):
    """Render the card (or a subset of its layers) at full internal
    resolution. Layers not requested stay transparent — that is what the
    editable export uses to hand out separate Photoshop layers."""
    cw, ch = W * S, H * S
    cv = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    title, tag = names[lang]

    if "bg" in layers:
        for y in range(ch):
            f = y / ch
            col = tuple(int(BG[i] + (BG2[i] - BG[i]) * (1 - f)) for i in range(3))
            d.line([(0, y), (cw, y)], fill=col + (255,))
        glow(cv, cw * 0.85, ch * 0.10, 420 * S, accent, 36)
        glow(cv, cw * 0.05, ch * 0.95, 360 * S, accent, 22)
        d = ImageDraw.Draw(cv)
        d.rectangle([0, 0, cw, 14 * S], fill=accent)   # accent top bar

    if "icon" in layers:
        rounded(d, [LX, BADGE_Y, LX + BADGE, BADGE_Y + BADGE], radius=44 * S,
                fill=tuple(int(c * 0.22) for c in accent) + (255,),
                outline=accent, width=4 * S)
        paste_emoji(cv, icon, 120, LX + BADGE / 2, BADGE_Y + BADGE / 2)
        d = ImageDraw.Draw(cv)

    if "text" in layers:
        tf = title_font(title)
        d.text((LX, TITLE_Y), title, font=tf, fill=TEXT)
        d.text((LX, TITLE_Y + tf.size + TAG_GAP), tag,
               font=font(44 * S, "medium"), fill=accent)

    if "logos" in layers:
        fx = LX
        for _path, logo in logo_images():
            cv.alpha_composite(logo, (int(fx), int(LOGO_Y)))
            fx += logo.width + LOGO_GAP
        d = ImageDraw.Draw(cv)

    if "screen" in layers:
        sx0, sy0, sx1, sy1 = screen_rect()
        rounded(d, [sx0 - 6 * S, sy0 - 6 * S, sx1 + 6 * S, sy1 + 6 * S],
                radius=30 * S, fill=(0, 0, 0, 255), outline=(255, 255, 255, 40),
                width=2 * S)
        rounded(d, [sx0, sy0, sx1, sy1], radius=24 * S, fill=(16, 20, 34, 255))
        scene(cv, ImageDraw.Draw(cv), [sx0, sy0, sx1, sy1], accent, lang)
        d = ImageDraw.Draw(cv)
        lf = font(26 * S, "bold")
        lw_ = d.textlength(LIVE[lang], font=lf)
        rounded(d, [sx1 - lw_ - 70 * S, sy0 + 18 * S, sx1 - 18 * S, sy0 + 66 * S],
                radius=24 * S, fill=(0, 0, 0, 170))
        d.ellipse([sx1 - lw_ - 56 * S, sy0 + 32 * S,
                   sx1 - lw_ - 36 * S, sy0 + 52 * S], fill=(248, 81, 73))
        d.text((sx1 - lw_ - 28 * S, sy0 + 26 * S), LIVE[lang], font=lf, fill=TEXT)

    return cv


def make_card(key, icon, accent, scene, names, lang):
    cv = render_card(icon, accent, scene, names, lang)
    return cv.resize((W, H), Image.LANCZOS).convert("RGB")


def make_overview(lang):
    cw, ch = W * S, 620 * S
    cv = Image.new("RGBA", (cw, ch), BG + (255,))
    d = ImageDraw.Draw(cv)
    for y in range(ch):
        f = y / ch
        col = tuple(int(BG[i] + (BG2[i] - BG[i]) * (1 - f)) for i in range(3))
        d.line([(0, y), (cw, y)], fill=col)
    glow(cv, cw * 0.5, 0, 420 * S, (120, 80, 200), 40)
    d = ImageDraw.Draw(cv)

    logos = []
    lh = 62 * S
    for path in (LOGO, LOGO2):
        if path.exists():
            logo = Image.open(path).convert("RGBA")
            logos.append(logo.resize((int(logo.width * lh / logo.height), lh),
                                     Image.LANCZOS))
    gap = 48 * S
    total = sum(l.width for l in logos) + gap * (len(logos) - 1)
    px = (cw - total) // 2
    for logo in logos:
        cv.alpha_composite(logo, (px, 52 * S))
        px += logo.width + gap

    # brand accent top bar ties the banner to the card set
    for x in range(cw):
        f = x / cw
        col = (int(64 + (195 - 64) * f), int(11 + (38 - 11) * f),
               int(103 + (131 - 103) * f))
        d.line([(x, 0), (x, 10 * S)], fill=col)

    title = {"de": "Sechs Stationen. Eine Kamera. Deine Daten.",
             "en": "Six stations. One camera. Your data."}[lang]
    tf = font(58 * S, "bold")
    d.text(((cw - d.textlength(title, font=tf)) / 2, 150 * S), title, font=tf, fill=TEXT)

    n = len(STATIONS)
    cell = cw / n
    for i, (key, icon, accent, _, names) in enumerate(STATIONS):
        cx = cell * i + cell / 2
        by = 280 * S
        badge = 120 * S
        rounded(d, [cx - badge / 2, by, cx + badge / 2, by + badge], radius=30 * S,
                fill=tuple(int(c * 0.22) for c in accent) + (255,),
                outline=accent, width=3 * S)
        paste_emoji(cv, icon, 74, cx, by + badge / 2)
        name = names[lang][0]
        nf = font(26 * S, "bold")
        while d.textlength(name, font=nf) > cell * 0.92:
            nf = font(int(nf.size * 0.92), "bold")
        d.text((cx - d.textlength(name, font=nf) / 2, by + badge + 24 * S),
               name, font=nf, fill=TEXT)
        tag = names[lang][1]
        gf = font(20 * S)
        d.text((cx - d.textlength(tag, font=gf) / 2, by + badge + 62 * S),
               tag, font=gf, fill=MUTED)

    # footer names the exhibit — the banner is used standalone for promotion
    ff = font(22 * S)
    d.text(((cw - d.textlength(FOOT[lang], font=ff)) / 2, 545 * S),
           FOOT[lang], font=ff, fill=MUTED)
    return cv.resize((W, 620), Image.LANCZOS).convert("RGB")


# ------------------------------------------------------- editable export ---

def export_editable():
    """Write per-card source material for Photoshop / Illustrator / PowerPoint:

    <key>_<lang>@2x.png     flattened, 3200x1800 (print-grade raster)
    <key>_<lang>_bg.png     background + glow + accent bar
    <key>_<lang>_screen.png the mock live screen incl. its scene
    <key>_icon.png          icon badge (language-independent)
    logo.png / logo2.png    the two brand logos, untouched
    <key>_<lang>.svg        all of the above stacked, title/tagline as REAL
                            editable text (self-contained, base64-embedded)
    """
    edit = OUT / "editable"
    edit.mkdir(parents=True, exist_ok=True)

    def b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    # brand logos alongside, so a designer has them at hand
    for src, name in ((LOGO, "logo.png"), (LOGO2, "logo2.png")):
        if src.exists():
            (edit / name).write_bytes(src.read_bytes())

    written = 0
    for key, icon, accent, scene, names in STATIONS:
        # icon layer is identical for both languages → render once
        icon_layer = render_card(icon, accent, scene, names, "de", layers=("icon",))
        icon_layer.save(edit / f"{key}_icon.png", optimize=True)
        for lang in ("de", "en"):
            title, tag = names[lang]
            flat = render_card(icon, accent, scene, names, lang)
            flat.convert("RGB").save(edit / f"{key}_{lang}@2x.png", optimize=True)
            bg = render_card(icon, accent, scene, names, lang, layers=("bg",))
            bg.save(edit / f"{key}_{lang}_bg.png", optimize=True)
            sc = render_card(icon, accent, scene, names, lang, layers=("screen",))
            sc.save(edit / f"{key}_{lang}_screen.png", optimize=True)

            # ---- SVG: raster layers + live text ------------------------
            tf = title_font(title)
            asc, _desc = tf.getmetrics()
            t_size = tf.size / S
            t_base = (TITLE_Y + asc) / S                 # PIL top-left → SVG baseline
            gf = font(44 * S, "medium")
            g_asc, _ = gf.getmetrics()
            g_base = (TITLE_Y + tf.size + TAG_GAP + g_asc) / S
            hexc = "#%02x%02x%02x" % accent
            lx = LX / S
            logo_svg, fx = "", LX
            for _p, logo in logo_images():
                logo_svg += (f'\n  <image x="{fx / S:.1f}" y="{LOGO_Y / S:.1f}" '
                             f'width="{logo.width / S:.1f}" '
                             f'height="{logo.height / S:.1f}" '
                             f'href="{b64(logo)}"/>')
                fx += logo.width + LOGO_GAP
            svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- {key} ({lang}) · editable: text below is live text, layers are images.
     Generated by setup/make_station_cards.py — do not hand-edit if you
     plan to re-run the generator. -->
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <g id="background"><image x="0" y="0" width="{W}" height="{H}" href="{b64(bg)}"/></g>
  <g id="screen"><image x="0" y="0" width="{W}" height="{H}" href="{b64(sc)}"/></g>
  <g id="icon"><image x="0" y="0" width="{W}" height="{H}" href="{b64(icon_layer)}"/></g>
  <g id="text" font-family="Helvetica Neue, Helvetica, Arial, sans-serif">
    <text x="{lx:.1f}" y="{t_base:.1f}" font-size="{t_size:.1f}"
          font-weight="700" fill="rgb{TEXT}">{title}</text>
    <text x="{lx:.1f}" y="{g_base:.1f}" font-size="{44 / 1:.1f}"
          font-weight="500" fill="{hexc}">{tag}</text>
  </g>
  <g id="logos">{logo_svg}
  </g>
</svg>
"""
            (edit / f"{key}_{lang}.svg").write_text(svg, encoding="utf-8")
            written += 1
        print(f"  ✓ {key} (de/en): @2x, bg, screen, icon, svg")

    (edit / "README.md").write_text(READ_ME_EDIT, encoding="utf-8")
    print(f"→ {edit.relative_to(ROOT)}: {written} Karten als Ebenen + SVG")


READ_ME_EDIT = """# Editable source material — station cards

Everything here is generated by `setup/make_station_cards.py --editable`.
Re-running overwrites these files, so save your own work under a new name.

## What is what

| File | Contents |
|---|---|
| `<station>_<lang>@2x.png` | the finished card, 3200×1800 (2× print-grade) |
| `<station>_<lang>_bg.png` | background: gradient, accent glow, top bar |
| `<station>_<lang>_screen.png` | the mock "live screen" incl. its scene |
| `<station>_icon.png` | icon badge (same for both languages) |
| `<station>_<lang>.svg` | all layers stacked, **title + tagline as live text** |
| `logo.png`, `logo2.png` | SKILL and aiwareness Lab logos, transparent |

All PNG layers are full-canvas 3200×1800 with transparency, so stacking
them in this order reproduces the card pixel for pixel:

    bg → screen → icon → (your text) → logos

## Photoshop

Open the `.svg` (it comes in as a smart object, text stays vector), or
build a layered document: File → Scripts → *Load Files into Stack…* and
pick `_bg`, `_screen`, `_icon` — then set the text yourself in
Helvetica Neue Bold (title) / Medium (tagline).

## Illustrator / Affinity / Inkscape

Open the `.svg`. Groups are named `background`, `screen`, `icon`, `text`,
`logos`; the two `<text>` elements are editable type.

## PowerPoint / Keynote / Google Slides

Use `station_cards.pptx` in this folder — one editable slide per card,
with real text boxes. Alternatively insert the `.svg` and use
*Graphics Format → Convert to Shape* to make it editable.

## Fonts & colours

Type: Helvetica Neue (Bold for titles, Medium for taglines).
Brand colours: `#400b67`, `#c32683`. Card background `#0d1117` → `#161b27`.
Station accents: see the `STATIONS` list in `setup/make_station_cards.py`.
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for lang in ("de", "en"):
        for key, icon, accent, scene, names in STATIONS:
            img = make_card(key, icon, accent, scene, names, lang)
            path = OUT / f"{key}_{lang}.png"
            img.save(path, optimize=True)
            files.append(path)
            print("✓", path.relative_to(ROOT))
        ov = make_overview(lang)
        ov.save(OUT / f"overview_{lang}.png", optimize=True)
        print("✓", (OUT / f"overview_{lang}.png").relative_to(ROOT))

        # contact sheet for quick review
        cols, rows = 2, 3
        tw, th = W // 2, H // 2
        sheet = Image.new("RGB", (cols * tw + 30, rows * th + 40), (30, 34, 44))
        for i, (key, *_rest) in enumerate(STATIONS):
            img = Image.open(OUT / f"{key}_{lang}.png").resize((tw, th))
            sheet.paste(img, ((i % cols) * (tw + 10) + 10, (i // cols) * (th + 10) + 10))
        sheet.save(OUT / f"contact_{lang}.png")
        print("✓", (OUT / f"contact_{lang}.png").relative_to(ROOT))


if __name__ == "__main__":
    main()
    if "--editable" in sys.argv:
        print("\nEditierbare Vorlagen (Ebenen-PNGs + SVG):")
        export_editable()
