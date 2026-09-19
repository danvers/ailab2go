"""The frame pipeline: one camera, one active station mode, many viewers.

A single background thread reads frames, runs the active station's
processing, draws overlays and publishes JPEG bytes + a state dict that the
web clients poll.
"""

import glob
import logging
import subprocess
import threading
import time

import cv2
import numpy as np

import config
import vision
from labels_de import class_info, de_ascii

MODES = ("start", "detektiv", "trainer", "schild", "spur", "trick", "pose")

FONT = cv2.FONT_HERSHEY_SIMPLEX

# COCO-17 keypoint indices: 0 nose, 5/6 shoulders, 7/8 elbows, 9/10 wrists,
# 11/12 hips, 13/14 knees, 15/16 ankles
SKELETON_BONES = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12),
                  (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
                  (0, 5), (0, 6)]
SKELETON_COLORS = [(255, 200, 80), (120, 255, 120), (80, 160, 255),
                   (220, 120, 255), (100, 240, 255), (160, 160, 255)]


def _kpt_ok(kpts, *idx):
    import config as _c
    return all(kpts[i, 2] >= _c.POSE_KPT_THRESHOLD for i in idx)


def _shoulder_width(kpts):
    return abs(kpts[5, 0] - kpts[6, 0]) + 1e-6


def _ch_one_hand(kpts):
    return _kpt_ok(kpts, 0) and (
        (_kpt_ok(kpts, 9) and kpts[9, 1] < kpts[0, 1]) or
        (_kpt_ok(kpts, 10) and kpts[10, 1] < kpts[0, 1]))


def _ch_both_hands(kpts):
    return (_kpt_ok(kpts, 0, 9, 10)
            and kpts[9, 1] < kpts[0, 1] and kpts[10, 1] < kpts[0, 1])


def _ch_hands_together(kpts):
    if not _kpt_ok(kpts, 5, 6, 9, 10):
        return False
    sw = _shoulder_width(kpts)
    dist = np.hypot(kpts[9, 0] - kpts[10, 0], kpts[9, 1] - kpts[10, 1])
    below_shoulders = min(kpts[9, 1], kpts[10, 1]) > min(kpts[5, 1], kpts[6, 1])
    return dist < 0.5 * sw and below_shoulders


def _ch_t_pose(kpts):
    if not _kpt_ok(kpts, 5, 6, 9, 10):
        return False
    sw = _shoulder_width(kpts)
    level = (abs(kpts[9, 1] - kpts[5, 1]) < 0.6 * sw
             and abs(kpts[10, 1] - kpts[6, 1]) < 0.6 * sw)
    wide = abs(kpts[9, 0] - kpts[10, 0]) > 2.1 * sw
    return level and wide


# NOTE bilingual: the German text here is what the server publishes (and the
# client's fallback). The web UI re-renders each challenge BY POSITION from
# the two "poseCh" lists in app/static/i18n.js (DE + EN) — when you edit,
# reorder or extend this list, update BOTH lists there to match.
POSE_CHALLENGES = [
    ("👋", "Heb eine Hand über den Kopf!", _ch_one_hand),
    ("🙌", "Beide Hände hoch!", _ch_both_hands),
    ("🤲", "Beide Hände vor der Brust zusammen!", _ch_hands_together),
    ("✈️", "Mach ein T — Arme waagerecht zur Seite!", _ch_t_pose),
]


def _class_color(class_id):
    """Stable, vivid BGR colour per class (golden-angle hue walk)."""
    hue = int((class_id * 47) % 180)
    hsv = np.uint8([[[hue, 200, 255]]])
    b, g, r = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
    return int(b), int(g), int(r)


def _label(frame, text, x, y, color):
    (tw, th), _ = cv2.getTextSize(text, FONT, 0.5, 1)
    y = max(th + 6, y)
    cv2.rectangle(frame, (x, y - th - 6), (x + tw + 8, y + 4), color, -1)
    cv2.putText(frame, text, (x + 4, y - 2), FONT, 0.5, (10, 10, 10), 1, cv2.LINE_AA)


