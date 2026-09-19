"""Vision building blocks: Hailo object detection, face anonymisation,
motion heatmap and the teachable kNN classifier.

Everything degrades gracefully: without an AI HAT the app still runs and the
face/motion/teachable stations keep working on the CPU.
"""

import collections
import os
import time

import cv2
import numpy as np

import config


def hailo_temperature():
    """Chip temperature of the AI HAT in °C, or None if there is no HAT.

    It goes through the VDevice that picamera2 shares between our detection
    and pose models (Hailo.TARGET) — opening a second handle to ask would
    fail while inference is running. Call this from the pipeline thread, the
    same one that runs inference, so the two never overlap.
    """
    try:
        from picamera2.devices import Hailo
        if Hailo.TARGET is None:
            return None
        devices = Hailo.TARGET.get_physical_devices()
        if not devices:
            return None
        info = devices[0].control.get_chip_temperature()
        # two sensors on the die; the hotter one is the interesting one
        return round(max(info.ts0_temperature, info.ts1_temperature), 1)
    except Exception:
        return None


# --- Object detection (AI HAT) ---------------------------------------------

def _letterbox(frame, mw, mh):
    """Fit the frame into the model canvas WITHOUT distortion: scale to
    fit, pad bottom/right with YOLO's canonical gray. The old plain resize
    squashed 16:9 into the square input (1.8x vertical stretch) and cost
    real accuracy. Returns the canvas plus the (sx, sy) fraction the image
    occupies, for mapping normalised model outputs back."""
    h, w = frame.shape[:2]
    scale = min(mw / w, mh / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    canvas = np.full((mh, mw, 3), 114, np.uint8)
    canvas[:nh, :nw] = cv2.resize(frame, (nw, nh),
                                  interpolation=cv2.INTER_LINEAR)
    return canvas, (nw / mw, nh / mh)


class HailoDetector:
    """YOLO object detection on the Hailo accelerator via picamera2's wrapper.

    The .hef models shipped by hailo-all run NMS on-chip, so the output is
    already a per-class list of [y0, x0, y1, x1, score] boxes (normalised).
    """

    def __init__(self, hef_path):
        from picamera2.devices import Hailo  # lazy: Pi + hailo-all only
        self.hef_path = hef_path
        self.hailo = Hailo(hef_path)
        self.height, self.width, _ = self.hailo.get_input_shape()

    def detect(self, frame_bgr):
        model_frame, span = _letterbox(frame_bgr, self.width, self.height)
        if config.MODEL_EXPECTS_RGB:
            model_frame = cv2.cvtColor(model_frame, cv2.COLOR_BGR2RGB)
        raw = self.hailo.run(model_frame)
        return self._extract(raw, span)

    @staticmethod
    def _extract(raw, span=(1.0, 1.0)):
        # Some HailoRT versions wrap the per-class list in one more list.
        if isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], (list, np.ndarray)) \
                and len(raw[0]) > 20:
            raw = raw[0]
        detections = []
        for class_id, class_dets in enumerate(raw):
            for det in class_dets:
                if len(det) < 5:
                    continue
                y0, x0, y1, x1, score = (float(v) for v in det[:5])
                sx, sy = span              # undo the letterbox padding
                box = (min(x0 / sx, 1.0), min(y0 / sy, 1.0),
                       min(x1 / sx, 1.0), min(y1 / sy, 1.0))
                detections.append((class_id, score, box))
        return detections

    def close(self):
        try:
            self.hailo.close()
        except Exception:
            pass


def find_hef():
    for path in config.HEF_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def open_detector():
    """Return (detector_or_None, status_text)."""
    hef = find_hef()
    if hef is None:
        return None, "Kein Hailo-Modell gefunden"
    try:
        det = HailoDetector(hef)
        return det, os.path.basename(hef)
    except Exception as exc:  # no HAT, driver missing, …
        return None, f"Hailo nicht verfügbar ({type(exc).__name__})"


# --- Pose estimation (Skelett-Spiegel) -------------------------------------

