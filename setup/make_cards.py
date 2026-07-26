#!/usr/bin/env python3
"""Generate the printable A5 postcard deck (station + discussion cards).

    python3 setup/make_cards.py
    → setup/cards_de.html   (24 A5-landscape pages: 12 cards, front + back)

Open in a browser and print double-sided on A5.
**Duplex setting: flip on the SHORT edge** — landscape pages come out
upside down with the usual long-edge setting.
Printing on A4 instead? Choose "2 pages per sheet" and cut in the middle.

Card layout
  front — dark, station colour, big icon, glitch-styled title, both logos
  back  — light and calm, the actual text (tasks / discussion prompts)

The glitch is deliberately static (offset colour copies, scanlines, noise
bars): it must survive a printer, so nothing here depends on animation.
"""

import base64
from pathlib import Path

_static = Path(__file__).parent.parent / "app" / "static"


def _data_uri(path: Path) -> str:
    return ("data:image/png;base64," +
            base64.b64encode(path.read_bytes()).decode()) if path.exists() else ""


LOGO = _data_uri(_static / "logo.png")     # SKILL
LOGO2 = _data_uri(_static / "logo2.png")   # aiwareness Lab

# ── content ───────────────────────────────────────────────────────────────
# Kept in sync with workshop/stationskarten.md and
# workshop/diskussionskarten-privatsphaere.md.

