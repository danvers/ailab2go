#!/usr/bin/env python3
"""Generate the printable A4 event poster with QR codes.

    python3 setup/make_poster.py
    → setup/poster.html  (open in a browser, print on A4, done)

Keep SSID/PASSWORD in sync with setup/hotspot.sh.

Layout note: the page is one flex column at exactly A4 size with
`justify-content: space-between`, so the free space is distributed between
the blocks instead of piling up at the bottom. Everything is sized in mm —
what you see is what the printer puts on the sheet.
"""

import base64
import io
import sys
from pathlib import Path

SSID = "KI-Werkstatt"
PASSWORD = "lernen-mit-ki"
URL = "http://10.42.0.1"
TITLE = "KI-Werkstatt"

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


wifi_qr = qr_data_uri(f"WIFI:T:WPA;S:{SSID};P:{PASSWORD};;")
url_qr = qr_data_uri(URL)

# The poster must stay a single self-contained file → embed the logos.
def _data_uri(path):
    return ("data:image/png;base64," +
            base64.b64encode(path.read_bytes()).decode()) \
        if path.exists() else ""

_static = Path(__file__).parent.parent / "app" / "static"
logo_uri = _data_uri(_static / "logo.png")        # SKILL
logo2_uri = _data_uri(_static / "logo2.png")      # aiwareness Lab

STATIONS = [
    ("🔍", "Objekt-Detektiv", "Was sieht die KI?", "#2f6fe0"),
    ("🧠", "Trainiere die KI", "Du bist der Coach", "#8a4fd8"),
    ("🛡️", "Privatsphäre-Schild", "Schutz eingebaut", "#1fa877"),
    ("🗺️", "Die Datenspur", "Was Kameras sammeln", "#d98211"),
    ("🎭", "Täusche die KI", "Finde ihre Grenzen", "#d81b60"),
    ("🤸", "Skelett-Spiegel", "Spiel ohne Bild", "#0f9b96"),
]

station_cards = "\n".join(
    f'<div class="st" style="--c:{color}"><span class="ic">{icon}</span>'
    f'<strong>{name}</strong><em>{teaser}</em></div>'
    for icon, name, teaser, color in STATIONS
)

html = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><title>{TITLE} · Poster</title>
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
    padding: 15mm 15mm 11mm;
    display: flex; flex-direction: column; justify-content: space-between;
  }}
  @media print {{ body {{ padding: 0; background: #fff; }} }}
  @media screen {{ .page {{ box-shadow: 0 10px 40px rgba(20,26,51,.25);
                           border-radius: 6px; }} }}

  /* ── header: logo row on top, full-size title beneath ───────────── */
  header {{ display: flex; flex-direction: column; align-items: center;
            gap: 4mm; }}
  .logos {{ display: flex; align-items: center; gap: 6mm; }}
  .brandmark {{ height: 12mm; width: auto; }}
  .rule {{ width: 0.5mm; height: 10mm; background: #c9d0e2; border-radius: 1mm; }}
  h1 {{ font-size: 11mm; line-height: 1; letter-spacing: 0.3mm;
        background: linear-gradient(90deg, #400b67, #c32683);
        -webkit-background-clip: text; background-clip: text; color: transparent; }}

  .hook {{ text-align: center; font-size: 5.4mm; line-height: 1.5;
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

  footer {{ text-align: center; color: #8a92ab; font-size: 3.4mm; }}
</style></head><body>
<div class="page">

  <header>
    <div class="logos">
      <img class="brandmark" src="{logo_uri}" alt="SKILL">
      <span class="rule"></span>
      <img class="brandmark" src="{logo2_uri}" alt="aiwareness Lab">
    </div>
    <h1>{TITLE}</h1>
  </header>

  <p class="hook">Trainiere eine echte KI, tricks sie aus —<br>
    und finde heraus, <em>was Kameras wirklich über dich wissen</em>.</p>

  <div class="steps">
    <div class="step">
      <span class="badge">1️⃣ &nbsp;WLAN verbinden</span>
      <img src="{wifi_qr}" alt="WLAN-QR-Code">
      <div class="cred">Netz: <code>{SSID}</code><br>Passwort: <code>{PASSWORD}</code>
        <span class="fine">„Kein Internet“? Trotzdem verbinden!</span></div>
    </div>
    <div class="arrow">➜</div>
    <div class="step">
      <span class="badge">2️⃣ &nbsp;Seite öffnen</span>
      <img src="{url_qr}" alt="Adress-QR-Code">
      <div class="cred">oder eintippen:<br><code>{URL}</code>
        <span class="fine">http — ohne „s“, ohne www</span></div>
    </div>
  </div>

  <p class="phone-hint">📱 Dein Handy genügt — keine App, keine Anmeldung.</p>

  <div>
    <h2>Sechs Stationen warten auf dich</h2>
    <div class="stations">{station_cards}</div>
  </div>

  <div class="privacy">
    <strong>🔒 Unser Versprechen</strong>
    <p>Alles läuft auf einem Raspberry&nbsp;Pi hier im Raum. Keine Cloud, kein
    Internet, keine gespeicherten Fotos — und alles, was du der KI beibringst,
    kannst du selbst wieder löschen.</p>
  </div>

  <footer>Raspberry Pi 5 + KI-Chip · Open Source (MIT) · Fragen? Sprich uns an!<br>
    © Dan Verständig · medienbildung.team</footer>
</div>
</body></html>
"""

out = Path(__file__).parent / "poster.html"
out.write_text(html, encoding="utf-8")
print(f"Poster written to {out} — open it in a browser and print (A4).")