class PoseEstimator:
    """YOLOv8-pose on Hailo with host-side decoding.

    The pose .hef files ship without on-chip NMS: the output is a dict of
    raw head tensors, per scale (stride 8/16/32) one box-distribution map
    (H,W,64), one person-score map (H,W,1) and one keypoint map (H,W,51 =
    17 joints x (x, y, conf)).
    """

    def __init__(self, hef_path):
        from picamera2.devices import Hailo  # lazy: Pi + hailo runtime only
        self.hef_path = hef_path
        self.hailo = Hailo(hef_path)
        self.height, self.width, _ = self.hailo.get_input_shape()

    def infer(self, frame_bgr):
        """Return persons as dicts: score, box (normalised x0,y0,x1,y1),
        kpts (17,3) array of normalised x, y and confidence."""
        model, (sx, sy) = _letterbox(frame_bgr, self.width, self.height)
        if config.MODEL_EXPECTS_RGB:
            model = cv2.cvtColor(model, cv2.COLOR_BGR2RGB)
        raw = self.hailo.run(model)
        persons = self._decode(raw)
        for p in persons:                  # undo the letterbox padding
            p["box"] = p["box"] / np.array([sx, sy, sx, sy])
            p["kpts"][:, 0] /= sx
            p["kpts"][:, 1] /= sy
        return persons

    def _decode(self, raw):
        by_scale = {}
        for arr in raw.values():
            by_scale.setdefault(arr.shape[0], {})[arr.shape[-1]] = arr

        candidates = []
        for grid, tensors in by_scale.items():
            if not all(c in tensors for c in (64, 1, 51)):
                continue
            stride = self.height / grid
            scores = tensors[1][..., 0]
            if scores.max() > 1.0:  # logits instead of probabilities
                scores = 1.0 / (1.0 + np.exp(-scores))
            ys, xs = np.where(scores >= config.POSE_SCORE_THRESHOLD)
            for gy, gx in zip(ys, xs):
                # box: DFL distribution -> expected l,t,r,b in cell units
                dist = tensors[64][gy, gx].reshape(4, 16)
                dist = np.exp(dist - dist.max(axis=1, keepdims=True))
                dist /= dist.sum(axis=1, keepdims=True)
                ltrb = dist @ np.arange(16, dtype=np.float32)
                cx, cy = gx + 0.5, gy + 0.5
                box = np.array([(cx - ltrb[0]), (cy - ltrb[1]),
                                (cx + ltrb[2]), (cy + ltrb[3])]) * stride
                # keypoints (ultralytics decode: (k*2 + cell) * stride)
                k = tensors[51][gy, gx].reshape(17, 3).astype(np.float32)
                kx = (k[:, 0] * 2.0 + gx) * stride / self.width
                ky = (k[:, 1] * 2.0 + gy) * stride / self.height
                kc = 1.0 / (1.0 + np.exp(-k[:, 2]))
                candidates.append({
                    "score": float(scores[gy, gx]),
                    "box": box / np.array([self.width, self.height] * 2),
                    "kpts": np.stack([kx, ky, kc], axis=1),
                })
        return self._nms(candidates)

    @staticmethod
    def _nms(candidates, iou_limit=0.5):
        candidates.sort(key=lambda p: -p["score"])
        kept = []
        for cand in candidates:
            x0, y0, x1, y1 = cand["box"]
            area = max(0.0, x1 - x0) * max(0.0, y1 - y0)
            duplicate = False
            for other in kept:
                ox0, oy0, ox1, oy1 = other["box"]
                iw = max(0.0, min(x1, ox1) - max(x0, ox0))
                ih = max(0.0, min(y1, oy1) - max(y0, oy0))
                inter = iw * ih
                oarea = max(0.0, ox1 - ox0) * max(0.0, oy1 - oy0)
                if inter / max(area + oarea - inter, 1e-6) > iou_limit:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(cand)
        return kept[:6]

    def close(self):
        try:
            self.hailo.close()
        except Exception:
            pass


def open_pose():
    """Return (estimator_or_None, status_text)."""
    for path in config.POSE_HEF_CANDIDATES:
        if os.path.exists(path):
            try:
                return PoseEstimator(path), os.path.basename(path)
            except Exception as exc:
                return None, f"Pose nicht verfügbar ({type(exc).__name__})"
    return None, "Kein Pose-Modell gefunden"


