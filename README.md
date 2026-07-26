# AI-Lab2Go — a mobile computer-vision & privacy-literacy exhibit framework for Raspberry Pi 5

An out-of-the-box, self-explanatory AI workshop station: the Raspberry Pi 5
(with AI HAT+ 2) runs a live camera feed through real neural networks and serves
an interactive web UI over its own Wi-Fi hotspot. Visitors join with
their own phones or laptops — no app, no internet, no cloud, and (by design)
**no stored images**. Privacy literacy isn't a chapter at the end; it's baked
into every station.

![Six stations. One camera. Your data.](assets/stations/overview_en.png)

## The six stations

| Station | What visitors do | What they learn |
|---|---|---|
| **Object-Detective** | Live YOLO object detection with a confidence slider | Models pattern-match, they don't "understand"; the precision/recall trade-off |
| **Train the AI** | Train a classifier on any two objects in ~1 minute | Learning from examples, bias from one-sided data, right to erasure (one-click delete) |
| **Privacy-Shield** | Faces get pixelated/blurred *at the source*; toggle it, break it | Detection ≠ recognition; tech can protect privacy; no shield is perfect |
| **The Data Trail** | Reveal a motion heatmap collected *while they played* | Metadata: behaviour profiles without a single photo |
| **Fool the AI** | Four challenges to fool the detector | AI limits, adversarial thinking, healthy scepticism |
| **Skeleton Mirror** | Live pose estimation, a pose-challenge parcours, and a "ghost mode" showing skeletons without video | Body data is data: tracking works without images (gait, behaviour) |

<table>
  <tr>
    <td><img src="assets/stations/detektiv_en.png" alt="Object Detective — What does the AI see?"></td>
    <td><img src="assets/stations/trainer_en.png" alt="Train the AI — You are the coach"></td>
  </tr>
  <tr>
    <td><img src="assets/stations/schild_en.png" alt="Privacy Shield — Protection built in"></td>
    <td><img src="assets/stations/spur_en.png" alt="The Data Trail — What cameras collect"></td>
  </tr>
  <tr>
    <td><img src="assets/stations/trick_en.png" alt="Fool the AI — Find its limits"></td>
    <td><img src="assets/stations/pose_en.png" alt="Skeleton Mirror — Play without pictures"></td>
  </tr>
</table>

Everything degrades gracefully: without the AI HAT (or on your laptop) the app
runs in CPU demo mode, so the exhibit never shows a blank screen.

## Hardware

- Raspberry Pi 5 (4 GB is fine, 8 GB nice) + official 27 W USB-C PSU
- Raspberry Pi AI HAT — AI HAT+ 2 (Hailo-10H) as well as AI Kit /
  AI HAT+ (Hailo-8/8L). The installer detects the chip generation and
  installs the matching stack (`hailo-h10-all` vs `hailo-all`); the app
  picks whatever `.hef` model is installed (see `HEF_CANDIDATES` in
  `app/config.py`).
- Camera Module 3 (recommended; autofocus is handled) — or any USB webcam
- microSD ≥ 16 GB, a small tripod/mount, ideally a case with HAT clearance

> Step-by-step guide (assembly, operation, troubleshooting):
> 🇬🇧 [MANUAL.md](MANUAL.md) · 🇩🇪 [ANLEITUNG.md](ANLEITUNG.md)

## Install (on the Pi)

1. Flash **Raspberry Pi OS Bookworm 64-bit** with Raspberry Pi Imager.
2. Copy this folder onto the Pi (USB stick, `scp`, or git), then:

```bash
bash setup/install.sh
sudo reboot
```

3. After reboot the exhibit serves on port 80 and starts on every boot
   (`systemctl status ki-werkstatt`).
4. Start the student hotspot and print the poster:

```bash
bash setup/hotspot.sh
python3 setup/make_poster.py
```

Visitors join Wi-Fi **KI-Werkstatt** and open **http://10.42.0.1**. Change
SSID/password in `setup/hotspot.sh` (and re-run the poster script).

