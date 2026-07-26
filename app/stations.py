"""The frame pipeline: one camera, one active station mode, many viewers.

A single background thread reads frames, runs the active station's
processing, draws overlays and publishes JPEG bytes + a state dict that the
web clients poll.
"""

import logging
import threading
import time

import cv2
import numpy as np

import config
import vision
from camera import FakeSource
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
        self.pose_ghost = False
        self._ch_idx = 0
        self._ch_done = 0
        self._ch_hold_since = None
        self._ch_flash_until = 0.0
        self._pose_count = 0

        self.faces = vision.FaceGuard()
        self.heatmap = vision.MotionHeatmap()
        self.teach = vision.Teachable()

        self.mode = config.DEFAULT_MODE
        self.threshold = config.DETECT_THRESHOLD_DEFAULT
        self.privacy_on = config.FACE_GUARD_GLOBAL_DEFAULT
        self.privacy_style = "pixel"
        self.locked = False

        self.started = time.time()
        self.running = True
        self.fps = 0.0
        self.stream_clients = 0

        self.jpeg = None
        self.state = {}
        self.frame_ready = threading.Condition()

        self._thread = threading.Thread(target=self._run, daemon=True)

    # -- public control (called from Flask request threads) -----------------

    def start(self):
        self._thread.start()

    def stop(self):
        self.running = False

    def set_mode(self, mode):
        if mode in MODES:
            self.mode = mode
            return True
        return False

    # -- main loop ----------------------------------------------------------

    def _run(self):
        log = logging.getLogger("pipeline")
        last_error_log = 0.0
        while self.running:
            t0 = time.time()
            try:
                frame = self.source.read()
            except Exception:
                time.sleep(0.5)
                continue

            try:
                self._process(frame)
            except Exception:
                # One bad frame must never kill the exhibit for everyone —
                # log (rate-limited), drop the frame, keep streaming.
                if time.time() - last_error_log > 10:
                    last_error_log = time.time()
                    log.exception("Frame processing failed — frame dropped")

            time.sleep(max(0.0, 1 / 30 - (time.time() - t0)))
            loop_dt = time.time() - t0
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / max(loop_dt, 1e-3))

    def _process(self, frame):
            self.last_frame = frame.copy()  # clean copy for teach_capture
            mode = self.mode  # snapshot: mode may change mid-frame

            # Background bookkeeping that runs in *every* mode — on purpose:
            # the Datenspur station later reveals what was collected while
            # people were busy playing (exactly how real surveillance works).
            self.heatmap.update(frame)
            self.faces.update(frame)

            detections = []
            if mode in ("detektiv", "trick"):
                detections = self._detect(frame)
                self._draw_detections(frame, detections)
            elif mode == "trainer":
                prediction = self._trainer_frame(frame)
            elif mode == "spur":
                frame = self.heatmap.render(frame)
            elif mode == "pose":
                frame = self._pose_frame(frame)
            elif mode == "start":
                cv2.putText(frame, "Willkommen! Waehle eine Station.",
                            (14, 30), FONT, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

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

            ok, buf = cv2.imencode(".jpg", frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, config.JPEG_QUALITY])
            if ok:
                with self.frame_ready:
                    self.jpeg = buf.tobytes()
                    self.frame_ready.notify_all()

            self._publish_state(mode, detections)

    # -- per-station helpers -------------------------------------------------

    def _detect(self, frame):
        if self.detector is not None:
            try:
                return self.detector.detect(frame)
            except Exception:
                return []
        if isinstance(self.source, FakeSource):
            return self.source.fake_detections
        # CPU fallback: at least report faces as persons so the station
        # is not dead without an AI HAT.
        h, w = frame.shape[:2]
        return [(0, 0.8, (x / w, y / h, (x + fw) / w, (y + fh) / h))
                for (x, y, fw, fh) in self.faces.boxes]

    def _draw_detections(self, frame, detections):
        h, w = frame.shape[:2]
        for class_id, conf, (x0, y0, x1, y1) in detections:
            if conf < self.threshold:
                continue
            color = _class_color(class_id)
            p0 = (int(x0 * w), int(y0 * h))
            p1 = (int(x1 * w), int(y1 * h))
            cv2.rectangle(frame, p0, p1, color, 2)
            _, name_de, _ = class_info(class_id)
            _label(frame, f"{de_ascii(name_de)} {int(conf * 100)}%",
                   p0[0], p0[1] - 4, color)

    def _trainer_frame(self, frame):
        x0, y0, x1, y1 = self.teach.guide_box(frame)
        cv2.rectangle(frame, (x0, y0), (x1, y1), (255, 200, 80), 2)
        prediction = self.teach.predict(frame)
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

    def _pose_frame(self, frame):
        h, w = frame.shape[:2]
        if self.pose is None:
            cv2.putText(frame, "Pose-Modell nicht verfuegbar", (14, 30),
                        FONT, 0.7, (120, 120, 255), 2, cv2.LINE_AA)
            self._pose_count = 0
            return frame

        persons = self.pose.infer(frame)
        self._pose_count = len(persons)

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
        if time.time() < self._ch_flash_until:
            text = "GESCHAFFT!"
            (tw, _), _ = cv2.getTextSize(text, FONT, 1.3, 3)
            cv2.putText(frame, text, ((w - tw) // 2, h // 2), FONT, 1.3,
                        (90, 255, 120), 3, cv2.LINE_AA)
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
                self._ch_hold_since = time.time()
            elif time.time() - self._ch_hold_since >= config.POSE_HOLD_SECONDS:
                self._ch_done += 1
                self._ch_idx = (self._ch_idx + 1) % len(POSE_CHALLENGES)
                self._ch_hold_since = None
                self._ch_flash_until = time.time() + 1.5
        else:
            self._ch_hold_since = None

    def _publish_state(self, mode, detections):
        panel = []
        for class_id, conf, _ in sorted(detections, key=lambda d: -d[1])[:8]:
            if conf < self.threshold:
                continue
            _, name_de, emoji = class_info(class_id)
            panel.append({"emoji": emoji, "name": name_de, "pct": int(conf * 100)})

        prediction = getattr(self, "_last_prediction", None)
        teach_pred = None
        if mode == "trainer" and prediction is not None:
            slot, conf = prediction
            teach_pred = {"slot": slot, "name": self.teach.names[slot],
                          "pct": int(conf * 100)}

        self.state = {
            "event_name": config.EVENT_NAME,
            "mode": mode,
            "locked": self.locked,
            "uptime_s": int(time.time() - self.started),
            "fps": round(self.fps, 1),
            "clients": self.stream_clients,
            "source": self.source.name,
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
            "pose": {
                "available": self.pose is not None,
                "status": self.pose_status,
                "persons": self._pose_count,
                "ghost": self.pose_ghost,
                "challenge": {
                    "emoji": POSE_CHALLENGES[self._ch_idx][0],
                    "text": POSE_CHALLENGES[self._ch_idx][1],
                    "idx": self._ch_idx + 1,
                    "total": len(POSE_CHALLENGES),
                    "done": self._ch_done,
                    "progress": min(1.0, (time.time() - self._ch_hold_since)
                                    / config.POSE_HOLD_SECONDS)
                    if self._ch_hold_since else 0.0,
                },
            },
        }

    # -- actions from the web API -------------------------------------------

    def teach_capture(self, slot):
        # Use the pipeline's latest raw frame — never read the camera from
        # a request thread (two readers can starve each other on webcams).
        frame = getattr(self, "last_frame", None)
        if frame is None:
            return 0
        return self.teach.capture(frame, slot)

    def reset_all(self):
        self.teach.reset()
        self.heatmap.reset()
        self.faces.protect_events = 0
        self.faces._had_faces = False
        self._ch_idx = 0
        self._ch_done = 0
