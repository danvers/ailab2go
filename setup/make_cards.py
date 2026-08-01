#!/usr/bin/env python3
"""Generate the printable A6 postcard deck (station + discussion cards).

    bash setup/tools.sh cards                # or:
    python3 setup/make_cards.py              # → setup/cards_de.html
                                             #   setup/cards_en.html
    python3 setup/make_cards.py --editable   # + editable PowerPoint + layers

Format: DIN A6 landscape (148 × 105 mm) — classic postcard size.
Each card is two pages: front (dark, glitch look, both logos) and back
(light, the actual text).

Printing
  Double-sided on A6, **flip on the SHORT edge** — landscape pages come out
  upside down with the usual long-edge setting.
  On A4: "4 pages per sheet" and cut twice.

German content lives in this file; the English content is loaded from
setup/cards_en.json (same structure), so translators can work on the JSON
without touching code.
"""

import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
_static = ROOT / "app" / "static"


def _data_uri(path: Path) -> str:
    return ("data:image/png;base64," +
            base64.b64encode(path.read_bytes()).decode()) if path.exists() else ""


LOGO = _data_uri(_static / "logo.png")     # SKILL
LOGO2 = _data_uri(_static / "logo2.png")   # aiwareness Lab

# ── layout (mm) — shared by the HTML and the PowerPoint export ────────────
L = dict(
    w=148, h=105,                 # A6 landscape
    pad_x=8, pad_top=7, pad_bot=5.5,
    bar=2,                        # accent top bar
    kicker=2.6, icon=19,
    title=8, title_long=6.4, tag=3.6,
    logo_h=5, logo_gap=4.5, logo_y=93,
    back_title=4.8, back_kicker=2.5,
    body=3.05, h4=2.9, note=2.5, foot=2.3,
)

ACCENT_STATION = ["#4ea8ff", "#b57bff", "#3ddc97", "#ffb347", "#ff5d8f", "#2dd4bf"]
ACCENT_DISCUSS = ["#8a4fd8", "#c32683", "#7c4dff", "#e0409f", "#b57bff", "#5b21a6"]
ICONS_STATION = ["🔍", "🧠", "🛡️", "🗺️", "🎭", "🤸"]
ICONS_DISCUSS = ["🚪", "🏟️", "🏫", "📱", "🛒", "🤖"]

# ── content: German is authoritative, English comes from cards_en.json ────