## Try it on your laptop first (no Pi needed)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r dev/requirements-dev.txt
python3 app/main.py --source webcam     # or --source fake for a test pattern
```

Then open http://localhost:8080. `--source fake` needs no camera at all and
even emits fake detections, so every station and the whole UI can be tested.

## Deploying changes

```bash
bash setup/deploy.sh              # or: bash setup/deploy.sh dan@10.42.0.1
```

Syncs the project, installs it to `/opt/ki-werkstatt`, restarts the service
and prints the startup status lines (camera, AI chip, pose model, face guard).

## Station advertising cards

[assets/stations/](assets/stations/) holds ready-made promo images
(1600×900 PNG) for every station in German and English —
`<station>_{de,en}.png` plus an `overview_{de,en}.png` banner. Use them in
the manuals, on social media or in print. They are generated (macOS only,
uses system fonts) by:

```bash
python3 setup/make_station_cards.py
```

Edit titles/taglines/scenes there and re-run; the SKILL logo is picked up
from `app/static/logo.png` automatically.

## Branding

The header, favicon and poster use the SKILL logo from `app/static/`:

- `logo.png` — full lockup, placed unaltered (transparent background) in the
  header. Note the dark purple sits at roughly 1.3:1 contrast against the
  dark UI background — deliberate, brand-faithful choice; a lighter
  dark-mode variant of the file can be dropped in without code changes.
- `logo-icon.png` — square 256 px icon mark on white, used as favicon and
  home-screen icon (an opaque square is what iOS/Android expect there)

To rebrand, replace both files (keep the names and roughly the aspect
ratios: ~3.9:1 and 1:1) and re-run `python3 setup/make_poster.py` — the
poster embeds the logo as a data URI so it stays a single portable file.
Brand colours in use: `#400b67` and `#c32683` (poster headline gradient).

## Configuration

All the knobs live in [app/config.py](app/config.py): stream resolution/fps
(hotspot bandwidth), confidence default, samples needed for the teachable
machine, the moderator PIN (`ADMIN_PIN`, default `2468` — change it!), and
the global face-anonymisation default.

Moderator functions (lock stations, reset everything) are behind the
"Moderator:in" link in the page footer + PIN.

## Workshop materials (German)

- [workshop/leitfaden.md](workshop/leitfaden.md) — facilitator guide: setup
  checklist, prop box, 45/90-min formats, per-station learning goals,
  troubleshooting
- [workshop/stationskarten.md](workshop/stationskarten.md) — printable
  station cards incl. rally tasks
- [workshop/diskussionskarten-privatsphaere.md](workshop/diskussionskarten-privatsphaere.md)
  — discussion cards for the closing round

## Architecture

```
app/main.py        entry point & CLI
app/camera.py      frame sources: Pi camera / USB webcam / synthetic test pattern
app/vision.py      Hailo YOLO detection, face guard, motion heatmap, teachable kNN
app/stations.py    the pipeline: one camera thread → overlays → JPEG + state dict
app/webserver.py   Flask: MJPEG stream (/stream.mjpg) + JSON API (/api/*)
app/templates+static  the bilingual single-page UI (offline, no CDNs)
```

The UI is bilingual: German is the default in the markup (works without
JS), English lives in `app/static/i18n.js`; a DE/EN toggle in the header
switches per device (localStorage). To edit copy: change the German in
`index.html` and its English twin under the same `data-i18n` key in
`i18n.js`. Never place an element with an `id` inside a `data-i18n` block —
the language swap replaces that block's HTML wholesale.

One processing thread serves every viewer the same stream — visitors control
the stations *together* (that's a feature: shared experience, and a moderator
lock exists for rowdy groups).

Privacy by architecture: frames live only in RAM; the teachable machine
stores HOG feature vectors, never images; the heatmap stores a 160×90 motion
counter. There is nothing *to* leak.

## License & author

MIT — see [LICENSE](LICENSE).

© 2026 **Dan Verständig** · <verstaendig@c3s.uni-frankfurt.de> ·
[medienbildung.team](https://medienbildung.team) ·
[aiwarenesslab.io](https://aiwarenesslab.io)

(The bundled YuNet face-detection model in `app/models/` comes from the
OpenCV Zoo under its own MIT license; the SKILL logo remains the property
of its owner and is not covered by the MIT license.)

## Extending it

- Swap in other `.hef` models from the Hailo model zoo (pose, segmentation)
  via `--hef` or `HEF_CANDIDATES`
- Add a station: one mode in `app/stations.py`, one `<section>` in
  `index.html` — the tile/panel wiring is generic
- Add a language: extend the dictionaries in `app/static/i18n.js` and add a
  button to the `.langswitch` group in `index.html`; video-overlay texts
  (shared by all viewers) live in `stations.py`