class DetectionSmoother:
    """Temporal steadiness for the detection overlay.

    Raw YOLO output flickers: confidences bounce around the slider value and
    boxes jitter a little every frame, so labels blink in and out. Instead of
    drawing raw output, we keep a tiny track list: an object must show up for
    a few consecutive frames before it appears, survives short dropouts, and
    its box and score are exponentially smoothed. Entry and exit use
    different thresholds (hysteresis), so a confidence hovering exactly at
    the slider value cannot strobe. Tuning lives in config.py.
    """

    IOU_MATCH = 0.25       # boxes overlapping this much are the same object
    EXIT_FACTOR = 0.85     # visible until score < threshold * this
    BOX_ALPHA = 0.45       # weight of the newest box (higher = snappier)
    SCORE_ALPHA = 0.30     # weight of the newest score

    def __init__(self):
        self._tracks = []
        self._last_update = 0.0

    @staticmethod
    def _iou(a, b):
        ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
        iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
        inter = ix * iy
        if inter <= 0:
            return 0.0
        union = ((a[2] - a[0]) * (a[3] - a[1])
                 + (b[2] - b[0]) * (b[3] - b[1]) - inter)
        return inter / max(union, 1e-9)

    def update(self, raw, threshold):
        now = time.monotonic()
        if now - self._last_update > 1.5:   # station was left — start fresh
            self._tracks = []
        self._last_update = now

        # Keep candidates a bit below the slider too, so a held object may
        # dip briefly without being treated as gone.
        cands = [d for d in raw if d[1] >= threshold * 0.7]

        for t in self._tracks:
            t["matched"] = False
        # strongest detections claim their track first
        for cid, score, box in sorted(cands, key=lambda d: -d[1]):
            best, best_iou = None, self.IOU_MATCH
            for t in self._tracks:
                if t["matched"] or t["cid"] != cid:
                    continue
                iou = self._iou(t["box"], box)
                if iou > best_iou:
                    best, best_iou = t, iou
            if best is None:
                self._tracks.append({"cid": cid, "box": box, "score": score,
                                     "seen": 1, "missed": 0, "shown": False,
                                     "matched": True})
            else:
                best["matched"] = True
                a = self.BOX_ALPHA
                best["box"] = tuple((1 - a) * o + a * n
                                    for o, n in zip(best["box"], box))
                best["score"] += self.SCORE_ALPHA * (score - best["score"])
                best["seen"] += 1
                best["missed"] = 0

        out = []
        alive = []
        for t in self._tracks:
            if not t["matched"]:
                t["missed"] += 1
                if t["missed"] > config.DETECT_STEADY_HOLD:
                    continue                       # object really left
            alive.append(t)
            if not t["shown"]:
                if (t["seen"] >= config.DETECT_STEADY_ENTER
                        and t["score"] >= threshold):
                    t["shown"] = True
            elif t["score"] < threshold * self.EXIT_FACTOR:
                t["shown"] = False
                t["seen"] = 0    # must re-confirm — prevents strobing
            if t["shown"]:
                out.append((t["cid"], t["score"], tuple(t["box"])))
        self._tracks = alive
        return out


# --- Face anonymisation ----------------------------------------------------