STATIONS_DE = [
    dict(title="Objekt-Detektiv", tag="Was sieht die KI?",
         steps=["Halte Dinge aus der Kiste in die Kamera. Welche erkennt die "
                "KI, welche nicht?",
                "Schiebe den Regler „Wie sicher muss sich die KI sein?“ ganz "
                "nach links. Was für Unsinn taucht plötzlich auf?",
                "Schiebe ihn ganz nach rechts. Was übersieht die KI jetzt?"],
         rally="Finde einen Gegenstand, den die KI mit über 80 % erkennt — "
               "und einen, den sie komplett ignoriert.",
         think="Die KI kennt genau 80 Dinge. Wer hat das entschieden — und "
               "was bedeutet das für alles, was sie nicht kennt?"),
    dict(title="Trainiere die KI", tag="Du bist der Coach",
         steps=["Wähle zwei Gegenstände. Gib ihnen im Bildschirm echte Namen "
                "(Name antippen).",
                "Nimm von jedem 8–10 Beispiele auf — aus verschiedenen "
                "Winkeln und Entfernungen!",
                "Teste: Erkennt die KI beide zuverlässig?"],
         rally="<em>Der Bias-Versuch:</em> Trainiere absichtlich schlecht — "
               "nimm ein Ding nur von vorne auf, das andere nur von hinten. "
               "Drehe dann beide. Was passiert, und wie heißt dieses Problem "
               "bei echten KIs?",
         think="Hier kannst du alle Daten per Knopf löschen. Wo im Internet "
               "hättest du das auch gern?"),
    dict(title="Privatsphäre-Schild", tag="Schutz eingebaut",
         steps=["Schau in die Kamera — dein Gesicht wird sofort unkenntlich "
                "gemacht.",
                "Probiere die drei Schutz-Stile aus. Schalte den Schutz kurz "
                "aus: Wie fühlt sich der Unterschied an?",
                "Teste die Grenzen: Kopf drehen, Hand vors halbe Gesicht, "
                "Sonnenbrille…"],
         rally="Finde zwei Wege, wie der Schutz versagt. Notiert: Warum ist "
               "das bei einem „Schutz-Versprechen“ ein Problem?",
         think="Erkennen („da ist ein Gesicht“) ist nicht Wiedererkennen "
               "(„das ist Ali aus der 8b“). Warum ist dieser Unterschied so "
               "wichtig?"),
    dict(title="Die Datenspur", tag="Was Kameras sammeln",
         steps=["Öffne die Station und schau auf die Wärmekarte. Diese Daten "
                "wurden nebenbei gesammelt, während ihr gespielt habt!",
                "Lauft als Gruppe einen bestimmten Weg — seht ihr eure Spur "
                "entstehen?",
                "Drückt „Datenspur löschen“. Wer sollte diesen Knopf im "
                "echten Leben haben?"],
         rally="Nennt drei Dinge, die man aus so einer Karte über einen Raum "
               "und seine Menschen ablesen könnte — ganz ohne Gesichter.",
         think="„Ich habe doch nichts zu verbergen“ — gilt das auch für deine "
               "Laufwege, deine Gewohnheiten, deine Lieblingsecke?"),
    dict(title="Täusche die KI", tag="Finde ihre Grenzen",
         steps=["Die vier Challenges stehen am Bildschirm: Unsichtbar 🥷 · "
                "Verwechslung 🎩 · Volltreffer 💯 · Geister 👻"],
         rally="Schafft mindestens zwei Challenges und haltet fest, "
               "<em>wie</em> — euer Trick ist die Erkenntnis!",
         think="Ihr habt eine KI in wenigen Minuten überlistet. Was heißt das "
               "für Orte, an denen KIs allein entscheiden — Grenzkontrolle, "
               "Bewerbung, autonomes Fahren?"),
    dict(title="Skelett-Spiegel", tag="Spiel ohne Bild",
         steps=["Stell dich vor die Kamera — du wirst zum Strichmännchen mit "
                "17 Punkten.",
                "Spielt den Posen-Parcours: Wer schafft alle vier Posen am "
                "schnellsten?",
                "Schaltet den <strong>Geist-Modus</strong> ein: kein Video "
                "mehr, nur Skelette. Erkennt ihr trotzdem, wer wer ist?"],
         rally="Findet im Geist-Modus drei Dinge, die man über eine Person "
               "herausfinden kann, obwohl man ihr Gesicht nie sieht.",
         think="Spielkonsolen, Sturz-Melder im Pflegeheim, Kameras im "
               "Schwimmbad, die Ertrinkende erkennen — alles Skelett-Tracking. "
               "Wann ist es Fürsorge, wann Überwachung? Und wer entscheidet "
               "das?"),
]

DISCUSSION_DE = [
    dict(title="Die smarte Türklingel",
         scenario="Familie Yilmaz hat eine Kamera-Türklingel. Sie filmt "
                  "automatisch auch den Gehweg — also alle Nachbarn, den "
                  "Postboten, spielende Kinder. Die Aufnahmen landen auf "
                  "Servern des Herstellers in den USA.",
         ask="Wessen Privatsphäre zählt hier? Was würdet ihr ändern, wenn ihr "
             "die Türklingel <em>bauen</em> dürftet? (Tipp: Ihr habt heute "
             "eine Kamera gesehen, die Gesichter <em>vor</em> dem Speichern "
             "unkenntlich macht…)"),
    dict(title="Das Stadion",
         scenario="Ein Fußballstadion will Gesichts-Wiedererkennung am "
                  "Eingang: Bekannte Gewalttäter sollen automatisch erkannt "
                  "werden. Dafür wird <em>jedes</em> Gesicht aller 50.000 "
                  "Besucher:innen gescannt und mit einer Datenbank verglichen.",
         ask="49.990 Unbeteiligte werden gescannt, um 10 zu finden — fair oder "
             "nicht? Und was ist, wenn die KI sich irrt (ihr wisst ja jetzt, "
             "dass sie das tut)?"),
    dict(title="Die Schulkamera",
         scenario="Eure Schule überlegt, Kameras mit KI aufzuhängen, die "
                  "„auffälliges Verhalten“ melden sollen — Rangeleien, "
                  "Vandalismus. Gespeichert wird angeblich nichts, gemeldet "
                  "wird nur ein Alarm.",
         ask="Würdet ihr euch sicherer fühlen — oder beobachtet? Verändert "
             "eine Kamera, wie ihr euch verhaltet, selbst wenn sie „nichts "
             "speichert“? (Denkt an die Datenspur-Station!)"),
    dict(title="Der Gratis-Filter",
         scenario="Eine Foto-App macht lustige KI-Filter — kostenlos. Im "
                  "Kleingedruckten: Alle hochgeladenen Gesichter dürfen zum "
                  "Training neuer KI-Modelle verwendet werden.",
         ask="Ihr habt heute selbst eine KI trainiert — mit Daten, die ihr "
             "danach löschen konntet. Warum bieten die meisten Apps das nicht "
             "an? Was wäre ein fairer Tausch für einen Gratis-Filter?"),
    dict(title="Der Supermarkt",
         scenario="Ein Supermarkt zählt mit Kameras anonym, wo Kund:innen "
                  "entlanggehen und wo sie stehen bleiben — wie unsere "
                  "Wärmekarte, keine Gesichter. Damit werden Regale "
                  "umgeräumt und Preise platziert.",
         ask="Ist das okay, weil niemand erkennbar ist? Wo verläuft für euch "
             "die Grenze zwischen „anonymer Statistik“ und „Manipulation“?"),
    dict(title="Ihr seid die Chefs",
         scenario="Stellt euch vor: Ihr dürft die Regeln für alle KI-Kameras "
                  "in eurer Stadt schreiben. Ihr habt heute gesehen, was "
                  "möglich ist — Erkennen, Verfolgen, aber auch Schützen und "
                  "Löschen.",
         ask="<strong>Schreibt gemeinsam drei Regeln auf</strong>, die jede "
             "KI-Kamera einhalten müsste. Vergleicht mit den anderen Gruppen: "
             "Welche Regel kommt überall vor?"),
]

