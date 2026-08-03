# Kameragehäuse für das ELP 48MP Autofokus-Modul

3D-Druck-Gehäuse für die USB-Kamera der KI-Werkstatt
(**ELP-USB48MP01-AF70**, 38 × 38 mm Double-Deck-Platine).

| ![vorne](stl/preview-front.png) | ![hinten](stl/preview-back.png) | ![zerlegt](stl/preview-exploded.png) |
|---|---|---|
| vorne | hinten | zerlegt |

Fertige Druckdateien liegen in [`stl/`](stl/). Wer Maße ändern will, bearbeitet
[`case_elp48mp.py`](case_elp48mp.py) und ruft auf:

```bash
bash setup/tools.sh case
```

---

## 1 · Warum ein eigenes Gehäuse?

Für ältere ELP-Module gibt es viele fertige Gehäuse auf Thingiverse und
Printables — aber **keines passt auf dieses Modul**. Die vorhandenen Modelle
sind für einlagige Platinen mit M12-Objektivtubus gebaut; das 48-MP-Modul ist
ein zweilagiger Platinenstapel (rund 13 mm dick) mit einem winzigen
Autofokus-Block statt eines Objektivgewindes.

Dazu kommt der eigentliche Anlass: **das Modul wird im Betrieb spürbar warm.**
Ein dichtes Gehäuse würde das verschlimmern, deshalb ist dieses hier an allen
vier Seiten und auf der Rückseite offen.

## 2 · Was du brauchst

| Teil | Menge | Hinweis |
|---|---|---|
| `elp48-case-body.stl` | 1× | Gehäusekörper |
| `elp48-case-back.stl` | 1× | Rückplatte |
| `elp48-case-shim.stl` | 0–4× | 1-mm-Ausgleichsrahmen, siehe Schritt 5 |
| Schrauben M3 × 12 mm, selbstschneidend | 4× | Blech- oder Kunststoffschrauben; Holzschrauben gehen auch |
| Sechskantmutter ¼"-20 (UNC) | 1× | nur wenn du das Stativgewinde nutzen willst |

**Filament: PETG, nicht PLA.** PLA wird ab etwa 55 °C weich — genau der
Bereich, in den sich ein Gehäuse um eine warme Kamera in einem sonnigen
Ausstellungsraum bewegt. PETG hält rund 75 °C aus. ASA oder ABS gehen auch.

## 3 · Drucken

| Einstellung | Wert |
|---|---|
| Lage | Gehäusekörper mit der **Objektivseite nach unten** aufs Bett, Rückplatte flach |
| Stützstruktur | **keine** — dafür ist alles konstruiert |
| Schichthöhe | 0,2 mm |
| Perimeter | 3 |
| Füllung | 20 % |
| Materialbedarf | ca. 36 cm³, rund 46 g |
| Druckzeit | ungefähr 4 Stunden |

Fertiges Maß: **50 × 50 × 31 mm**, der Stativsockel ragt 9 mm nach unten.
Die einzigen Überhänge sind die Decken der Lüftungsschlitze — kurze Brücken
von 6,5 mm, die jeder Drucker schafft.

## 4 · Zusammenbau

1. **Mutter einsetzen** (nur bei Stativnutzung): Die ¼"-Mutter von der
   **Gehäuserückseite** in den Kanal im Sockel schieben — Ecke nach oben,
   so wie der Sechskant unten geformt ist — bis sie in ihrer Tasche
   einrastet. Sie kann dort nicht mehr herausfallen, sobald die Rückplatte
   sitzt.
2. **Kabel abziehen.** Der Stecker sitzt auf der unteren Platine und lässt
   sich abnehmen — das macht den Einbau leichter.
3. **Platine einlegen**, Objektiv voran. Sie fällt in den Schacht und liegt
   vorn auf vier Ecknasen auf.
4. **Kabel wieder anstecken** und durch einen der Lüftungsschlitze
   nach außen führen. Alle Schlitze sind breit genug für den Stecker,
   du kannst also die Seite wählen, die zum Aufbau passt.
5. **Rückplatte auflegen** und mit den vier M3-Schrauben festziehen.
   *Wackelt die Platine noch?* Rückplatte abnehmen, einen Ausgleichsrahmen
   (`shim`) hinter die Platine legen, erneut schließen. Bis zu vier Rahmen
   passen — die Bauhöhe des Platinenstapels schwankt zwischen
   Produktionsserien.
6. **Bild prüfen.** Steht es auf dem Kopf, die Platine um 180° gedreht
   einlegen. Die Software dreht das Bild nicht.

## 5 · Montage

* **Stativ / Klemme:** ¼"-Gewinde im Sockel — passt auf jedes Fotostativ,
  jeden Magic Arm und jede Tischklemme.
* **Feste Wand:** Der Sockel lässt sich auch direkt anschrauben; alternativ
  hält doppelseitiges Klebeband auf der Rückplatte.

## 6 · Maße, und was daran unsicher ist

Der Hersteller veröffentlicht für dieses Modul nur die Platinengröße
(„Double-deck, 38 mm × 38 mm"). **Das Lochbild der Befestigungsbohrungen
nennt er nirgends** — deshalb benutzt dieses Gehäuse es gar nicht. Die
Platine wird stattdessen wie eine Fensterscheibe gehalten:

```
Frontwand ─ 4 Ecknasen ─ [Platinenstapel] ─ Andruckrahmen ─ Rückplatte
```

Die Ecknasen landen dabei auf den Schraubenköpfen, mit denen die beiden
Platinen verschraubt sind — das ist gewollt und stabil. Zwei Maße sind
geschätzt und in `case_elp48mp.py` oben eingestellt:

| Parameter | Annahme | Wenn es nicht passt |
|---|---|---|
| `stack_h` | 13 mm Stapelhöhe | Ausgleichsrahmen zulegen (Schritt 4) |
| `lens_offset` | 8 mm Luft vor der Platine | Wert erhöhen, wenn der Autofokus-Block anstößt |

Alles andere ist mit Toleranz gebaut: 0,4 mm Luft ringsum die Platine, und
die Linsenöffnung ist mit 14 mm innen deutlich größer als nötig, damit der
82°-Bildwinkel auf keinen Fall am Rand abgeschattet wird.

## 7 · Und die Wärme?

Die Kamera wird warm — das ist bei diesem Modul normal und kein Defekt
(ELP nennt 0–70 °C Betriebstemperatur). Das Gehäuse hilft dabei, statt zu
schaden:

* Zwölf Lüftungsschlitze plus offene Rückplatte, rund ein Drittel der
  Wandfläche.
* Der Sockel hält das Gehäuse von der Tischplatte weg, sodass unten Luft
  nachströmen kann.

**Nicht zusätzlich einpacken.** Kein Stoff darüber, keine Vitrine ohne
Belüftung, keine direkte Sonne.
