# 📦 Material · Alles zum Ausdrucken und Mitnehmen

**Everything ready to print — no software needed.**

> 🇩🇪 Deutsch unten · 🇬🇧 English below
> Alle Dateien sind fertig. Du brauchst **kein Python, keine Installation** —
> nur einen Drucker. *Everything here is ready to use. No Python, no install
> — just a printer.*

---

## 🇩🇪 Was drucke ich wofür?

| Was | Datei | Drucken |
|---|---|---|
| **Poster** für den Eingang / neben das Exponat | [`poster/poster_de.pdf`](poster/poster_de.pdf) | A4, einseitig. Trägt die beiden QR-Codes: WLAN beitreten + Ausstellung öffnen. |
| **Kartendeck** (11 Karten: 6 Stationen + 5 Diskussionskarten) | [`cards/cards_de.pdf`](cards/cards_de.pdf) | DIN A6 quer, **doppelseitig, an der KURZEN Seite spiegeln**. Auf A4: „4 Seiten pro Blatt", danach zweimal schneiden. |
| **Stationsschilder / Werbebilder** (16:9) | [`stations/`](stations/) | Neben die Station legen, an die Wand projizieren oder in eigene Folien einbauen. |
| **Leitfaden für die Moderation** | [`guide/leitfaden_de.md`](guide/leitfaden_de.md) | Muss nicht gedruckt werden — Aufbau-Checkliste, Zeitformate (45/90 Min.), Lernziele und Moderationsimpulse je Station, Pannenhilfe. |

### In welcher Reihenfolge?

1. **Vorher lesen:** [`guide/leitfaden_de.md`](guide/leitfaden_de.md) — besonders die
   Requisiten-Kiste. Die macht den Unterschied zwischen „nett" und „unvergesslich".
2. **Drucken:** Poster (1×) und Kartendeck (1× pro Kleingruppe).
3. **Aufbau + Technik:** steht in der [ANLEITUNG.md](../ANLEITUNG.md) — SD-Karte,
   Installation, Hotspot, Fehlerbehebung.

### Das Kartendeck genauer

Die **Karten 1–6** liegen an den Stationen (Objekt-Detektiv, Trainiere die KI,
Privatsphäre-Schild, Die Datenspur, Täusche die KI, Skelett-Spiegel): vorne das
Thema, hinten die Aufgaben. Die **Karten 7–11** sind Diskussionskarten für die
Abschlussrunde — smarte Türklingel, Stadion, Schulkamera, Foto-Filter,
Supermarkt. Jede Kleingruppe zieht eine.

### Karten ändern? Die PowerPoint-Datei ist der Master

Das Design der Karten lebt in
[`source/cards/cards_de.pptx`](source/cards/cards_de.pptx) bzw.
[`cards_en.pptx`](source/cards/cards_en.pptx) — dort bearbeiten, speichern,
dann:

```bash
bash setup/tools.sh cards      # PPTX → druckfertige PDFs, Design 1:1
```

Der Befehl **gestaltet nichts um**, er wandelt nur um: Was in PowerPoint
steht, steht danach im PDF. Beim ersten Mal erklärt er, welche einmalige
Freigabe macOS dafür braucht.

### Eigenes Layout?

In [`source/`](source/) liegen außerdem die Rohdaten: 300-dpi-Hintergründe
und freigestellte Icons (die in den PowerPoint-Folien stecken), Ebenen-PNGs
und SVGs für die Stationsschilder. Damit kannst du in Photoshop,
Illustrator, Affinity oder PowerPoint eigene Varianten bauen.
Schriften: Helvetica Neue. Markenfarben `#400b67` / `#c32683`.

---

## 🇬🇧 What do I print, and what for?