UI = {
    "de": dict(station="Station", discuss="Diskussionskarte", of="/",
               try_="Probiere das", rally="Rallye-Aufgabe",
               think="💭 Nachgefragt", ask="Diskutiert",
               subtitle="Privatsphäre & KI",
               note="5 Minuten diskutieren — dann ein Satz Fazit für die "
                    "Runde. Es gibt keine „richtigen“ Antworten, nur gute "
                    "Begründungen.",
               notes_label="Euer Fazit in einem Satz"),
    "en": dict(station="Station", discuss="Discussion card", of="/",
               try_="Try this", rally="Rally task",
               think="💭 Think about it", ask="Discuss",
               subtitle="Privacy & AI",
               note="Discuss for 5 minutes — then one sentence of takeaway "
                    "for the group. There are no “right” answers, only good "
                    "reasons.",
               notes_label="Your takeaway in one sentence"),
}


def load_content(lang):
    """Return (stations, discussion) for a language."""
    if lang == "de":
        return STATIONS_DE, DISCUSSION_DE
    path = HERE / f"cards_{lang}.json"
    if not path.exists():
        return None, None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["stations"], data["discussion"]


# ── HTML ─────────────────────────────────────────────────────────────────

def logos_html(cls="logos"):
    return (f'<div class="{cls}">'
            f'<img src="{LOGO}" alt="SKILL">'
            f'<img src="{LOGO2}" alt="aiwareness Lab">'
            f'</div>')


def front_html(kicker, icon, title, tag, color):
    long = " long" if len(title) > 16 else ""
    return f"""
<section class="card front" style="--c:{color}">
  <div class="glow"></div>
  <div class="bars">
    <i style="top:20%; left:0;   width:36%;"></i>
    <i style="top:33%; right:0;  width:24%;" class="cy"></i>
    <i style="top:70%; left:7%;  width:28%;" class="mg"></i>
    <i style="top:82%; right:4%; width:16%;"></i>
  </div>
  <div class="scan"></div>
  <div class="kicker">{kicker}</div>
  <div class="icon"><span class="cy">{icon}</span><span class="mg">{icon}</span><span>{icon}</span></div>
  <h2 class="glitch{long}" data-text="{title}">{title}</h2>
  <p class="tag">{tag}</p>
  {logos_html()}
</section>"""


def back_html(kicker, title, color, body):
    return f"""
<section class="card back" style="--c:{color}">
  <div class="topbar"></div>
  <div class="head"><span class="k">{kicker}</span><h3>{title}</h3></div>
  {body}
  <div class="foot">{logos_html("logos small")}<span>aiwarenesslab.io</span></div>
</section>"""


def station_pages(s, no, lang):
    u = UI[lang]
    steps = "".join(f"<li>{t}</li>" for t in s["steps"])
    body = f"""
  <div class="block"><h4>{u['try_']}</h4><ol>{steps}</ol></div>
  <div class="block accent"><h4>{u['rally']}</h4><p>{s['rally']}</p></div>
  <div class="block think"><h4>{u['think']}</h4><p>{s['think']}</p></div>"""
    kicker = f"{u['station']} {no} {u['of']} 6"
    color = ACCENT_STATION[no - 1]
    return (front_html(kicker, ICONS_STATION[no - 1], s["title"], s["tag"], color) +
            back_html(kicker, s["title"], color, body))