class FaceGuard:
    """Face detection + pixelate/blur/smiley anonymisation.

    Prefers the bundled YuNet DNN model (fast, handles small and slightly
    turned faces); falls back to a Haar cascade — resolved across the
    various install locations, because Debian's python3-opencv has no
    cv2.data module. `backend` says what is active ("yunet"/"haar"/"none")
    and is surfaced in the UI rather than failing silently.

    Boxes are held for a few frames after a lost detection so faces don't
    flash unprotected during detector hiccups.
    """

    STYLES = ("pixel", "blur", "smiley")
    HOLD_FRAMES = 8  # ~½ s protection hold-over after a lost detection

    YUNET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "models", "face_detection_yunet_2023mar.onnx")
    CASCADE_DIRS = [
        "/usr/share/opencv4/haarcascades",        # Debian/RPi OS apt package
        "/usr/local/share/opencv4/haarcascades",
        "/usr/share/opencv/haarcascades",
    ]

    def __init__(self):
        self.backend = "none"
        self.detector = None
        self.cascade = None
        if os.path.exists(self.YUNET_PATH) and hasattr(cv2, "FaceDetectorYN"):
            try:
                self.detector = cv2.FaceDetectorYN.create(
                    self.YUNET_PATH, "", (320, 180), 0.6)
                self.backend = "yunet"
            except Exception:
                self.detector = None
        if self.detector is None:
            for path in self._cascade_candidates():
                cascade = cv2.CascadeClassifier(path)
                if not cascade.empty():
                    self.cascade = cascade
                    self.backend = "haar"
                    break
        self.boxes = []          # in display coordinates
        self._hold = 0
        self.protect_events = 0  # times faces appeared after none were present
        self._tick = 0
        self._had_faces = False

    def clear(self):
        """Forget current boxes — called while the camera is off/standby so
        stale rectangles can't outlive the picture they belong to. Also
        resets the appeared-after-absent edge, so the first visitors after a
        wake count as a fresh protection moment."""
        self.boxes = []
        self._hold = 0
        self._had_faces = False

    @classmethod
    def _cascade_candidates(cls):
        name = "haarcascade_frontalface_default.xml"
        paths = []
        data = getattr(cv2, "data", None)  # pip wheel only, not Debian apt
        if data is not None:
            paths.append(os.path.join(data.haarcascades, name))
        paths += [os.path.join(d, name) for d in cls.CASCADE_DIRS]
        return [p for p in paths if os.path.exists(p)]

    def update(self, frame):
        if self.backend == "none":
            return
        self._tick += 1
        if self._tick % config.FACE_DETECT_EVERY_N_FRAMES:
            return
        h, w = frame.shape[:2]
        if self.detector is not None:
            # YuNet at full stream resolution: keeps 2-4 m faces detectable
            self.detector.setInputSize((w, h))
            _, dets = self.detector.detect(frame)
            found = [] if dets is None else \
                [(int(x), int(y), int(fw), int(fh))
                 for x, y, fw, fh in dets[:, :4]]
        else:
            small = cv2.resize(frame, (480, 480 * h // w))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            faces = self.cascade.detectMultiScale(gray, 1.15, 4,
                                                  minSize=(24, 24))
            sx, sy = w / small.shape[1], h / small.shape[0]
            found = [(int(x * sx), int(y * sy), int(fw * sx), int(fh * sy))
                     for (x, y, fw, fh) in faces]
        if found:
            self.boxes = found
            self._hold = self.HOLD_FRAMES
        elif self._hold > 0:
            self._hold -= 1   # keep protecting the last known positions
        else:
            self.boxes = []
        if self.boxes and not self._had_faces:
            self.protect_events += 1
        self._had_faces = bool(self.boxes)

    def apply(self, frame, style="pixel"):
        h, w = frame.shape[:2]
        for (x, y, fw, fh) in self.boxes:
            # widen the box a little so hairline/chin are covered too
            mx, my = int(fw * 0.15), int(fh * 0.2)
            x0, y0 = max(0, x - mx), max(0, y - my)
            x1, y1 = min(w, x + fw + mx), min(h, y + fh + my)
            if x1 <= x0 or y1 <= y0:
                continue
            roi = frame[y0:y1, x0:x1]
            if style == "blur":
                frame[y0:y1, x0:x1] = cv2.GaussianBlur(roi, (0, 0), 12)
            elif style == "smiley":
                cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                r = max((x1 - x0), (y1 - y0)) // 2
                cv2.circle(frame, (cx, cy), r, (60, 210, 255), -1)
                cv2.circle(frame, (cx, cy), r, (30, 150, 220), 3)
                er = max(2, r // 6)
                cv2.circle(frame, (cx - r // 3, cy - r // 4), er, (40, 40, 40), -1)
                cv2.circle(frame, (cx + r // 3, cy - r // 4), er, (40, 40, 40), -1)
                cv2.ellipse(frame, (cx, cy + r // 6), (r // 2, r // 3),
                            0, 15, 165, (40, 40, 40), max(2, r // 8))
            else:  # pixel
                ph = max(1, (y1 - y0) // 9)
                pw = max(1, (x1 - x0) // 9)
                small = cv2.resize(roi, (pw, ph), interpolation=cv2.INTER_LINEAR)
                frame[y0:y1, x0:x1] = cv2.resize(
                    small, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST)
        return frame


# --- Motion heatmap ("Die Datenspur") --------------------------------------

class MotionHeatmap:
    """Accumulates motion over time and renders it as a heat overlay —
    a visceral demo of what even a 'dumb' camera learns about a room."""

    GRID = (160, 90)  # small accumulator, cheap to update

    def __init__(self):
        self.reset()

    def reset(self):
        self.acc = np.zeros((self.GRID[1], self.GRID[0]), np.float32)
        self.prev = None
        self.since = time.time()

    def update(self, frame):
        gray = cv2.cvtColor(cv2.resize(frame, self.GRID), cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        if self.prev is not None:
            diff = cv2.absdiff(gray, self.prev)
            _, mask = cv2.threshold(diff, 18, 1, cv2.THRESH_BINARY)
            self.acc += mask.astype(np.float32)
        self.prev = gray

    @property
    def coverage(self):
        """Share of the room's grid cells that ever saw motion (0..1)."""
        return round(float((self.acc > 2).mean()), 3)

    def render(self, frame):
        peak = float(self.acc.max())
        if peak < 1:
            return frame
        norm = np.sqrt(self.acc / peak)  # sqrt lifts faint traces into view
        heat_small = cv2.applyColorMap((norm * 255).astype(np.uint8),
                                       cv2.COLORMAP_TURBO)
        heat = cv2.resize(heat_small, (frame.shape[1], frame.shape[0]))
        alpha = cv2.resize(norm, (frame.shape[1], frame.shape[0]))[:, :, None] * 0.7
        out = frame.astype(np.float32) * (1 - alpha) + heat.astype(np.float32) * alpha
        return out.astype(np.uint8)


# --- Teachable machine -----------------------------------------------------

class Teachable:
    """Train-your-own classifier: HOG features + weighted kNN.

    Stores only feature vectors — never images — which is itself part of the
    privacy story ('Datenminimierung') told in the UI.
    """

    SLOTS = ["A", "B", "C"]

    def __init__(self):
        try:
            self.hog = cv2.HOGDescriptor((64, 64), (16, 16), (8, 8), (8, 8), 9)
        except AttributeError:  # OpenCV without HOG: raw-pixel fallback
            self.hog = None
        self.reset()
        self.names = {s: f"Ding {s}" for s in self.SLOTS}

    def reset(self):
        self.samples = {s: [] for s in self.SLOTS}
        self._history = collections.deque(maxlen=6)

    def rename(self, slot, name):
        # Whitelist, not blacklist: the name is broadcast to every client and
        # rendered there, so no HTML metacharacters may survive.
        if slot in self.names:
            allowed = " -_äöüÄÖÜß"
            clean = "".join(c for c in name
                            if c.isalnum() or c in allowed)[:16].strip()
            if clean:
                self.names[slot] = clean

    def _features(self, frame):
        h, w = frame.shape[:2]
        side = min(h, w) * 2 // 3
        x0, y0 = (w - side) // 2, (h - side) // 2
        crop = frame[y0:y0 + side, x0:x0 + side]
        gray = cv2.cvtColor(cv2.resize(crop, (64, 64)), cv2.COLOR_BGR2GRAY)
        if self.hog is None:
            small = cv2.resize(gray, (32, 32)).astype(np.float32).flatten()
            return small / (np.linalg.norm(small) + 1e-6)
        return self.hog.compute(gray).flatten()

    @staticmethod
    def guide_box(frame):
        """The centre square students should hold their object inside."""
        h, w = frame.shape[:2]
        side = min(h, w) * 2 // 3
        x0, y0 = (w - side) // 2, (h - side) // 2
        return x0, y0, x0 + side, y0 + side

    MAX_SAMPLES = 50     # per slot: keeps predict() fast for a whole day

    def capture(self, frame, slot):
        if slot not in self.samples:
            return 0
        feats = self._features(frame)
        bucket = self.samples[slot]
        if len(bucket) >= self.MAX_SAMPLES:
            # reservoir-style replace: late examples still shape the class
            import random as _r
            bucket[_r.randrange(len(bucket))] = feats
        else:
            bucket.append(feats)
        return len(bucket)

    @property
    def trained_slots(self):
        return [s for s in self.SLOTS
                if len(self.samples[s]) >= config.TEACH_MIN_SAMPLES]

    def predict(self, frame):
        """Return (slot, confidence) or None while not enough data exists."""
        slots = self.trained_slots
        if len(slots) < 2:
            return None
        feats = self._features(frame)
        dists, labels = [], []
        for s in slots:
            for vec in self.samples[s]:
                dists.append(np.linalg.norm(vec - feats))
                labels.append(s)
        order = np.argsort(dists)[:config.TEACH_KNN_K]
        votes = {}
        for i in order:
            votes[labels[i]] = votes.get(labels[i], 0.0) + 1.0 / (dists[i] + 1e-6)
        total = sum(votes.values())
        best = max(votes, key=votes.get)
        self._history.append((best, votes[best] / total))
        # smooth over the last few frames so the label doesn't flicker
        counts = collections.Counter(s for s, _ in self._history)
        stable = counts.most_common(1)[0][0]
        confs = [c for s, c in self._history if s == stable]
        return stable, float(np.mean(confs))

    def sample_counts(self):
        return {s: len(v) for s, v in self.samples.items()}
