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
ein zweilagiger Platinenstapel mit winzigem Autofokus-Block statt
Objektivgewinde — und in unserem Aufbau sitzt dahinter zusätzlich ein
**passiver Kühlkörper auf 12-mm-Abstandshaltern** (Platte 4 mm). Der
4-Pin-Stecker verlässt den Stapel **unten mittig nach hinten**. Beides ist
in Rev 2 eingearbeitet: Das Gehäuse ist tiefer, die Rückplatte ist ein
Lamellengitter über dem Kühler mit Durchlass für Stecker und Kabel, und
alle Wände tragen gefaste Kühlrippen.

Dazu kommt der eigentliche Anlass: **das Modul wird im Betrieb spürbar warm.**
Ein dichtes Gehäuse würde das verschlimmern, deshalb ist dieses hier an allen
vier Seiten und auf der Rückseite offen.

## 2 · Was du brauchst

| Teil | Menge | Hinweis |
|---|---|---|
| `elp48-case-body.stl` | 1× | Gehäusekörper |
| `elp48-case-back.stl` | 1× | Rückplatte |
| `elp48-case-shim.stl` | 0–4 Paare | 1-mm-Ausgleichsstreifen, siehe Schritt 5 |
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
| Materialbedarf | ca. 29 cm³, rund 37 g |
| Druckzeit | gut 3 Stunden |

Fertiges Maß: **50 × 50 × 33 mm**, der Stativsockel ragt 9 mm nach unten.
Die einzigen Überhänge sind die Decken der Lüftungsschlitze — kurze Brücken
unter 5 mm, die jeder Drucker schafft; alle Fasen (Rippen, Schlitzenden,
Einlasslöcher, Außenkanten) drucken stützenfrei.

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
4. **Kabel wieder anstecken.** Stecker und Kabel verlassen das Gehäuse
   durch die **Kerbe unten in der Rückplatte** — der Spalt zwischen den
   beiden unteren Andruckbalken ist genau dafür da.
5. **Rückplatte auflegen** und mit den vier M3-Schrauben festziehen. Ihre
   fünf **Andrucksäulen** greifen oben und unten am Kühler vorbei und
   drücken auf die Ränder der hinteren Platine — der Kühler selbst wird
   nie berührt und behält 1 mm Luft zur Platte. *Wackelt das Modul noch?*
   Je einen Ausgleichsstreifen (`shim`) auf den oberen und unteren
   Platinenrand legen (Objektiv nach unten, dann hält die Schwerkraft sie
   fest) und erneut schließen — die Bauhöhen schwanken zwischen
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
Platinen verschraubt sind — das ist gewollt und stabil. Die Gehäusetiefe
wird nicht geraten, sondern **aus der Stapelkette berechnet** — der
Generator druckt bei jedem Lauf eine Passungstabelle und prüft per
Kollisionstest, dass Gehäuse und Modul sich nirgends schneiden:

```
Frontwand · Linsenluft · Platinen · Abstandshalter · Kühler · Luftspalt
   2,6         6,0         9,0        7,0 (folgt)      4,0       1,0
```

Nachgemessen am echten Modul sind die **Gesamttiefe des Moduls
(20 mm inklusive Kühler, `module_depth`)**, der Kühler (4) und der Stecker
(10 × 5, unten mittig); die Ständerhöhe ergibt sich daraus von selbst.
Geschätzt bleiben:

| Parameter | Annahme | Wenn es nicht passt |
|---|---|---|
| `stack_h` | 9 mm Platinen-Sandwich | Wert anpassen — Säulenlänge und Tiefe rechnen sich selbst nach |
| `lens_offset` | 6 mm Luft vor der Platine | erhöhen, wenn der Autofokus-Block anstößt |
| `cooler_w` | 30 mm Kühlerbreite | anpassen; muss schmaler als die Platine bleiben, sonst kommen die Säulen nicht vorbei (der Generator bricht mit Hinweis ab) |

Falls die Säulen nicht sauber auf den Platinenrändern landen, ist eine
Messung fällig: **Vorderkante der vorderen Platine bis Rückkante der
hinteren Platine** — das ist `stack_h`. Ändern, neu generieren; Säulen,
Tiefe und Fenster ziehen automatisch mit.

Alles andere ist mit Toleranz gebaut: 0,4 mm Luft ringsum die Platine, und
die Linsenöffnung ist mit 14 mm innen deutlich größer als nötig, damit der
82°-Bildwinkel auf keinen Fall am Rand abgeschattet wird.

## 7 · Und die Wärme?

Die Kamera wird warm — das ist bei diesem Modul normal und kein Defekt
(ELP nennt 0–70 °C Betriebstemperatur). Das Gehäuse hilft dabei, statt zu
schaden:

* Sechzehn gefaste Lamellenschlitze in den Wänden plus Lamellengitter in
  der Rückplatte direkt über dem Kühler — der Kamineffekt zieht die warme
  Luft am Kühlkörper vorbei nach draußen. Frischluft kommt vorn durch den
  **Ring aus zwölf gefasten Einlassöffnungen** um die Linse herein.
* Kindersicher dimensioniert: Alle Rippen haben 4,8 mm Basis und 3,2 mm
  flache Krone (nichts bricht unter einem Finger), keine Öffnung ist
  breiter als 4,8 mm (kein Kinderfinger passt hinein), und jede Kante —
  Schlitzflanken, Schlitzenden, Löcher, Außenkanten — trägt eine
  45°-Fase.
* Der Sockel hält das Gehäuse von der Tischplatte weg, sodass unten Luft
  nachströmen kann.

**Nicht zusätzlich einpacken.** Kein Stoff darüber, keine Vitrine ohne
Belüftung, keine direkte Sonne.
