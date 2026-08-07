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
| **Kartendeck** (12 Karten: 6 Stationen + 6 Diskussionskarten) | [`cards/cards_de.pdf`](cards/cards_de.pdf) | DIN A6 quer, **doppelseitig, an der KURZEN Seite spiegeln**. Auf A4: „4 Seiten pro Blatt", danach zweimal schneiden. |
| **Stationsschilder / Werbebilder** (16:9) | [`stations/`](stations/) | Neben die Station legen, an die Wand projizieren oder in eigene Folien einbauen. |
| **Leitfaden für die Moderation** | [`guide/leitfaden_de.md`](guide/leitfaden_de.md) | Muss nicht gedruckt werden — Aufbau-Checkliste, Zeitformate (45/90 Min.), Lernziele und Moderationsimpulse je Station, Pannenhilfe. |

### In welcher Reihenfolge?

1. **Vorher lesen:** [`guide/leitfaden_de.md`](guide/leitfaden_de.md) — besonders die
   Requisiten-Kiste. Die macht den Unterschied zwischen „nett" und „unvergesslich".
2. **Drucken:** Poster (1×) und Kartendeck (1× pro Kleingruppe).
3. **Aufbau + Technik:** steht in der [ANLEITUNG.md](../ANLEITUNG.md) — SD-Karte,
   Installation, Hotspot, Fehlerbehebung.

### Das Kartendeck genauer

Die **Karten 1–6** liegen an den Stationen: Was probiere ich aus? Was ist die
Rallye-Aufgabe? Was nehme ich mit? Die **Karten 7–12** sind Diskussionskarten
für die Abschlussrunde (smarte Türklingel, Stadion, Schule, Handy, Supermarkt,
KI-Entscheidungen) — jede Kleingruppe zieht eine.

### Eigenes Layout?

In [`source/`](source/) liegen die Rohdaten: 300-dpi-Hintergründe und
freigestellte Icons für die Karten, Ebenen-PNGs und SVGs für die
Stationsschilder. Damit kannst du in Photoshop, Illustrator, Affinity oder
PowerPoint eigene Varianten bauen. Schriften: Helvetica Neue.
Markenfarben `#400b67` / `#c32683`.

---

## 🇬🇧 What do I print, and what for?

| What | File | Printing |
|---|---|---|
| **Poster** for the entrance / next to the exhibit | [`poster/poster_en.pdf`](poster/poster_en.pdf) | A4, single-sided. Carries both QR codes: join the Wi-Fi + open the exhibit. |
| **Card deck** (12 cards: 6 stations + 6 discussion cards) | [`cards/cards_en.pdf`](cards/cards_en.pdf) | A6 landscape, **double-sided, flip on the SHORT edge**. On A4: "4 pages per sheet", then cut twice. |
| **Station signs / promo images** (16:9) | [`stations/`](stations/) | Lay them out next to each station, project them, or drop them into your own slides. |
| **Facilitator guide** | [`guide/guide_en.md`](guide/guide_en.md) | No need to print — setup checklist, session formats (45/90 min), learning goals and facilitation prompts per station, troubleshooting. |

### In what order?

1. **Read first:** [`guide/guide_en.md`](guide/guide_en.md) — especially the prop box.
   That is what turns "nice" into "unforgettable".
2. **Print:** the poster (once) and the card deck (once per small group).
3. **Build it + tech:** see [MANUAL.md](../MANUAL.md) — SD card, install, hotspot,
   troubleshooting.

### About the card deck

**Cards 1–6** go to the stations: what do I try, what is the rally task, what do
I take away? **Cards 7–12** are discussion cards for the closing round (smart
doorbell, stadium, school, phone, supermarket, AI decisions) — each small group
draws one.

### Want your own layout?

[`source/`](source/) holds the raw material: 300 dpi backgrounds and cut-out icons
for the cards, layer PNGs and SVGs for the station signs. Build your own variants
in Photoshop, Illustrator, Affinity or PowerPoint. Type: Helvetica Neue.
Brand colours `#400b67` / `#c32683`.

---

## 🔄 Neu erzeugen · Regenerating

Nur nötig, wenn du Texte, Farben oder das WLAN-Passwort geändert hast — die
fertigen PDFs oben sind aktuell. *Only needed if you changed texts, colours or
the Wi-Fi password; the PDFs above are up to date.*

```bash
bash setup/tools.sh all              # Poster + Karten + Stationsbilder
bash setup/tools.sh poster           # nur die Poster
bash setup/tools.sh cards            # nur das Kartendeck
bash setup/tools.sh stations         # nur die Stationsbilder
```

Die Inhalte stehen im Code, **einmalig** und ohne Dubletten:
deutsche Kartentexte in [`setup/make_cards.py`](../setup/make_cards.py),
englische in [`setup/cards_en.json`](../setup/cards_en.json) — Übersetzen geht
also ohne Programmierkenntnisse. *Content lives in the code exactly once:
German card texts in `setup/make_cards.py`, English in `setup/cards_en.json`,
so translating needs no coding.*
