#!/usr/bin/env python3
"""Generate the printable A4 event posters with QR codes — DE and EN.

    python3 setup/make_poster.py
    → setup/poster_de.html   (title: KI-Werkstatt)
    → setup/poster_en.html   (title: AI-Lab2Go)

Open in a browser and print on A4. Keep SSID/PASSWORD in sync with
setup/hotspot.sh — the QR code encodes them, so a mismatch means visitors
cannot join.

Layout note: the page is one flex column at exactly A4 size with
`justify-content: space-between`, so free space is distributed between the
blocks instead of piling up at the bottom. Everything is sized in mm — what
you see is what the printer puts on the sheet.
"""

import base64
import io
import sys
from pathlib import Path

# --- event data (identical on both posters — these are facts, not copy) ----
SSID = "KI-Werkstatt"
PASSWORD = "lernen-mit-ki"
URL = "http://10.42.0.1"

try:
    import qrcode
except ImportError:
    sys.exit("Missing dependency: sudo apt install python3-qrcode python3-pil")


def qr_data_uri(payload: str) -> str:
    qr = qrcode.QRCode(box_size=12, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(payload)
    img = qr.make_image(fill_color="#141a33", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _data_uri(path: Path) -> str:
    return ("data:image/png;base64," +
            base64.b64encode(path.read_bytes()).decode()) if path.exists() else ""


wifi_qr = qr_data_uri(f"WIFI:T:WPA;S:{SSID};P:{PASSWORD};;")
url_qr = qr_data_uri(URL)

# The posters must stay single self-contained files → embed the logos.
_static = Path(__file__).parent.parent / "app" / "static"
logo_uri = _data_uri(_static / "logo.png")        # SKILL
logo2_uri = _data_uri(_static / "logo2.png")      # aiwareness Lab

ACCENTS = ["#2f6fe0", "#8a4fd8", "#1fa877", "#d98211", "#d81b60", "#0f9b96"]
ICONS = ["🔍", "🧠", "🛡️", "🗺️", "🎭", "🤸"]

STRINGS = {
    "de": {
        "lang": "de",
        "title": "KI-Werkstatt",
        "hook": "Trainiere eine echte KI, tricks sie aus —<br>und finde heraus, "
                "<em>was Kameras wirklich über dich wissen</em>.",
        "badge1": "1️⃣ &nbsp;WLAN verbinden",
        "badge2": "2️⃣ &nbsp;Seite öffnen",
        "net": "Netz:",
        "pass": "Passwort:",
        "or_type": "oder eintippen:",
        "fine1": "„Kein Internet“? Trotzdem verbinden!",
        "fine2": "http — ohne „s“, ohne www",
        "phone": "📱 Dein Handy genügt — keine App, keine Anmeldung.",
        "stations_head": "Sechs Stationen warten auf dich",
        "stations": [
            ("Objekt-Detektiv", "Was sieht die KI?"),
            ("Trainiere die KI", "Du bist der Coach"),
            ("Privatsphäre-Schild", "Schutz eingebaut"),
            ("Die Datenspur", "Was Kameras sammeln"),
            ("Täusche die KI", "Finde ihre Grenzen"),
            ("Skelett-Spiegel", "Spiel ohne Bild"),
        ],
        "promise_head": "🔒 Unser Versprechen",
        "promise": "Alles läuft auf einem Raspberry&nbsp;Pi hier im Raum. Keine "
                   "Cloud, kein Internet, keine gespeicherten Fotos — und alles, "
                   "was du der KI beibringst, kannst du selbst wieder löschen.",
        "footer": "Raspberry Pi 5 + KI-Chip · Open Source (MIT) · Fragen? "
                  "Sprich uns an!<br>© Dan Verständig · aiwarenesslab.io",
    },
    "en": {
        "lang": "en",
        "title": "AI-Lab2Go",
        "hook": "Train a real AI, trick it —<br>and find out "
                "<em>what cameras really know about you</em>.",
        "badge1": "1️⃣ &nbsp;Join the Wi-Fi",
        "badge2": "2️⃣ &nbsp;Open the page",
        "net": "Network:",
        "pass": "Password:",
        "or_type": "or type in:",
        "fine1": "“No internet” warning? Connect anyway!",
        "fine2": "http — no “s”, no www",
        "phone": "📱 Your phone is all you need — no app, no sign-up.",
        "stations_head": "Six stations are waiting for you",
        "stations": [
            ("Object Detective", "What does the AI see?"),
            ("Train the AI", "You are the coach"),
            ("Privacy Shield", "Protection built in"),
            ("The Data Trail", "What cameras collect"),
            ("Fool the AI", "Find its limits"),
            ("Skeleton Mirror", "Play without pictures"),
        ],
        "promise_head": "🔒 Our promise",
        "promise": "Everything runs on a Raspberry&nbsp;Pi here in this room. No "
                   "cloud, no internet, no stored photos — and everything you "
                   "teach the AI, you can delete yourself.",
        "footer": "Raspberry Pi 5 + AI chip · open source (MIT) · Questions? "
                  "Just ask us!<br>© Dan Verständig · aiwarenesslab.io",
    },
}


def build(s: dict) -> str:
    station_cards = "\n".join(
        f'<div class="st" style="--c:{ACCENTS[i]}"><span class="ic">{ICONS[i]}</span>'
        f'<strong>{name}</strong><em>{teaser}</em></div>'
        for i, (name, teaser) in enumerate(s["stations"]))

    return f"""<!DOCTYPE html>
<html lang="{s['lang']}"><head><meta charset="utf-8">
<title>{s['title']} · Poster</title>
<style>
  @page {{ size: A4 portrait; margin: 0; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0;
      -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  html, body {{ background: #e8ecf5; }}
  body {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
          display: flex; justify-content: center; padding: 10px; }}

  .page {{
    width: 210mm; height: 297mm; overflow: hidden;
    background:
      radial-gradient(95mm 70mm at 108% -8%, rgba(195,38,131,.13), transparent 70%),
      radial-gradient(85mm 65mm at -8% 26%, rgba(64,11,103,.11), transparent 70%),
      radial-gradient(85mm 60mm at 50% 110%, rgba(31,168,119,.13), transparent 70%),
      #fdfdfd;
    color: #141a33;
    padding: 9mm 15mm 11mm;      /* small top padding → logos sit high */
    display: flex; flex-direction: column; justify-content: space-between;
  }}
  @media print {{ body {{ padding: 0; background: #fff; }} }}
  @media screen {{ .page {{ box-shadow: 0 10px 40px rgba(20,26,51,.25);
                           border-radius: 6px; }} }}

  /* ── header: small logo row up top, title beneath ────────────────── */
  header {{ display: flex; flex-direction: column; align-items: center;
            gap: 5mm; }}
  .logos {{ display: flex; align-items: center; gap: 5mm; }}
  .brandmark {{ height: 8mm; width: auto; }}
  .rule {{ width: 0.4mm; height: 7mm; background: #c9d0e2; border-radius: 1mm; }}
  .title {{ font-size: 13mm; line-height: 1; letter-spacing: 0.3mm;
            font-weight: 800;
            background: linear-gradient(90deg, #400b67, #c32683);
            -webkit-background-clip: text; background-clip: text;
            color: transparent; }}

  .hook {{ text-align: center; font-size: 5mm; line-height: 1.5;
           font-weight: 600; max-width: 155mm; margin: 0 auto; }}
  .hook em {{ font-style: normal;
              box-shadow: inset 0 -1.1mm 0 rgba(255,214,102,.85); }}

  /* ── QR steps ───────────────────────────────────────────────────── */
  .steps {{ display: flex; gap: 7mm; align-items: stretch;
            justify-content: center; }}
  .step {{
    flex: 1 1 0; max-width: 76mm;
    background: #fff; border: 0.6mm solid #141a33; border-radius: 6mm;
    padding: 7mm 5mm 5mm; text-align: center; position: relative;
    box-shadow: 1.6mm 1.6mm 0 rgba(20,26,51,.10);
  }}
  .badge {{
    position: absolute; top: -4.4mm; left: 50%; transform: translateX(-50%);
    background: #141a33; color: #fff; border-radius: 99mm;
    padding: 1.5mm 5mm; font-weight: 800; font-size: 4mm; white-space: nowrap;
  }}
  .step img {{ width: 47mm; height: 47mm; display: block; margin: 1mm auto 3mm; }}
  .cred {{ font-size: 4.1mm; line-height: 1.65; }}
  .cred code {{
    font-family: ui-monospace, Menlo, monospace; background: #eef1f8;
    border: 0.3mm solid #c9d0e2; border-radius: 1.6mm; padding: 0.3mm 2mm;
    font-weight: 700; font-size: 4mm; white-space: nowrap;
  }}
  .fine {{ display: block; margin-top: 1.6mm; font-size: 3.4mm;
           color: #5a6382; line-height: 1.4; }}
  .arrow {{ align-self: center; font-size: 9mm; color: #8a92ab; }}
  .phone-hint {{ text-align: center; color: #5a6382; font-size: 4mm; }}

  /* ── stations: 3 x 2 instead of 6 in a cramped row ──────────────── */
  h2 {{ text-align: center; font-size: 5.6mm; letter-spacing: 0.4mm;
        margin-bottom: 4mm; }}
  .stations {{ display: grid; grid-template-columns: repeat(3, 1fr);
               gap: 4mm; }}
  .st {{
    background: #fff; border: 0.4mm solid #dbe0ee; border-top: 2mm solid var(--c);
    border-radius: 4mm; padding: 3.5mm 2mm 4mm; text-align: center;
    display: flex; flex-direction: column; gap: 1.4mm; align-items: center;
  }}
  .st .ic {{ font-size: 8.5mm; line-height: 1; }}
  .st strong {{ font-size: 4mm; }}
  .st em {{ font-style: normal; color: #5a6382; font-size: 3.4mm; }}

  /* ── promise ────────────────────────────────────────────────────── */
  .privacy {{
    border: 0.8mm dashed #1fa877; border-radius: 5mm;
    background: rgba(31,168,119,.09);
    padding: 5mm 7mm; text-align: center; color: #0e6b47;
  }}
  .privacy strong {{ font-size: 5mm; display: block; margin-bottom: 1.8mm; }}
  .privacy p {{ font-size: 4.1mm; line-height: 1.55; max-width: 150mm;
                margin: 0 auto; }}

  footer {{ text-align: center; color: #8a92ab; font-size: 3.4mm;
            line-height: 1.5; }}
</style></head><body>
<div class="page">

  <header>
    <div class="logos">
      <img class="brandmark" src="{logo_uri}" alt="SKILL">
      <span class="rule"></span>
      <img class="brandmark" src="{logo2_uri}" alt="aiwareness Lab">
    </div>
    <div class="title">{s['title']}</div>
  </header>

  <p class="hook">{s['hook']}</p>

  <div class="steps">
    <div class="step">
      <span class="badge">{s['badge1']}</span>
      <img src="{wifi_qr}" alt="Wi-Fi QR code">
      <div class="cred">{s['net']} <code>{SSID}</code><br>{s['pass']} <code>{PASSWORD}</code>
        <span class="fine">{s['fine1']}</span></div>
    </div>
    <div class="arrow">➜</div>
    <div class="step">
      <span class="badge">{s['badge2']}</span>
      <img src="{url_qr}" alt="Address QR code">
      <div class="cred">{s['or_type']}<br><code>{URL}</code>
        <span class="fine">{s['fine2']}</span></div>
    </div>
  </div>

  <p class="phone-hint">{s['phone']}</p>

  <div>
    <h2>{s['stations_head']}</h2>
    <div class="stations">{station_cards}</div>
  </div>

  <div class="privacy">
    <strong>{s['promise_head']}</strong>
    <p>{s['promise']}</p>
  </div>

  <footer>{s['footer']}</footer>
</div>
</body></html>
"""


def main():
    here = Path(__file__).parent
    for lang, s in STRINGS.items():
        out = here / f"poster_{lang}.html"
        out.write_text(build(s), encoding="utf-8")
        print(f"✓ {out.name} — “{s['title']}” (open in a browser, print A4)")


if __name__ == "__main__":
    main()
