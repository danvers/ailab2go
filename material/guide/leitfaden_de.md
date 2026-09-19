# KI-Werkstatt · Leitfaden für Moderator:innen

Ein interaktives Mitmach-Exponat rund um **maschinelles Sehen** und
**Privatsphäre-Kompetenz** — für Schulklassen, Maker-Events und offene
Veranstaltungen mit gemischtem Publikum. Die Teilnehmenden nutzen ihre
eigenen Handys/Laptops, es ist keine App-Installation nötig.

---

## Die Idee in einem Satz

> Besucher:innen oder Teilnehemde spielen mit einer echten KI-Kamera, verstehen dabei, *wie*
> Maschinen lernen und sehen — und erleben am eigenen Körper, warum
> Datenschutz kein Verbotsthema ist, sondern gestaltbar.

**Der rote Faden:** Dieselbe Technik kann überwachen *oder* schützen.
Es kommt darauf an, wie wir sie bauen und einsetzen.

---

## Aufbau-Checkliste (15 Minuten)

- [ ] Raspberry Pi 5 mit AI HAT + Kamera aufbauen, Kamera auf den
      „Spielbereich" richten (2–4 m Abstand ist ideal)
- [ ] **Wichtig:** Gut sichtbares Schild aufstellen: *„Hier läuft eine
      Kamera-Installation. Es werden keine Bilder gespeichert."* — wir
      praktizieren die Transparenz, über die wir reden!
- [ ] Pi einschalten — die Ausstellung startet automatisch
- [ ] Hotspot prüfen: eigenes Handy mit WLAN `KI-Werkstatt` verbinden,
      `http://10.10.10.1` öffnen
- [ ] Poster mit QR-Codes aufhängen (`../poster/poster_de.pdf`)
- [ ] Requisiten-Kiste bereitstellen (siehe unten)
- [ ] Optional: Stationskarten ausdrucken und auslegen
      (`../cards/cards_de.pdf`, Karten 1–6)

### Requisiten-Kiste (macht den Unterschied!)

Das eingebaute Modell kennt genau die 80 Alltagsklassen des
COCO-Datensatzes — die Kiste bewusst danach sortieren:

- **Klappt zuverlässig (Station 1):** Tasse, Banane, Apfel, Orange,
  Flasche, Buch, Teddybär, Schere, Ball, Regenschirm, Handy, Laptop,
  Uhr, Löffel.
- **Scheitert absichtlich** (Spielzeugdino, Hammer/Schraubenzieher,
  Gemüse außer Brokkoli/Karotte): nicht wegwerfen! Erst an Station 2
  antrainieren — dann erkennt der Detektiv sie als „✨ selbst trainiert"
  — und an Station 5 sind sie die beste Munition.
- Sonnenbrille, Mütze, Schal → für Station 3 und 5.
- Ein Handy mit Tierfotos → „Geister"-Challenge in Station 5.

---

## Formate

| Format | Dauer | Ablauf |
|---|---|---|
| **Offenes Exponat** | beliebig | Selbsterklärend, läuft allein. Alle 30–45 Min. kurz vorbeischauen, ggf. „♻️ Zurücksetzen" (Moderationsleiste). |
| **Workshop kompakt** | 45 Min. | 10 Min. Intro → 25 Min. freies Erkunden in Gruppen → 10 Min. Abschlussrunde mit Diskussionskarten |
| **Workshop vertieft** | 90 Min. | Wie kompakt, plus: 20 Min. Stationen-Rallye mit Aufgaben (Stationskarten) und 15 Min. Diskussion in Kleingruppen |

**Tipp für Gruppen:** Alle sehen dasselbe Kamerabild und steuern gemeinsam.
Das ist Absicht (gemeinsames Erleben!), kann aber bei großen Gruppen
chaotisch werden. Dann: Moderationsleiste → „🔒 Sperren" und
gemeinsam durch die Stationen führen. PIN steht in `app/config.py` und lässt sich im System-Fenster (Moderationsleiste → 🖥️ System) jederzeit ändern.

**Ablauf mit einer Schulklasse (ca. 15 Schüler:innen, 1–2 Lehrkräfte):**

1. Vorher auf dem eigenen Handy: unten „Moderator:in" antippen, PIN eingeben.
2. **Geführte Phase:** „🔒 Sperren" — nur ihr wechselt die Station,
   alle sehen dasselbe Bild auf ihren Handys. Der Erkennungs-Regler bleibt
   absichtlich für alle frei: damit dürfen sie spielen.
3. **Freie Phase:** „🔓 Freigeben" — die Klasse erkundet selbst. Jeder
   Stationswechsel setzt alle Regler automatisch auf den Startzustand
   zurück, niemand erbt fremde Einstellungen.
4. **Nächste Klasse:** „♻️ Zurücksetzen" (zweimal tippen) — trainierte
   Klassen, Wärmebild und Zähler sind wieder frisch.

---

## Die sechs Stationen und ihre Lernziele

