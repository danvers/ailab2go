#!/usr/bin/env python3
"""Editable export of the A6 card deck — called by make_cards.py --editable.

Writes to assets/cards/editable/:
    cards_<lang>.pptx   24 slides at A6 landscape, front/back alternating.
                        Every text is a real, editable text box; the glitch
                        background is an image, everything else is native.
    front_<n>.png       front backgrounds (glow + scanlines + noise bars),
                        one per card, language-independent
    icon_<n>.png        the emoji icon, transparent
    README.md           what to open where

Needs pillow (background rendering) and python-pptx. Both are in
dev/requirements-tools.txt.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = ROOT / "assets" / "cards" / "editable"

MM_PER_IN = 25.4
DPI = 300                      # raster resolution for the background layers


def mm2in(mm):
    return mm / MM_PER_IN


def mm2px(mm):
    return int(round(mm / MM_PER_IN * DPI))


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def render_front_bg(color, L, path):
    """Dark card background: vertical gradient, two accent glows, scanlines,
    noise bars, accent top bar — the parts a PowerPoint shape cannot do."""
    from PIL import Image, ImageDraw, ImageFilter

    W, H = mm2px(L["w"]), mm2px(L["h"])
    accent = hex2rgb(color)
    bg, bg2 = (13, 17, 23), (22, 27, 39)

    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    for y in range(H):
        f = y / H
        d.line([(0, y), (W, y)],
               fill=tuple(int(bg[i] + (bg2[i] - bg[i]) * (1 - f)) for i in range(3)))

    def glow(cx, cy, rx, ry, alpha):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                                      fill=accent + (alpha,))
        layer = layer.filter(ImageFilter.GaussianBlur(rx / 2))
        im.paste(Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB"))

    glow(W * 0.78, H * 0.12, mm2px(42), mm2px(28), 108)
    glow(W * 0.12, H * 0.92, mm2px(38), mm2px(28), 66)

    d = ImageDraw.Draw(im, "RGBA")
    # noise bars (same positions as the HTML deck)
    bars = [(0.20, 0.00, 0.36, 1.1, accent, 128),
            (0.33, 0.76, 0.24, 0.7, (41, 231, 255), 115),
            (0.70, 0.07, 0.28, 1.5, (255, 46, 138), 97),
            (0.82, 0.80, 0.16, 1.1, accent, 128)]
    for ty, tx, tw, th, rgb, a in bars:
        x0 = int(W * tx)
        d.rectangle([x0, int(H * ty), x0 + int(W * tw),
                     int(H * ty) + mm2px(th)], fill=rgb + (a,))
    # scanlines
    step = mm2px(0.95)
    for y in range(0, H, max(2, step)):
        d.rectangle([0, y, W, y + max(1, mm2px(0.3))], fill=(255, 255, 255, 14))
    # accent top bar
    d.rectangle([0, 0, W, mm2px(L["bar"])], fill=accent + (255,))

    im.save(path, optimize=True)


def render_icon(char, size_mm, path):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", 160)
    tmp = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((10, 10), char, font=f, embedded_color=True)
    box = tmp.getbbox()
    tmp = tmp.crop(box) if box else tmp
    side = mm2px(size_mm)
    ratio = side / max(tmp.size)
    tmp = tmp.resize((max(1, int(tmp.width * ratio)),
                      max(1, int(tmp.height * ratio))), Image.LANCZOS)
    tmp.save(path, optimize=True)


def run(langs=("de", "en")):
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt, Emu
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
        from pptx.enum.shapes import MSO_SHAPE
    except ImportError:
        sys.exit("Missing dependency: python-pptx\n"
                 "    bash setup/tools.sh cards --editable\n"
                 "  or: .venv-tools/bin/pip install -r dev/requirements-tools.txt")

    import make_cards as mc

    OUT.mkdir(parents=True, exist_ok=True)
    L = mc.L
    logo_files = [ROOT / "app" / "static" / "logo.png",
                  ROOT / "app" / "static" / "logo2.png"]

    # ---- shared raster layers (language-independent) ----------------------
    cards_meta = []
    for i in range(6):
        cards_meta.append(dict(kind="station", idx=i,
                               color=mc.ACCENT_STATION[i], icon=mc.ICONS_STATION[i]))
    for i in range(6):
        cards_meta.append(dict(kind="discuss", idx=i,
                               color=mc.ACCENT_DISCUSS[i], icon=mc.ICONS_DISCUSS[i]))
    for n, m in enumerate(cards_meta, 1):
        m["bg"] = OUT / f"front_{n:02d}.png"
        m["ic"] = OUT / f"icon_{n:02d}.png"
        if not m["bg"].exists():
            render_front_bg(m["color"], L, m["bg"])
        if not m["ic"].exists():
            render_icon(m["icon"], L["icon"] - 3, m["ic"])
    print(f"  ✓ {len(cards_meta)} Hintergründe + Icons (300 dpi)")

    DARK = RGBColor(0x0D, 0x11, 0x17)
    LIGHT = RGBColor(0xFD, 0xFD, 0xFD)
    INK = RGBColor(0x14, 0x1A, 0x33)
    TEXT = RGBColor(0xE6, 0xED, 0xF3)
    MUTED = RGBColor(0x8A, 0x92, 0xAB)
    FONT = "Helvetica Neue"

    def strip(html):
        """The PPTX carries plain text — inline <em>/<strong> would show up
        as literal tags in a text box."""
        import re
        return re.sub(r"<[^>]+>", "", html)

    def textbox(slide, x, y, w, h, text, size, *, color=INK, bold=False,
                align=PP_ALIGN.LEFT, spacing=1.0, caps=False, letter=None):
        tb = slide.shapes.add_textbox(Inches(mm2in(x)), Inches(mm2in(y)),
                                      Inches(mm2in(w)), Inches(mm2in(h)))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text.upper() if caps else text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.name = FONT
        run.font.color.rgb = color
        p.line_spacing = spacing
        return tb

    def rect(slide, x, y, w, h, fill, *, shape=MSO_SHAPE.RECTANGLE, line=None):
        sh = slide.shapes.add_shape(shape, Inches(mm2in(x)), Inches(mm2in(y)),
                                    Inches(mm2in(w)), Inches(mm2in(h)))
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
        if line is None:
            sh.line.fill.background()
        else:
            sh.line.color.rgb = line
        sh.shadow.inherit = False
        return sh

    mm2pt = 72 / MM_PER_IN

    for lang in langs:
        stations, discussion = mc.load_content(lang)
        if stations is None:
            continue
        u = mc.UI[lang]
        prs = Presentation()
        prs.slide_width = Inches(mm2in(L["w"]))
        prs.slide_height = Inches(mm2in(L["h"]))
        blank = prs.slide_layouts[6]

        items = ([("station", i, s) for i, s in enumerate(stations)] +
                 [("discuss", i, c) for i, c in enumerate(discussion)])

        for n, (kind, i, item) in enumerate(items, 1):
            m = cards_meta[n - 1]
            accent = RGBColor(*hex2rgb(m["color"]))
            kicker = (f"{u['station']} {i + 1} {u['of']} 6" if kind == "station"
                      else f"{u['discuss']} {i + 1} {u['of']} 6")

            # ---------- FRONT ----------
            s1 = prs.slides.add_slide(blank)
            s1.shapes.add_picture(str(m["bg"]), 0, 0,
                                  width=prs.slide_width, height=prs.slide_height)
            textbox(s1, L["pad_x"], 20, L["w"] - 2 * L["pad_x"], 6,
                    kicker, L["kicker"] * mm2pt, color=accent, bold=True,
                    align=PP_ALIGN.CENTER, caps=True)
            icon_w = mm2in(L["icon"] - 3)
            s1.shapes.add_picture(str(m["ic"]),
                                  Inches(mm2in(L["w"] / 2) - icon_w / 2),
                                  Inches(mm2in(28)), height=Inches(icon_w))
            title = item["title"]
            t_size = (L["title_long"] if len(title) > 16 else L["title"]) * mm2pt
            textbox(s1, L["pad_x"], 56, L["w"] - 2 * L["pad_x"], 12,
                    title, t_size, color=TEXT, bold=True, align=PP_ALIGN.CENTER)
            tag = item.get("tag") or u["subtitle"]
            textbox(s1, L["pad_x"], 70, L["w"] - 2 * L["pad_x"], 6,
                    tag, L["tag"] * mm2pt, color=accent, bold=True,
                    align=PP_ALIGN.CENTER)
            # logos, centred as a pair
            from PIL import Image as PImage
            widths = []
            for lf in logo_files:
                with PImage.open(lf) as im:
                    widths.append(L["logo_h"] * im.width / im.height)
            total = sum(widths) + L["logo_gap"]
            lx = (L["w"] - total) / 2
            for lf, wmm in zip(logo_files, widths):
                s1.shapes.add_picture(str(lf), Inches(mm2in(lx)),
                                      Inches(mm2in(L["logo_y"])),
                                      height=Inches(mm2in(L["logo_h"])))
                lx += wmm + L["logo_gap"]
            s1.notes_slide.notes_text_frame.text = (
                f"{title} — front ({lang.upper()})\n"
                f"Background image: {m['bg'].name} (300 dpi, includes glow, "
                f"scanlines, glitch bars, accent bar).\n"
                f"Kicker, title, tagline are editable text boxes. "
                f"Accent {m['color']}. Type: {FONT}.")

            # ---------- BACK ----------
            s2 = prs.slides.add_slide(blank)
            bgs = rect(s2, 0, 0, L["w"], L["h"], LIGHT)
            bgs.shadow.inherit = False
            rect(s2, 0, 0, L["w"], L["bar"], accent)
            y = L["pad_top"]
            textbox(s2, L["pad_x"], y, 40, 4, kicker, L["back_kicker"] * mm2pt,
                    color=accent, bold=True, caps=True)
            textbox(s2, L["pad_x"] + 34, y - 0.8, L["w"] - 2 * L["pad_x"] - 34, 6,
                    title, L["back_title"] * mm2pt, color=INK, bold=True)
            y += 7
            body_pt = L["body"] * mm2pt

            def block(y, head, lines, tint=None):
                if tint is not None:
                    pass  # tinted panel drawn by caller
                textbox(s2, L["pad_x"], y, L["w"] - 2 * L["pad_x"], 4,
                        head, L["h4"] * mm2pt, color=accent, bold=True, caps=True)
                yy = y + 3.6
                for ln in lines:
                    h = 3.6 + 3.6 * (len(ln) // 62)
                    textbox(s2, L["pad_x"], yy, L["w"] - 2 * L["pad_x"], h,
                            strip(ln), body_pt, color=INK, spacing=1.15)
                    yy += h + 0.6
                return yy

            if kind == "station":
                steps = [f"{k + 1}. {t}" for k, t in enumerate(item["steps"])]
                y = block(y, u["try_"], steps) + 1.2
                y = block(y, u["rally"], [item["rally"]]) + 1.2
                y = block(y, u["think"], [item["think"]])
            else:
                for ln in [item["scenario"]]:
                    h = 3.8 + 3.8 * (len(ln) // 62)
                    textbox(s2, L["pad_x"], y, L["w"] - 2 * L["pad_x"], h,
                            strip(ln), body_pt, color=INK, spacing=1.15)
                    y += h + 1.6
                y = block(y, u["ask"], [item["ask"]]) + 1.4
                textbox(s2, L["pad_x"], y, L["w"] - 2 * L["pad_x"], 8,
                        strip(u["note"]), L["note"] * mm2pt, color=MUTED,
                        spacing=1.15)

            # footer: logos + domain
            fy = L["h"] - L["pad_bot"] - 4
            lx = L["pad_x"]
            for lf, wmm in zip(logo_files, widths):
                s2.shapes.add_picture(str(lf), Inches(mm2in(lx)), Inches(mm2in(fy)),
                                      height=Inches(mm2in(4)))
                lx += wmm * 0.8 + 3
            textbox(s2, L["w"] - L["pad_x"] - 30, fy + 0.6, 30, 4,
                    "aiwarenesslab.io", L["foot"] * mm2pt, color=MUTED,
                    align=PP_ALIGN.RIGHT)
            s2.notes_slide.notes_text_frame.text = (
                f"{title} — back ({lang.upper()})\n"
                "Everything here is native PowerPoint: text boxes, the accent "
                "bar and the background rectangle. Edit freely.")

        path = OUT / f"cards_{lang}.pptx"
        prs.save(str(path))
        print(f"  ✓ {path.name} — {len(prs.slides.__iter__.__self__._sldIdLst)} "
              f"Folien A6 ({lang.upper()})")

    (OUT / "README.md").write_text(READ_ME, encoding="utf-8")
    print(f"→ {OUT.relative_to(ROOT)}")


READ_ME = """# Editable A6 card deck