| What | File | Printing |
|---|---|---|
| **Poster** for the entrance / next to the exhibit | [`poster/poster_en.pdf`](poster/poster_en.pdf) | A4, single-sided. Carries both QR codes: join the Wi-Fi + open the exhibit. |
| **Card deck** (11 cards: 6 stations + 5 discussion cards) | [`cards/cards_en.pdf`](cards/cards_en.pdf) | A6 landscape, **double-sided, flip on the SHORT edge**. On A4: "4 pages per sheet", then cut twice. |
| **Station signs / promo images** (16:9) | [`stations/`](stations/) | Lay them out next to each station, project them, or drop them into your own slides. |
| **Facilitator guide** | [`guide/guide_en.md`](guide/guide_en.md) | No need to print — setup checklist, session formats (45/90 min), learning goals and facilitation prompts per station, troubleshooting. |

### In what order?

1. **Read first:** [`guide/guide_en.md`](guide/guide_en.md) — especially the prop box.
   That is what turns "nice" into "unforgettable".
2. **Print:** the poster (once) and the card deck (once per small group).
3. **Build it + tech:** see [MANUAL.md](../MANUAL.md) — SD card, install, hotspot,
   troubleshooting.

### About the card deck

**Cards 1–6** go to the stations (Object Detective, Train the AI, Privacy
Shield, The Data Trail, Fool the AI, Skeleton Mirror): the theme on the front,
the tasks on the back. **Cards 7–11** are discussion cards for the closing
round — smart doorbell, stadium, school camera, photo filter, supermarket.
Each small group draws one.

### Changing the cards? The PowerPoint file is the master

The card design lives in
[`source/cards/cards_de.pptx`](source/cards/cards_de.pptx) and
[`cards_en.pptx`](source/cards/cards_en.pptx) — edit there, save, then:

```bash
bash setup/tools.sh cards      # PPTX → print-ready PDFs, design 1:1
```

The command **never re-designs**, it only converts: whatever is in
PowerPoint is what ends up in the PDF. On first run it explains the
one-time macOS permission it needs.

### Want your own layout?

[`source/`](source/) also holds the raw material: 300 dpi backgrounds and
cut-out icons (the ones used inside the PowerPoint slides), layer PNGs and
SVGs for the station signs. Build your own variants in Photoshop,
Illustrator, Affinity or PowerPoint. Type: Helvetica Neue.
Brand colours `#400b67` / `#c32683`.

---

## 🔄 Neu erzeugen · Regenerating

Nur nötig, wenn du Texte, Farben oder das WLAN-Passwort geändert hast — die
fertigen PDFs oben sind aktuell. *Only needed if you changed texts, colours or
the Wi-Fi password; the PDFs above are up to date.*

```bash
bash setup/tools.sh all           # Poster + Karten + Stationsbilder
bash setup/tools.sh poster        # nur die Poster (Text: setup/make_poster.py)
bash setup/tools.sh cards         # Karten-PDFs aus den PowerPoint-Mastern
bash setup/tools.sh card-layers   # die 300-dpi-Hintergründe in den Folien
bash setup/tools.sh stations      # nur die Stationsbilder
bash setup/tools.sh cards-html    # alternatives HTML-Deck (anderes Design)
```

**Wo steht welcher Inhalt?** Die gedruckten Karten kommen aus den
PowerPoint-Dateien in `material/source/cards/` — dort ändern, dann
`tools.sh cards`. Das Poster kommt aus
[`setup/make_poster.py`](../setup/make_poster.py). Das alternative
HTML-Deck (`cards-html`) hat ein eigenes Design mit eigenen Texten:
deutsch in [`setup/make_cards.py`](../setup/make_cards.py), englisch in
[`setup/cards_en.json`](../setup/cards_en.json).

*Printed cards come from the PowerPoint masters in
`material/source/cards/` — edit there, then `tools.sh cards`. The poster
comes from `setup/make_poster.py`. The alternative HTML deck
(`cards-html`) is a separate design with its own texts: German in
`setup/make_cards.py`, English in `setup/cards_en.json`.*