### 🔍 1 · Objekt-Detektiv
**Lernziel:** KI erkennt Muster, versteht aber nichts. Der
Konfidenz-Schieberegler macht den zentralen Zielkonflikt erlebbar:
mehr erkennen = mehr Fehler.
**Moderationsimpuls:** „Stell den Regler ganz nach links — was passiert?
Und wer trägt die Verantwortung, wenn eine echte KI so eingestellt ist?"

### 🧠 2 · Trainiere die KI
**Lernziel:** Maschinen lernen aus Beispielen; einseitige Beispiele →
verzerrte KI (Bias). Bonus: Recht auf Löschung praktisch erlebt.
**Moderationsimpuls:** Absichtlich „schlecht" trainieren lassen (alle
Beispiele aus einem Winkel) und gemeinsam scheitern sehen. Das ist der
Lernmoment!
**Brücke zu Station 1:** Was hier trainiert wird (mindestens zwei
Klassen), erkennt der Objekt-Detektiv danach mit — als goldener Rahmen
„✨ selbst trainiert" in der Bildmitte, neben den Werks-Erkennungen.
Starker Vergleich: das eingefrorene Fabrikmodell gegen euer eigenes
Training. Tipp: eine Klasse „leerer Tisch" mittrainieren macht die
Ergebnisse deutlich sauberer.

### 🛡️ 3 · Privatsphäre-Schild
**Lernziel:** Erkennen ≠ Wiedererkennen; Technik kann Privatsphäre
*schützen*; kein Schutz ist perfekt.
**Moderationsimpuls:** „Dreh dein Gesicht zur Seite. Warum versagt der
Schutz? Wen könnten solche Schwächen im echten Leben treffen?"

### 🗺️ 4 · Die Datenspur
**Lernziel:** Metadaten! Auch ohne Fotos entsteht ein Verhaltensprofil.
Der Überraschungseffekt („das lief die ganze Zeit nebenbei?!") ist der
stärkste Moment des ganzen Exponats — nicht vorher spoilern.
**Moderationsimpuls:** „Was würde diese Karte über euren Klassenraum nach
einer Woche verraten? Und über einen Supermarkt? Wem gehören diese Daten?"

### 🎭 5 · Täusche die KI
**Lernziel:** KI-Systeme haben ausnutzbare Grenzen; gesunde Skepsis
gegenüber „die KI hat es erkannt" als Beweis.
**Moderationsimpuls:** Challenges als Wettbewerb moderieren. Danach:
„Ihr habt die KI in 5 Minuten ausgetrickst. Sollte so ein System allein
entscheiden dürfen, wer ein Gebäude betritt?"

### 🤸 6 · Skelett-Spiegel
**Lernziel:** Posenschätzung erlebbar machen — und begreifen, dass auch
„nur Skelett-Daten" Verhaltensdaten sind (Gang, Bewegungsmuster). Die
körperlich aktivste Station — ideal als Energizer in der Mitte.
**Moderationsimpuls:** Erst den Posen-Parcours als Wettbewerb spielen
lassen. Dann den **Geist-Modus** einschalten: „Ihr seht kein Video mehr —
könnt ihr trotzdem erkennen, wer von euch welches Skelett ist? Woran?
Genau das kann eine Maschine auch."

---

## Abschlussrunde (10–15 Min.)

Die Diskussionskarten (`../cards/cards_de.pdf`, Karten 7–11 — die zweite
Hälfte des Decks) ausdrucken und ausschneiden. Kleingruppen ziehen je eine Karte, 5 Minuten
Diskussionszeit, dann 1-Satz-Fazit pro Gruppe.

Guter Schlusssatz für die Moderation:

> „Ihr habt heute beides gesehen: eine Kamera, die überwachen könnte —
> und dieselbe Kamera, die Gesichter schützt und nichts speichert.
> Welche davon in unserer Welt stehen, entscheiden Menschen. Auch ihr."

---

## Pannenhilfe

Ausführliche Diagnose-Schritte (Kamera, Hailo, Hotspot, Logs) stehen in
der [ANLEITUNG.md](../../ANLEITUNG.md), Abschnitt 9 — hier nur das
Wichtigste für den schnellen Blick:

| Problem | Lösung |
|---|---|
| Seite lädt nicht | Ist das Gerät im richtigen WLAN? `http://10.10.10.1` (http, nicht https!) |
| Stream ruckelt bei vielen Geräten | In `setup/hotspot.sh` `BAND="a"` (5 GHz) setzen; oder in `app/config.py` `STREAM_MAX_FPS` senken |
| „Demo-Modus ohne KI-Chip" im Footer | AI HAT nicht erkannt: einmal neu starten; `hailortcli fw-control identify` prüfen. Das Exponat läuft trotzdem! |
| Farben wirken vertauscht | In `app/config.py` `MODEL_EXPECTS_RGB` umschalten |
| Alles hängt | Strom aus/an — das System startet vollautomatisch neu |