Generated by `bash setup/tools.sh cards --editable`. Re-running overwrites
these files — save your own edits under a new name.

| File | What it is |
|---|---|
| `cards_de.pptx`, `cards_en.pptx` | 24 slides each at **A6 landscape (148 × 105 mm)**, front/back alternating. All text is editable; the accent bars and panels are native shapes. |
| `front_NN.png` | front background per card, 300 dpi — carries the glitch look (glow, scanlines, colour bars, accent bar) that PowerPoint shapes cannot draw |
| `icon_NN.png` | the emoji icon, transparent |

Card order in both decks: stations 1–6, then discussion cards 1–6.

## PowerPoint / Keynote / Google Slides

Open the `.pptx`. The slide size is already A6 landscape, so *File → Print*
gives print-ready cards — for double-sided output choose **flip on the short
edge**, otherwise the backs come out upside down.

## Photoshop / Illustrator / Affinity

Use `front_NN.png` as the background layer and set your own type on top
(Helvetica Neue, Bold for the title). Brand colours `#400b67` / `#c32683`;
each card's accent colour is in the slide notes of the matching PowerPoint
slide.

For a vector version of the whole card, open `setup/cards_de.html` (or
`_en`) in a browser and print to PDF — the PDF keeps the text as editable
vector type.
"""


if __name__ == "__main__":
    run()