STATIONS = [
    dict(no=1, icon="🔍", title="Objekt-Detektiv", tag="Was sieht die KI?",
         color="#4ea8ff",
         steps=["Halte Dinge aus der Kiste in die Kamera. Welche erkennt die "
                "KI, welche nicht?",
                "Schiebe den Regler „Wie sicher muss sich die KI sein?“ ganz "
                "nach links. Was für Unsinn taucht plötzlich auf?",
                "Schiebe ihn ganz nach rechts. Was übersieht die KI jetzt?"],
         rally="Finde einen Gegenstand, den die KI mit über 80 % erkennt — "
               "und einen, den sie komplett ignoriert.",
         think="Die KI kennt genau 80 Dinge. Wer hat das entschieden — und "
               "was bedeutet das für alles, was sie nicht kennt?"),
    dict(no=2, icon="🧠", title="Trainiere die KI", tag="Du bist der Coach",
         color="#b57bff",
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
    dict(no=3, icon="🛡️", title="Privatsphäre-Schild", tag="Schutz eingebaut",
         color="#3ddc97",
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
    dict(no=4, icon="🗺️", title="Die Datenspur", tag="Was Kameras sammeln",
         color="#ffb347",
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
    dict(no=5, icon="🎭", title="Täusche die KI", tag="Finde ihre Grenzen",
         color="#ff5d8f",
         steps=["Die vier Challenges stehen am Bildschirm: Unsichtbar 🥷 · "
                "Verwechslung 🎩 · Volltreffer 💯 · Geister 👻"],
         rally="Schafft mindestens zwei Challenges und haltet fest, "
               "<em>wie</em> — euer Trick ist die Erkenntnis!",
         think="Ihr habt eine KI in wenigen Minuten überlistet. Was heißt das "
               "für Orte, an denen KIs allein entscheiden — Grenzkontrolle, "
               "Bewerbung, autonomes Fahren?"),
    dict(no=6, icon="🤸", title="Skelett-Spiegel", tag="Spiel ohne Bild",
         color="#2dd4bf",
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
               "Wann ist es Fürsorge, wann Überwachung? Und wer entscheidet das?"),
]

DISCUSSION = [
    dict(no=1, icon="🚪", title="Die smarte Türklingel", color="#8a4fd8",
         scenario="Familie Yilmaz hat eine Kamera-Türklingel. Sie filmt "
                  "automatisch auch den Gehweg — also alle Nachbarn, den "
                  "Postboten, spielende Kinder. Die Aufnahmen landen auf "
                  "Servern des Herstellers in den USA.",
         ask="Wessen Privatsphäre zählt hier? Was würdet ihr ändern, wenn ihr "
             "die Türklingel <em>bauen</em> dürftet? (Tipp: Ihr habt heute "
             "eine Kamera gesehen, die Gesichter <em>vor</em> dem Speichern "
             "unkenntlich macht…)"),
    dict(no=2, icon="🏟️", title="Das Stadion", color="#c32683",
         scenario="Ein Fußballstadion will Gesichts-Wiedererkennung am "
                  "Eingang: Bekannte Gewalttäter sollen automatisch erkannt "
                  "werden. Dafür wird <em>jedes</em> Gesicht aller 50.000 "
                  "Besucher:innen gescannt und mit einer Datenbank verglichen.",
         ask="49.990 Unbeteiligte werden gescannt, um 10 zu finden — fair oder "
             "nicht? Und was ist, wenn die KI sich irrt (ihr wisst ja jetzt, "
             "dass sie das tut)?"),
    dict(no=3, icon="🏫", title="Die Schulkamera", color="#7c4dff",
         scenario="Eure Schule überlegt, Kameras mit KI aufzuhängen, die "
                  "„auffälliges Verhalten“ melden sollen — Rangeleien, "
                  "Vandalismus. Gespeichert wird angeblich nichts, gemeldet "
                  "wird nur ein Alarm.",
         ask="Würdet ihr euch sicherer fühlen — oder beobachtet? Verändert "
             "eine Kamera, wie ihr euch verhaltet, selbst wenn sie „nichts "
             "speichert“? (Denkt an die Datenspur-Station!)"),
    dict(no=4, icon="📱", title="Der Gratis-Filter", color="#e0409f",
         scenario="Eine Foto-App macht lustige KI-Filter — kostenlos. Im "
                  "Kleingedruckten: Alle hochgeladenen Gesichter dürfen zum "
                  "Training neuer KI-Modelle verwendet werden.",
         ask="Ihr habt heute selbst eine KI trainiert — mit Daten, die ihr "
             "danach löschen konntet. Warum bieten die meisten Apps das nicht "
             "an? Was wäre ein fairer Tausch für einen Gratis-Filter?"),
    dict(no=5, icon="🛒", title="Der Supermarkt", color="#b57bff",
         scenario="Ein Supermarkt zählt mit Kameras anonym, wo Kund:innen "
                  "entlanggehen und wo sie stehen bleiben — wie unsere "
                  "Wärmekarte, keine Gesichter. Damit werden Regale umgeräumt "
                  "und Preise platziert.",
         ask="Ist das okay, weil niemand erkennbar ist? Wo verläuft für euch "
             "die Grenze zwischen „anonymer Statistik“ und „Manipulation“?"),
    dict(no=6, icon="🤖", title="Ihr seid die Chefs", color="#400b67",
         scenario="Stellt euch vor: Ihr dürft die Regeln für alle KI-Kameras "
                  "in eurer Stadt schreiben. Ihr habt heute gesehen, was "
                  "möglich ist — Erkennen, Verfolgen, aber auch Schützen und "
                  "Löschen.",
         ask="<strong>Schreibt gemeinsam drei Regeln auf</strong>, die jede "
             "KI-Kamera einhalten müsste. Vergleicht mit den anderen Gruppen: "
             "Welche Regel kommt überall vor?"),
]


# ── card rendering ────────────────────────────────────────────────────────

def logos_block(cls="logos"):
    return (f'<div class="{cls}">'
            f'<img src="{LOGO}" alt="SKILL">'
            f'<img src="{LOGO2}" alt="aiwareness Lab">'
            f'</div>')


def front(kicker, icon, title, tag, color):
    long = " long" if len(title) > 16 else ""
    return f"""
<section class="card front" style="--c:{color}">
  <div class="glow"></div>
  <div class="bars">
    <i style="top:19%; left:0;  width:38%;"></i>
    <i style="top:34%; right:0; width:26%;" class="cy"></i>
    <i style="top:71%; left:8%; width:30%;" class="mg"></i>
    <i style="top:83%; right:4%;width:18%;"></i>
  </div>
  <div class="scan"></div>
  <div class="kicker">{kicker}</div>
  <div class="icon"><span class="cy">{icon}</span><span class="mg">{icon}</span><span>{icon}</span></div>
  <h2 class="glitch{long}" data-text="{title}">{title}</h2>
  <p class="tag">{tag}</p>
  {logos_block()}
</section>"""


def back(kicker, title, color, body):
    return f"""
<section class="card back" style="--c:{color}">
  <div class="topbar"></div>
  <div class="head"><span class="k">{kicker}</span><h3>{title}</h3></div>
  {body}
  <div class="foot">{logos_block("logos small")}<span>aiwarenesslab.io</span></div>
</section>"""


def station_pages(s):
    steps = "".join(f"<li>{t}</li>" for t in s["steps"])
    body = f"""
  <div class="block">
    <h4>Probiere das</h4>
    <ol>{steps}</ol>
  </div>
  <div class="block accent">
    <h4>Rallye-Aufgabe</h4>
    <p>{s['rally']}</p>
  </div>
  <div class="block think">
    <h4>💭 Denk mal nach</h4>
    <p>{s['think']}</p>
  </div>"""
    kicker = f"Station {s['no']} / 6"
    return (front(kicker, s["icon"], s["title"], s["tag"], s["color"]) +
            back(kicker, s["title"], s["color"], body))


def discussion_pages(c):
    body = f"""
  <div class="block">
    <p class="scenario">{c['scenario']}</p>
  </div>
  <div class="block accent">
    <h4>Diskutiert</h4>
    <p>{c['ask']}</p>
  </div>
  <p class="note">5 Minuten diskutieren — dann ein Satz Fazit für die Runde.
    Es gibt keine „richtigen“ Antworten, nur gute Begründungen.</p>
  <div class="notes"><span>Euer Fazit in einem Satz</span><i></i><i></i></div>"""
    kicker = f"Diskussionskarte {c['no']} / 6"
    return (front(kicker, c["icon"], c["title"], "Privatsphäre & KI", c["color"]) +
            back(kicker, c["title"], c["color"], body))


CSS = """
  @page { size: A5 landscape; margin: 0; }
  * { box-sizing: border-box; margin: 0; padding: 0;
      -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
         background: #e8ecf5; display: flex; flex-direction: column;
         align-items: center; gap: 8mm; padding: 8mm; }

  .card {
    position: relative; overflow: hidden;
    width: 210mm; height: 148mm;
    page-break-after: always; break-after: page;
  }
  @media screen { .card { box-shadow: 0 6px 24px rgba(20,26,51,.28);
                          border-radius: 3mm; } }
  @media print  { body { background: #fff; padding: 0; gap: 0; } }

  /* ── front ─────────────────────────────────────────────────────── */
  .front {
    background: #0d1117; color: #e6edf3;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 14mm 16mm;
    border-top: 3mm solid var(--c);
  }
  .front .glow {
    position: absolute; inset: 0;
    background:
      radial-gradient(60mm 40mm at 78% 12%, color-mix(in srgb, var(--c) 42%, transparent), transparent 70%),
      radial-gradient(55mm 40mm at 12% 92%, color-mix(in srgb, var(--c) 26%, transparent), transparent 70%);
  }
  /* glitch: displaced noise bars */
  .front .bars i {
    position: absolute; height: 1.6mm; display: block;
    background: color-mix(in srgb, var(--c) 75%, transparent);
    opacity: .5;
  }
  .front .bars i.cy { background: #29e7ff; height: 1mm; opacity: .45; }
  .front .bars i.mg { background: #ff2e8a; height: 2.2mm; opacity: .38; }
  /* glitch: scanlines */
  .front .scan {
    position: absolute; inset: 0; opacity: .5;
    background: repeating-linear-gradient(180deg,
      rgba(255,255,255,.055) 0 0.35mm, transparent 0.35mm 1.1mm);
  }

  .front .kicker {
    position: relative; z-index: 2;
    font-size: 3.6mm; font-weight: 800; letter-spacing: 1.6mm;
    text-transform: uppercase; color: var(--c); margin-bottom: 5mm;
    padding-left: 1.6mm;
  }
  /* glitch: three offset copies of the icon */
  .front .icon { position: relative; z-index: 2; height: 34mm; width: 34mm; }
  .front .icon span {
    position: absolute; inset: 0; font-size: 30mm; line-height: 34mm;
    text-align: center;
  }
  .front .icon span.cy { transform: translate(-1.6mm, .8mm); opacity: .5;
                         filter: hue-rotate(150deg) saturate(3); }
  .front .icon span.mg { transform: translate(1.4mm, -.7mm); opacity: .45;
                         filter: hue-rotate(300deg) saturate(3); }

  .front h2 {
    position: relative; z-index: 2; margin-top: 7mm;
    font-size: 14mm; line-height: 1.05; letter-spacing: -0.2mm;
    text-align: center; font-weight: 800;
    max-width: 100%;
  }
  /* long compound names (Privatsphäre-Schild) get a step down */
  .front h2.long { font-size: 11.5mm; }
  /* glitch: colour-split copies, sliced so only bands are offset */
  .front h2.glitch::before,
  .front h2.glitch::after {
    content: attr(data-text);
    position: absolute; left: 0; right: 0; top: 0;
    text-align: center;
  }
  /* subtle on purpose: the title must stay readable across a room */
  .front h2.glitch::before {
    color: #29e7ff; transform: translate(-0.8mm, .35mm);
    clip-path: inset(4% 0 62% 0); opacity: .55;
  }
  .front h2.glitch::after {
    color: #ff2e8a; transform: translate(0.75mm, -.35mm);
    clip-path: inset(66% 0 3% 0); opacity: .5;
  }
  .front .tag {
    position: relative; z-index: 2; margin-top: 4mm;
    font-size: 5.4mm; color: var(--c); font-weight: 600;
  }
  .front .logos {
    position: absolute; z-index: 2; left: 0; right: 0; bottom: 9mm;
    display: flex; justify-content: center; align-items: center; gap: 7mm;
  }
  .front .logos img { height: 7mm; width: auto; }

  /* ── back ──────────────────────────────────────────────────────── */
  .back {
    background: #fdfdfd; color: #141a33;
    padding: 11mm 14mm 8mm;
    display: flex; flex-direction: column; gap: 4mm;
  }
  .back .topbar { position: absolute; top: 0; left: 0; right: 0;
                  height: 3mm; background: var(--c); }
  .back .head { display: flex; align-items: baseline; gap: 4mm;
                border-bottom: 0.4mm solid #dbe0ee; padding-bottom: 2.5mm; }
  .back .head .k { font-size: 3.4mm; font-weight: 800; letter-spacing: .6mm;
                   text-transform: uppercase;
                   color: color-mix(in srgb, var(--c) 78%, #141a33); }
  .back h3 { font-size: 7mm; letter-spacing: -.1mm; }

  .back .block { }
  .back h4 { font-size: 4.2mm; letter-spacing: .3mm; text-transform: uppercase;
             color: color-mix(in srgb, var(--c) 72%, #141a33);
             margin-bottom: 1.8mm; }
  .back ol { padding-left: 6mm; display: flex; flex-direction: column;
             gap: 1.4mm; }
  .back li, .back p { font-size: 4.1mm; line-height: 1.5; }
  .back .scenario { font-size: 4.4mm; line-height: 1.55; }
  .back .block.accent {
    background: color-mix(in srgb, var(--c) 10%, #fdfdfd);
    border-left: 1.2mm solid var(--c);
    border-radius: 0 2.5mm 2.5mm 0; padding: 3mm 4mm;
  }
  .back .block.think {
    background: rgba(255,214,102,.16);
    border: 0.4mm dashed rgba(190,140,20,.55);
    border-radius: 2.5mm; padding: 3mm 4mm;
  }
  .back .note { font-size: 3.5mm; color: #5a6382; line-height: 1.45; }
  /* writing area — turns the leftover space into something useful */
  .back .notes { margin-top: 1mm; }
  .back .notes span { font-size: 3.2mm; letter-spacing: .4mm;
                      text-transform: uppercase; color: #a6adc0; }
  .back .notes i { display: block; height: 9mm;
                   border-bottom: 0.3mm dotted #c9d0e2; }
  .back .foot { margin-top: auto; display: flex; align-items: center;
                justify-content: space-between;
                border-top: 0.4mm solid #dbe0ee; padding-top: 2.5mm; }
  .back .foot span { font-size: 3.3mm; color: #8a92ab; }
  .back .logos { display: flex; align-items: center; gap: 5mm; }
  .back .logos img { height: 5.5mm; width: auto; }
"""


def main():
    pages = "".join(station_pages(s) for s in STATIONS) + \
            "".join(discussion_pages(c) for c in DISCUSSION)

    html = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<title>KI-Werkstatt · Kartendeck A5</title>
<style>{CSS}</style></head>
<body>
{pages}
</body></html>
"""
    out = Path(__file__).parent / "cards_de.html"
    out.write_text(html, encoding="utf-8")
    n = len(STATIONS) + len(DISCUSSION)
    print(f"✓ {out.name} — {n} Karten ({n * 2} A5-Seiten: Vorder-/Rückseite)")
    print("  Drucken: doppelseitig, A5 quer, an der KURZEN Seite spiegeln.")


if __name__ == "__main__":
    main()