def discussion_pages(c, no, lang):
    u = UI[lang]
    body = f"""
  <div class="block"><p class="scenario">{c['scenario']}</p></div>
  <div class="block accent"><h4>{u['ask']}</h4><p>{c['ask']}</p></div>
  <p class="note">{u['note']}</p>
  <div class="notes"><span>{u['notes_label']}</span><i></i></div>"""
    kicker = f"{u['discuss']} {no} {u['of']} 6"
    color = ACCENT_DISCUSS[no - 1]
    return (front_html(kicker, ICONS_DISCUSS[no - 1], c["title"],
                       u["subtitle"], color) +
            back_html(kicker, c["title"], color, body))


def css():
    return f"""
  @page {{ size: A6 landscape; margin: 0; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0;
      -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
         background: #e8ecf5; display: flex; flex-direction: column;
         align-items: center; gap: 6mm; padding: 6mm; }}

  .card {{
    position: relative; overflow: hidden;
    width: {L['w']}mm; height: {L['h']}mm;
    page-break-after: always; break-after: page;
  }}
  @media screen {{ .card {{ box-shadow: 0 4px 18px rgba(20,26,51,.28);
                          border-radius: 2mm; }} }}
  @media print  {{ body {{ background: #fff; padding: 0; gap: 0; }} }}

  /* ── front ─────────────────────────────────────────────────────── */
  .front {{
    background: #0d1117; color: #e6edf3;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: {L['pad_top']}mm {L['pad_x']}mm;
    border-top: {L['bar']}mm solid var(--c);
  }}
  .front .glow {{
    position: absolute; inset: 0;
    background:
      radial-gradient(42mm 28mm at 78% 12%, color-mix(in srgb, var(--c) 42%, transparent), transparent 70%),
      radial-gradient(38mm 28mm at 12% 92%, color-mix(in srgb, var(--c) 26%, transparent), transparent 70%);
  }}
  .front .bars i {{
    position: absolute; height: 1.1mm; display: block;
    background: color-mix(in srgb, var(--c) 75%, transparent); opacity: .5;
  }}
  .front .bars i.cy {{ background: #29e7ff; height: .7mm; opacity: .45; }}
  .front .bars i.mg {{ background: #ff2e8a; height: 1.5mm; opacity: .38; }}
  .front .scan {{
    position: absolute; inset: 0; opacity: .5;
    background: repeating-linear-gradient(180deg,
      rgba(255,255,255,.055) 0 .3mm, transparent .3mm .95mm);
  }}

  .front .kicker {{
    position: relative; z-index: 2;
    font-size: {L['kicker']}mm; font-weight: 800; letter-spacing: 1.1mm;
    text-transform: uppercase; color: var(--c); margin-bottom: 3mm;
    padding-left: 1.1mm;
  }}
  .front .icon {{ position: relative; z-index: 2;
                 height: {L['icon']}mm; width: {L['icon']}mm; }}
  .front .icon span {{
    position: absolute; inset: 0; font-size: {L['icon'] - 2}mm;
    line-height: {L['icon']}mm; text-align: center;
  }}
  .front .icon span.cy {{ transform: translate(-1mm, .5mm); opacity: .5;
                         filter: hue-rotate(150deg) saturate(3); }}
  .front .icon span.mg {{ transform: translate(.9mm, -.45mm); opacity: .45;
                         filter: hue-rotate(300deg) saturate(3); }}

  .front h2 {{
    position: relative; z-index: 2; margin-top: 4mm;
    font-size: {L['title']}mm; line-height: 1.05; letter-spacing: -0.1mm;
    text-align: center; font-weight: 800; max-width: 100%;
  }}
  .front h2.long {{ font-size: {L['title_long']}mm; }}
  .front h2.glitch::before, .front h2.glitch::after {{
    content: attr(data-text); position: absolute; left: 0; right: 0; top: 0;
    text-align: center;
  }}
  .front h2.glitch::before {{
    color: #29e7ff; transform: translate(-.5mm, .22mm);
    clip-path: inset(4% 0 62% 0); opacity: .55;
  }}
  .front h2.glitch::after {{
    color: #ff2e8a; transform: translate(.45mm, -.22mm);
    clip-path: inset(66% 0 3% 0); opacity: .5;
  }}
  .front .tag {{
    position: relative; z-index: 2; margin-top: 2.4mm;
    font-size: {L['tag']}mm; color: var(--c); font-weight: 600;
  }}
  .front .logos {{
    position: absolute; z-index: 2; left: 0; right: 0; top: {L['logo_y']}mm;
    display: flex; justify-content: center; align-items: center;
    gap: {L['logo_gap']}mm;
  }}
  .front .logos img {{ height: {L['logo_h']}mm; width: auto; }}

  /* ── back ──────────────────────────────────────────────────────── */
  .back {{
    background: #fdfdfd; color: #141a33;
    padding: {L['pad_top']}mm {L['pad_x']}mm {L['pad_bot']}mm;
    display: flex; flex-direction: column; gap: 2.2mm;
  }}
  .back .topbar {{ position: absolute; top: 0; left: 0; right: 0;
                  height: {L['bar']}mm; background: var(--c); }}
  .back .head {{ display: flex; align-items: baseline; gap: 2.5mm;
                border-bottom: .3mm solid #dbe0ee; padding-bottom: 1.5mm; }}
  .back .head .k {{ font-size: {L['back_kicker']}mm; font-weight: 800;
                   letter-spacing: .4mm; text-transform: uppercase;
                   white-space: nowrap;
                   color: color-mix(in srgb, var(--c) 78%, #141a33); }}
  .back h3 {{ font-size: {L['back_title']}mm; letter-spacing: -.05mm; }}

  .back h4 {{ font-size: {L['h4']}mm; letter-spacing: .2mm;
             text-transform: uppercase;
             color: color-mix(in srgb, var(--c) 72%, #141a33);
             margin-bottom: 1.1mm; }}
  .back ol {{ padding-left: 4.5mm; display: flex; flex-direction: column;
             gap: .9mm; }}
  .back li, .back p {{ font-size: {L['body']}mm; line-height: 1.42; }}
  .back .scenario {{ font-size: {L['body'] + .15}mm; line-height: 1.45; }}
  .back .block.accent {{
    background: color-mix(in srgb, var(--c) 10%, #fdfdfd);
    border-left: .9mm solid var(--c);
    border-radius: 0 1.8mm 1.8mm 0; padding: 1.8mm 2.6mm;
  }}
  .back .block.think {{
    background: rgba(255,214,102,.16);
    border: .3mm dashed rgba(190,140,20,.55);
    border-radius: 1.8mm; padding: 1.8mm 2.6mm;
  }}
  .back .note {{ font-size: {L['note']}mm; color: #5a6382; line-height: 1.4; }}
  .back .notes span {{ font-size: {L['note'] - .2}mm; letter-spacing: .3mm;
                      text-transform: uppercase; color: #a6adc0; }}
  .back .notes i {{ display: block; height: 6mm;
                   border-bottom: .25mm dotted #c9d0e2; }}
  .back .foot {{ margin-top: auto; display: flex; align-items: center;
                justify-content: space-between;
                border-top: .3mm solid #dbe0ee; padding-top: 1.5mm; }}
  .back .foot span {{ font-size: {L['foot']}mm; color: #8a92ab; }}
  .back .logos {{ display: flex; align-items: center; gap: 3.5mm; }}
  .back .logos img {{ height: 4mm; width: auto; }}
"""