class Pipeline:
    def __init__(self, source, detector, detector_status,
                 pose=None, pose_status=""):
        self.source = source
        self.detector = detector
        self.detector_status = detector_status
        self.pose = pose
        self.pose_status = pose_status
        self._ch_idx = 0
        self._ch_done = 0
        self._ch_hold_since = None
        self._ch_flash_until = 0.0
        self._pose_count = 0

        self.faces = vision.FaceGuard()
        self.heatmap = vision.MotionHeatmap()
        self.teach = vision.Teachable()
        self.det_smooth = vision.DetectionSmoother()

        self.mode = config.DEFAULT_MODE
        self.reset_params()
        self.locked = False
        # Room language: the beamer wall follows the LAST language toggle
        # anyone clicked in the station UI. Deliberately not reset on
        # station switches — a class works in one language throughout.
        self.lang = "de"

        self.started = time.time()
        self.running = True
        self.fps = 0.0
        self.stream_clients = 0

        # --- exhibition counters (RAM only, reset with the process) ---------
        # These exist to make the *invisible* visible on the projector wall:
        # how much a comparable cloud camera would have uploaded by now, how
        # often faces were shielded, how much of the room has been mapped.
        self.frames_total = 0
        self.published_total = 0      # frames actually handed to viewers —
                                      # the watchdog's liveness metric
        self.cloud_bytes = 0          # sum of encoded frame sizes
        self.object_events = 0        # object appeared after being absent
        self.classes_seen = set()
        self.faces_max = 0
        self._objects_present = set()
        self.last_interaction = time.monotonic()
        self._attract_since = None
        self._attract_next = 0.0

        # Video/AI decoupling: publishes run at PROCESS_MAX_FPS, the
        # accelerator at INFER_MAX_FPS. Between AI passes these caches are
        # drawn onto every fresh camera frame — smooth video, same heat.
        self._last_infer = 0.0
        self._last_dets = []
        self._last_persons = []
        self._own_cache = None

        self._throttled = None
        self._sys_cache = {}
        self._sys_ts = 0.0

        self.jpeg = None
        self.state = {}
        self.frame_ready = threading.Condition()

        self._thread = threading.Thread(target=self._run, daemon=True)

    # -- public control (called from Flask request threads) -----------------

    def start(self):
        self._thread.start()
        threading.Thread(target=self._throttle_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def reset_params(self):
        """The knobs every station starts from. Mode and settings are ROOM
        state shared by all phones, so a station switch wipes the previous
        group's slider positions — each station begins at the same,
        predictable defaults (and the face shield re-arms: safe direction)."""
        self.threshold = config.DETECT_THRESHOLD_DEFAULT
        self.privacy_on = config.FACE_GUARD_GLOBAL_DEFAULT
        self.privacy_style = "pixel"
        self.pose_ghost = False

    def set_mode(self, mode):
        if mode in MODES:
            if mode != self.mode:
                keep_privacy = self.privacy_on
                self.mode = mode
                self.reset_params()
                if mode == "pose":
                    # The skeleton mirror honours the CURRENT shield choice
                    # instead of re-arming it: whoever switched the shield
                    # off wants unobstructed skeletons, and pixel blobs on
                    # top of the stick figures ruin the station. Every
                    # other station re-arms the shield as usual.
                    self.privacy_on = keep_privacy
                self._last_infer = 0.0   # next pass infers immediately
            return True
        return False

    def touch(self):
        """Any visitor interaction — pauses the attract rotation."""
        self.last_interaction = time.monotonic()
        self._attract_since = None

    @property
    def attract(self):
        """True while nobody has touched anything for a while: the exhibit
        tours itself so passers-by always see something happening."""
        return (config.EXHIBIT_AUTOROTATE and not self.locked and
                time.monotonic() - self.last_interaction
                > config.EXHIBIT_IDLE_AFTER)

    def _attract_step(self):
        now = time.monotonic()
        if not self.attract:
            return
        if self._attract_since is None:
            self._attract_since = now
            self._attract_next = now              # switch immediately
        if now >= self._attract_next:
            tour = [m for m in config.EXHIBIT_TOUR if m in MODES]
            if tour:
                try:
                    nxt = tour[(tour.index(self.mode) + 1) % len(tour)]
                except ValueError:
                    nxt = tour[0]
                self.set_mode(nxt)   # through the chokepoint: resets knobs
            self._attract_next = now + config.EXHIBIT_ROTATE_EVERY

    # -- main loop ----------------------------------------------------------

    def _run(self):
        log = logging.getLogger("pipeline")
        last_error_log = 0.0
        set_standby = getattr(self.source, "set_standby", None)
        viewers_gone_since = None     # when the LAST viewer disconnected
        self._last_full = 0.0         # last full processing pass
        while self.running:
            t0 = time.monotonic()
            # Camera standby: nobody connected for a while -> power down the
            # camera (it runs hot); the first viewer wakes it in ~1-2 s.
            # The timer starts when the last viewer LEAVES — a solitary
            # watcher whose phone briefly locks must not trigger an instant
            # sleep/wake churn.
            if set_standby and config.CAMERA_STANDBY_AFTER > 0:
                now = time.monotonic()
                if self.stream_clients > 0:
                    viewers_gone_since = None
                elif viewers_gone_since is None:
                    viewers_gone_since = now
                set_standby(
                    viewers_gone_since is not None and
                    now - viewers_gone_since > config.CAMERA_STANDBY_AFTER and
                    now - self.last_interaction > config.CAMERA_STANDBY_AFTER)
            try:
                frame = self.source.read()
            except Exception:
                time.sleep(0.5)
                continue

            # Thermal pacing: the camera is drained at its native rate
            # (above), but the expensive part — AI inference, overlays,
            # JPEG — runs at most PROCESS_MAX_FPS. With no viewer at all
            # it drops to a ~3 fps heartbeat: enough to keep the watchdog
            # fed and hand the first joiner a fresh frame, while the Pi
            # and the Hailo cool off between visitors.
            now = time.monotonic()
            min_gap = 1.0 / (3 if self.stream_clients == 0
                             else config.PROCESS_MAX_FPS)
            if now - self._last_full < min_gap:
                # skipped frame: still pace the loop (a standby placeholder
                # read returns instantly — without this sleep the skip path
                # would busy-spin at 100 % CPU, the opposite of cooling)
                time.sleep(max(0.0, 1 / 30 - (now - t0)))
                continue
            # honest fps: rate of full passes, not of camera reads — this is
            # the number /system shows while debugging a warm exhibit
            self.fps = 0.9 * self.fps + 0.1 * (
                1.0 / max(now - self._last_full, 1e-3))
            self._last_full = now

            try:
                self._process(frame)
            except Exception:
                # One bad frame must never kill the exhibit for everyone —
                # log (rate-limited), drop the frame, keep streaming.
                if time.monotonic() - last_error_log > 10:
                    last_error_log = time.monotonic()
                    log.exception("Frame processing failed — frame dropped")

            time.sleep(max(0.0, 1 / 30 - (time.monotonic() - t0)))

    def _process(self, frame):
            self.last_frame = frame.copy()  # clean copy for teach_capture
            self._attract_step()            # self-touring while nobody plays
            mode = self.mode  # snapshot: mode may change mid-frame

            now = time.monotonic()
            infer = now - self._last_infer >= 1.0 / config.INFER_MAX_FPS
            if infer:
                self._last_infer = now

            # Background bookkeeping that runs in *every* mode — on purpose:
            # the Datenspur station later reveals what was collected while
            # people were busy playing (exactly how real surveillance works).
            # Placeholder frames (camera unplugged) are excluded: the "no
            # camera" text must not become heatmap blobs or HOG samples.
            self.camera_live = getattr(self.source, "connected", True)
            if self.camera_live:
                if infer:
                    # analysis belongs on the AI clock: face boxes and the
                    # heatmap are cached state, redrawn/applied every frame.
                    # Running yunet per VIDEO frame was what kept the loop
                    # from reaching PROCESS_MAX_FPS.
                    self.heatmap.update(frame)
                    self.faces.update(frame)
                    self.faces_max = max(self.faces_max,
                                         len(self.faces.boxes))
                    self.frames_total += 1
            else:
                # placeholder phase: stale face boxes must not linger for
                # hours (they would pixelate the sleep frame and report
                # last night's visitors as "faces right now")
                self.faces.clear()

            detections = []
            self._own_hit = None
            if mode in ("detektiv", "trick"):
                if infer:
                    # steadied, not raw: see vision.DetectionSmoother. On
                    # placeholder frames the accelerator gets the night off.
                    raw = self._detect(frame) if self.camera_live else []
                    self._last_dets = self.det_smooth.update(raw,
                                                             self.threshold)
                detections = self._last_dets
                self._draw_detections(frame, detections)
                if mode == "detektiv" and self.camera_live:
                    self._own_hit = self._own_frame(frame, infer)
            elif mode == "trainer":
                prediction = (self._trainer_frame(frame, infer)
                              if self.camera_live else None)
            elif mode == "spur":
                frame = self.heatmap.render(frame)
            elif mode == "pose":
                frame = (self._pose_frame(frame, infer)
                         if self.camera_live else frame)
            elif mode == "start" and self.camera_live:
                # Frosted glass until someone picks a station: shapes stay
                # (the room is visibly live), details vanish. Down/up-scale
                # is a near-free box blur. The welcome text stays a crisp
                # client-side overlay — never burned into the frame; the
                # standby/placeholder image is left readable.
                h, w = frame.shape[:2]
                frame = cv2.resize(cv2.resize(frame, (64, 36),
                                              interpolation=cv2.INTER_AREA),
                                   (w, h), interpolation=cv2.INTER_LINEAR)

            # Face shield: global best-effort anonymisation in every mode.
            # Only skipped in *working* ghost mode, where the frame is fully
            # synthetic (pixelating the grid would leak head positions).
            # Without a pose model _pose_frame returns RAW camera video —
            # anonymisation must stay on there.
            ghost_synthetic = (mode == "pose" and self.pose_ghost
                               and self.pose is not None)
            if self.privacy_on and not ghost_synthetic:
                frame = self.faces.apply(frame, self.privacy_style)
            elif mode == "schild":
                # Shield switched off: make the exposure visible.
                for (x, y, w, h) in self.faces.boxes:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 60, 230), 2)
                    _label(frame, "ungeschuetzt!", x, y - 4, (60, 60, 230))

            # Which object classes are on screen right now? Counting the
            # *appearances* (not every frame) gives the wall an honest
            # "recognitions so far" number.
            present = {c for c, _, _ in detections}   # already steady-filtered
            new = present - self._objects_present
            self.object_events += len(new)
            self.classes_seen |= present
            self._objects_present = present

            ok, buf = cv2.imencode(".jpg", frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, config.JPEG_QUALITY])
            if ok:
                # what a cloud camera would have shipped off by now — only
                # real footage counts; a night of standby placeholders must
                # not fabricate gigabytes of fictitious surveillance
                if self.camera_live:
                    self.cloud_bytes += len(buf)
                with self.frame_ready:
                    self.jpeg = buf.tobytes()
                    self.published_total += 1
                    self.frame_ready.notify_all()

            self._publish_state(mode, detections)

    # -- per-station helpers -------------------------------------------------

    def _detect(self, frame):
        if self.detector is not None:
            try:
                return self.detector.detect(frame)
            except Exception:
                return []
        fake = getattr(self.source, "fake_detections", [])
        if fake:
            return fake
        # CPU fallback: at least report faces as persons so the station
        # is not dead without an AI HAT.
        h, w = frame.shape[:2]
        return [(0, 0.8, (x / w, y / h, (x + fw) / w, (y + fh) / h))
                for (x, y, fw, fh) in self.faces.boxes]

    def _draw_detections(self, frame, detections):
        # No threshold check here: the smoother already applied it, WITH
        # hysteresis — re-filtering would cut objects in their hold phase
        # and bring the flicker back.
        h, w = frame.shape[:2]
        for class_id, conf, (x0, y0, x1, y1) in detections:
            color = _class_color(class_id)
            p0 = (int(x0 * w), int(y0 * h))
            p1 = (int(x1 * w), int(y1 * h))
            cv2.rectangle(frame, p0, p1, color, 2)
            _, name_de, _ = class_info(class_id)
            _label(frame, f"{de_ascii(name_de)} {int(conf * 100)}%",
                   p0[0], p0[1] - 4, color)

    def _own_frame(self, frame, infer):
        """Station-2 fusion: the visitor-trained classifier joins the hunt.
        The factory model (frozen COCO) and the exhibit's own training show
        up side by side — train your dino at station 2, and the Detektiv
        recognises it here, clearly marked as self-trained. Classifier, not
        detector: it looks only inside the centre guide box, the exact crop
        the station-2 samples were taken with. Classification runs on the
        AI clock; every frame just redraws the cached hit."""
        if len(self.teach.trained_slots) < 2:
            self._own_cache = None
            return None
        x0, y0, x1, y1 = self.teach.guide_box(frame)
        cv2.rectangle(frame, (x0, y0), (x1, y1), (150, 150, 150), 1)
        if infer:
            self._own_cache = None
            pred = self.teach.predict(frame)
            if pred is not None:
                slot, conf = pred
                if conf >= 0.7:           # only confident hits leave the box
                    name = self.teach.names[slot]
                    self._own_cache = {"emoji": "\u2728", "name": name,
                                       "name_en": name,
                                       "pct": int(conf * 100)}
        hit = self._own_cache
        if hit:
            gold = (60, 200, 255)
            cv2.rectangle(frame, (x0, y0), (x1, y1), gold, 2)
            _label(frame,
                   f"{de_ascii(hit['name'])} {hit['pct']}% - selbst trainiert",
                   x0, y0 - 4, gold)
        return hit

    def _trainer_frame(self, frame, infer):
        x0, y0, x1, y1 = self.teach.guide_box(frame)
        cv2.rectangle(frame, (x0, y0), (x1, y1), (255, 200, 80), 2)
        prediction = (self.teach.predict(frame) if infer
                      else getattr(self, "_last_prediction", None))
        if prediction is not None:
            slot, conf = prediction
            name = self.teach.names[slot]
            text = f"{de_ascii(name)}  {int(conf * 100)}%"
            (tw, _), _ = cv2.getTextSize(text, FONT, 0.9, 2)
            x = (frame.shape[1] - tw) // 2
            cv2.rectangle(frame, (x - 10, frame.shape[0] - 46),
                          (x + tw + 10, frame.shape[0] - 10), (30, 30, 30), -1)
            cv2.putText(frame, text, (x, frame.shape[0] - 20), FONT, 0.9,
                        (120, 255, 120), 2, cv2.LINE_AA)
        self._last_prediction = prediction
        return prediction

    def _pose_frame(self, frame, infer):
        h, w = frame.shape[:2]
        if self.pose is None:
            cv2.putText(frame, "Pose-Modell nicht verfuegbar", (14, 30),
                        FONT, 0.7, (120, 120, 255), 2, cv2.LINE_AA)
            self._pose_count = 0
            return frame

        if infer:
            try:
                self._last_persons = self.pose.infer(frame)
            except Exception:
                # a dying Hailo must degrade to "no skeletons", never freeze
                # the shared stream (see also the detection wrapper in _detect)
                self._last_persons = []
        persons = self._last_persons
        self._pose_count = len(persons)

        if (time.monotonic() < self._ch_flash_until
                and not self.pose_ghost):
            # Challenge passed: frost the CAMERA image for the celebration
            # (skeletons are drawn after this, so they stay sharp on the
            # soft background). The crisp "Geschafft!" text itself is a
            # client-side overlay — never burned into the frame. Ghost
            # mode needs no frosting: its frame is synthetic anyway.
            frame = cv2.resize(cv2.resize(frame, (64, 36),
                                          interpolation=cv2.INTER_AREA),
                               (w, h), interpolation=cv2.INTER_LINEAR)

        if self.pose_ghost:
            # Geist-Modus: the camera image disappears entirely — the point
            # of the station: tracking works without ever showing video.
            frame = np.full_like(frame, 16)
            frame[:, :, 0] = 28
            for x in range(0, w, 40):
                cv2.line(frame, (x, 0), (x, h), (36, 26, 22), 1)
            for y in range(0, h, 40):
                cv2.line(frame, (0, y), (w, y), (36, 26, 22), 1)

        for n, person in enumerate(persons):
            color = SKELETON_COLORS[n % len(SKELETON_COLORS)]
            kpts = person["kpts"]
            pts = [(int(x * w), int(y * h), c) for x, y, c in kpts]
            for a, b in SKELETON_BONES:
                if kpts[a, 2] >= config.POSE_KPT_THRESHOLD \
                        and kpts[b, 2] >= config.POSE_KPT_THRESHOLD:
                    cv2.line(frame, pts[a][:2], pts[b][:2], color, 3,
                             cv2.LINE_AA)
            for x, y, c in pts:
                if c >= config.POSE_KPT_THRESHOLD:
                    cv2.circle(frame, (x, y), 4, color, -1, cv2.LINE_AA)
            if kpts[0, 2] >= config.POSE_KPT_THRESHOLD:  # a head for the ghost
                head_r = max(8, int(_shoulder_width(kpts) * w * 0.25))
                cv2.circle(frame, pts[0][:2], head_r, color, 2, cv2.LINE_AA)

        self._pose_challenge(persons)
        return frame

    def _pose_challenge(self, persons):
        """Advance the Posen-Parcours: hold the pose briefly to pass."""
        if not persons:
            self._ch_hold_since = None
            return
        # the largest (closest) skeleton plays
        def area(p):
            x0, y0, x1, y1 = p["box"]
            return (x1 - x0) * (y1 - y0)
        player = max(persons, key=area)
        _, _, check = POSE_CHALLENGES[self._ch_idx]
        if check(player["kpts"]):
            if self._ch_hold_since is None:
                self._ch_hold_since = time.monotonic()
            elif (time.monotonic() - self._ch_hold_since
                  >= config.POSE_HOLD_SECONDS):
                self._ch_done += 1
                self._ch_idx = (self._ch_idx + 1) % len(POSE_CHALLENGES)
                self._ch_hold_since = None
                # 2.5 s: phones poll at ~0.8 s, every viewer must catch it
                self._ch_flash_until = time.monotonic() + 2.5
        else:
            self._ch_hold_since = None

    def _publish_state(self, mode, detections):
        panel = []
        # coarse-round before sorting so score jitter cannot reshuffle rows
        for class_id, conf, _ in sorted(
                detections, key=lambda d: (-int(d[1] * 20), d[0]))[:8]:
            name_en, name_de, emoji = class_info(class_id)
            panel.append({"emoji": emoji, "name": name_de,
                          "name_en": name_en.capitalize(),
                          "pct": int(conf * 100)})
        own = getattr(self, "_own_hit", None)
        if mode == "detektiv" and own:
            panel.insert(0, own)          # own training tops the list

        prediction = getattr(self, "_last_prediction", None)
        teach_pred = None
        if mode == "trainer" and prediction is not None:
            slot, conf = prediction
            teach_pred = {"slot": slot, "name": self.teach.names[slot],
                          "pct": int(conf * 100)}

        self.state = {
            "event_name": config.EVENT_NAME,
            "lang": self.lang,
            "mode": mode,
            "locked": self.locked,
            "uptime_s": int(time.time() - self.started),
            "fps": round(self.fps, 1),
            "clients": self.stream_clients,
            "source": self.source.name,
            "camera_ok": getattr(self.source, "connected", True),
            "camera_reconnects": getattr(self.source, "reconnects", 0),
            "ai": {"ok": self.detector is not None, "status": self.detector_status},
            "threshold": self.threshold,
            "privacy": {
                "on": self.privacy_on,
                "style": self.privacy_style,
                "current": len(self.faces.boxes),
                "events": self.faces.protect_events,
                "backend": self.faces.backend,
            },
            "detections": panel,
            "teach": {
                "names": self.teach.names,
                "counts": self.teach.sample_counts(),
                "min": config.TEACH_MIN_SAMPLES,
                "trained": self.teach.trained_slots,
                "prediction": teach_pred,
            },
            "heatmap": {"since_s": int(time.time() - self.heatmap.since)},
            "system": self._system_health(),
            "camera_standby": getattr(self.source, "standby", False),
            "exhibit": {
                "attract": self.attract,
                "frames": self.frames_total,
                "cloud_mb": round(self.cloud_bytes / 1e6, 1),
                "object_events": self.object_events,
                "classes_seen": len(self.classes_seen),
                "faces_now": len(self.faces.boxes),
                "faces_max": self.faces_max,
                "protect_events": self.faces.protect_events,
                "heat_coverage": self.heatmap.coverage,
            },
            "pose": {
                "available": self.pose is not None,
                "status": self.pose_status,
                "persons": self._pose_count,
                "ghost": self.pose_ghost,
                "challenge": {
                    "flash": time.monotonic() < self._ch_flash_until,
                    "emoji": POSE_CHALLENGES[self._ch_idx][0],
                    "text": POSE_CHALLENGES[self._ch_idx][1],
                    "idx": self._ch_idx + 1,
                    "total": len(POSE_CHALLENGES),
                    "done": self._ch_done,
                    "progress": min(1.0, (time.monotonic() - self._ch_hold_since)
                                    / config.POSE_HOLD_SECONDS)
                    if self._ch_hold_since else 0.0,
                },
            },
        }

    def _system_health(self):
        """Temperatures, fan and throttling for the /system window.

        Everything is None off-Pi, and the page just leaves those rows out.
        A CPU reading WITH no fan reading means the Pi found no fan at boot:
        either it is unplugged or it died. That combination is worth saying
        out loud, because the exhibit then has no thermal headroom at all.
        """
        now = time.monotonic()
        if now - getattr(self, "_sys_ts", 0.0) < 3.0:
            return self._sys_cache

        cpu = fan = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                cpu = round(int(f.read()) / 1000.0, 1)
        except Exception:
            pass
        try:
            for path in glob.glob(
                    "/sys/devices/platform/cooling_fan/hwmon/*/fan1_input"):
                with open(path) as f:
                    fan = int(f.read())
                break
        except Exception:
            pass

        self._sys_cache = {
            "temp_c": cpu,
            "fan_rpm": fan,
            "hailo_c": vision.hailo_temperature(),
            "throttled": self._throttled,
            # surfaces as a warning in /system: the default PIN is public
            # (it is in the repo), so real events need their own
            "default_pin": config.ADMIN_PIN == "2468",
        }
        self._sys_ts = now
        return self._sys_cache

    def _throttle_loop(self):
        """`vcgencmd get_throttled` in the background.

        It is a subprocess, so it must never run on the pipeline thread —
        one slow call there would stutter the stream for every viewer.
        """
        log = logging.getLogger("pipeline")
        while self.running:
            try:
                out = subprocess.run(["vcgencmd", "get_throttled"],
                                     capture_output=True, text=True, timeout=3)
                bits = int(out.stdout.strip().split("=")[1], 16)
                self._throttled = {
                    # low half: happening right now, high half: since boot
                    "now": bool(bits & 0xF),
                    "ever": bool(bits >> 16 & 0xF),
                    "raw": hex(bits),
                }
            except Exception:
                self._throttled = None       # not a Pi, or vcgencmd missing
                log.debug("throttle read failed", exc_info=True)
                return                       # no point retrying forever
            time.sleep(15)

    # -- actions from the web API -------------------------------------------

    def teach_capture(self, slot):
        # Use the pipeline's latest raw frame — never read the camera from
        # a request thread (two readers can starve each other on webcams).
        frame = getattr(self, "last_frame", None)
        if frame is None or not getattr(self, "camera_live", True):
            return 0        # never learn from the placeholder image
        return self.teach.capture(frame, slot)

    def reset_all(self):
        self.lang = "de"              # next class starts in German
        self.teach.reset()
        self.heatmap.reset()
        self.faces.protect_events = 0
        self.frames_total = 0
        self.published_total = 0      # frames actually handed to viewers —
                                      # the watchdog's liveness metric
        self.cloud_bytes = 0
        self.object_events = 0
        self.classes_seen = set()
        self._objects_present = set()
        self.faces_max = 0
        self.faces._had_faces = False
        self._ch_idx = 0
        self._ch_done = 0
