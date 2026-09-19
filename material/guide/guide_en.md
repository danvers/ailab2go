# AI-Lab2Go · Facilitator Guide

A hands-on interactive exhibit about **machine vision** and **privacy
literacy** — for school classes, maker events and open events with a mixed
audience. Participants use their own phones or laptops; there is no app to
install.

---

## The idea in one sentence

> Visitors and participants play with a real AI camera, come to understand
> along the way *how* machines learn and see — and experience first-hand
> why privacy isn't a matter of bans and prohibitions, but something we
> can shape.

**The thread running through it all:** the same technology can surveil *or*
protect. What matters is how we build it and how we use it.

---

## Setup checklist (15 minutes)

- [ ] Set up the Raspberry Pi 5 with AI HAT + camera, point the camera at
      the "play area" (2–4 m distance is ideal)
- [ ] **Important:** put up a clearly visible sign: *"A camera
      installation is running here. No images are stored."* — we practise
      the transparency we talk about!
- [ ] Power the Pi on — the exhibit starts by itself
- [ ] Check the hotspot: join the Wi-Fi `KI-Werkstatt` with your own phone
      and open `http://10.10.10.1`
- [ ] Put up the poster with the QR codes (`../poster/poster_en.pdf`)
- [ ] Get the prop box ready (see below)
- [ ] Optional: print the station cards and lay them out
      (`../cards/cards_en.pdf`, station cards 1–6)

### The prop box (this is what makes the difference!)

The built-in model knows exactly the 80 everyday classes of the COCO
dataset — sort the box accordingly, on purpose:

- **Works reliably (station 1):** mug, banana, apple, orange, bottle,
  book, teddy bear, scissors, ball, umbrella, phone, laptop, clock,
  spoon.
- **Fails on purpose** (a toy dinosaur, hammer/screwdriver, any
  vegetable other than broccoli or carrot): don't toss these! Train
  them at station 2 first — the Detective then recognises them as
  "✨ self-trained" — and at station 5 they are your best ammunition.
- Sunglasses, a hat, a scarf → for stations 3 and 5.
- A phone with photos of animals on it → the "Ghosts" challenge in
  station 5.

---

## Formats

| Format | Length | How it runs |
|---|---|---|
| **Open exhibit** | any | Self-explanatory, runs on its own. Look in every 30–45 min and hit "♻️ Reset everything" (Moderator bar) if needed. |
| **Compact workshop** | 45 min | 10 min intro → 25 min free exploring in groups → 10 min closing round with the discussion cards |
| **Extended workshop** | 90 min | Like the compact one, plus: 20 min station rally with tasks (station cards) and 15 min small-group discussion |

**Tip for groups:** everyone sees the same camera picture and steers it
together. That is deliberate (shared experience!), but it can get chaotic
with big groups. Then use the Moderator bar → "🔒 Lock stations" and walk
through the stations together. The PIN is in `app/config.py`.

**Running a school class (about 15 students, 1–2 teachers):**

1. Beforehand, on your own phone: tap "Moderator" in the footer, enter the PIN.
2. **Guided phase:** "🔒 Lock stations" — only you switch stations, and
   everyone sees the same picture on their phones. The detection slider
   deliberately stays free for everyone: that one is for playing.
3. **Free phase:** "🔓 Unlock stations" — the class explores on its own. Every station
   switch automatically resets all controls to their starting values, so
   nobody inherits someone else's settings.
4. **Next class:** "♻️ Reset everything" (tap twice) — trained classes,
   heatmap and counters start fresh again.

---

## The six stations and their learning goals

### 🔍 1 · Object Detective
**Learning goal:** AI spots patterns but understands nothing. The
confidence slider makes the central trade-off tangible: spot more = get
more wrong.
**Facilitation prompt:** "Push the slider all the way to the left — what
happens? And who carries the responsibility when a real AI is tuned like
that?"

### 🧠 2 · Train the AI
**Learning goal:** machines learn from examples; one-sided examples →
skewed AI (bias). Bonus: the right to erasure, experienced first-hand.
**Facilitation prompt:** have them train it "badly" on purpose (every
example from the same angle) and watch it fail together. That is the
learning moment!
**Bridge to station 1:** whatever is trained here (at least two
classes) joins the Object Detective afterwards — a golden frame marked
"✨ self-trained" in the centre of the picture, right next to the
factory detections. A strong comparison: the frozen factory model
versus your own training. Tip: also training an "empty table" class
makes the results noticeably cleaner.

### 🛡️ 3 · Privacy Shield
**Learning goal:** detection ≠ recognition; technology can *protect*
privacy; no protection is perfect.
**Facilitation prompt:** "Turn your face to the side. Why does the
protection fail? Who might be hurt by weaknesses like that in real life?"

### 🗺️ 4 · The Data Trail
**Learning goal:** metadata! A behaviour profile builds up even without
photos. The surprise ("that was running the whole time in the
background?!") is the strongest moment of the entire exhibit — don't spoil
it beforehand.
**Facilitation prompt:** "What would this map reveal about your classroom
after a week? And about a supermarket? Who owns this data?"

### 🎭 5 · Fool the AI
**Learning goal:** AI systems have limits that can be exploited; healthy
scepticism towards "the AI detected it" as proof.
**Facilitation prompt:** run the challenges as a competition. Afterwards:
"You outsmarted the AI in 5 minutes. Should a system like that be allowed
to decide on its own who gets into a building?"

### 🤸 6 · Skeleton Mirror
**Learning goal:** make pose estimation tangible — and grasp that even
"just skeleton data" is behavioural data (gait, movement patterns). The
most physically active station — perfect as an energizer in the middle.
**Facilitation prompt:** play the pose course as a competition first. Then
switch on **Ghost mode**: "There's no video any more — can you still tell
which skeleton is which of you? How? A machine can do exactly the same."

---

## Closing round (10–15 min)

Print the discussion cards (`../cards/cards_en.pdf`, cards 7–11, the second
half of the deck) and cut them out. Each small group draws one
card, 5 minutes of discussion time, then one sentence of takeaway per
group.

A good closing line for the facilitator:

> "Today you saw both: a camera that could surveil — and the very same
> camera protecting faces and storing nothing. Which of the two end up
> standing in our world is decided by people. By you too."

---

## Troubleshooting

Detailed diagnostic steps (camera, Hailo, hotspot, logs) are in
[MANUAL.md](../../MANUAL.md), section 9 — here are just the essentials for
a quick glance:

| Problem | Fix |
|---|---|
| Page doesn't load | Is the device on the right Wi-Fi? `http://10.10.10.1` (http, not https!) |
| Stream stutters with many devices | Set `BAND="a"` (5 GHz) in `setup/hotspot.sh`; or lower `STREAM_MAX_FPS` in `app/config.py` |
| "Demo mode without AI chip" in the footer | AI HAT not detected: reboot once; check with `hailortcli fw-control identify`. The exhibit still runs! |
| Colours look swapped | Flip `MODEL_EXPECTS_RGB` in `app/config.py` |
| Everything is frozen | Power off/on — the system restarts fully automatically |