TITLES = {"de": "KI-Werkstatt · Kartendeck A6",
          "en": "AI-Lab2Go · Card deck A6"}


def build_html(lang, stations, discussion):
    pages = "".join(station_pages(s, i + 1, lang) for i, s in enumerate(stations))
    pages += "".join(discussion_pages(c, i + 1, lang)
                     for i, c in enumerate(discussion))
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8">
<title>{TITLES[lang]}</title>
<style>{css()}</style></head>
<body>
{pages}
</body></html>
"""


def main():
    made = []
    for lang in ("de", "en"):
        stations, discussion = load_content(lang)
        if stations is None:
            print(f"⚠ {lang}: setup/cards_{lang}.json fehlt — übersprungen")
            continue
        out = HERE / f"cards_{lang}.html"
        out.write_text(build_html(lang, stations, discussion), encoding="utf-8")
        n = len(stations) + len(discussion)
        print(f"✓ {out.name} — {n} Karten ({n * 2} A6-Seiten, {lang.upper()})")
        made.append(lang)
    print("  Drucken: doppelseitig, A6 quer, an der KURZEN Seite spiegeln.")
    return made


if __name__ == "__main__":
    langs = main()
    if "--editable" in sys.argv:
        import build_cards_editable
        build_cards_editable.run(langs)
