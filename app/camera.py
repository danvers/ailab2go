"""Frame sources: Pi camera, USB webcam, or a synthetic test pattern.

All sources deliver BGR frames at config.FRAME_SIZE via read().
The fake source additionally exposes fake_detections so the whole UI can be
demoed on a laptop without any camera or AI hardware.
"""

import logging
import math
import threading
import time

import cv2
import numpy as np

import config


class PiCameraSource:
    """CSI camera (e.g. Camera Module 3) via picamera2."""

    name = "Pi-Kamera"

    READ_TIMEOUT = 2.0   # a dead CSI feed must raise, not hang the pipeline

    def __init__(self):
        from picamera2 import Picamera2  # lazy: only available on the Pi

        # libcamera also enumerates USB/UVC cameras — but this class assumes
        # CSI semantics (XRGB stream, ISP scaling). A USB cam grabbed here
        # arrives as MJPEG/YUV and renders as garbage; it belongs to
        # WebcamSource, which handles format and aspect correctly.
        infos = Picamera2.global_camera_info()
        csi = [i for i, info in enumerate(infos)
               if "usb" not in str(info.get("Id", "")).lower()]
        if not csi:
            raise RuntimeError("no CSI camera attached "
                               "(USB cameras are handled by WebcamSource)")

        self.picam2 = Picamera2(csi[0])
        try:
            cam_config = self.picam2.create_video_configuration(
                main={"size": config.FRAME_SIZE, "format": "XRGB8888"}
            )
            self.picam2.configure(cam_config)
            self.picam2.start()
            try:  # continuous autofocus (Camera Module 3; older lack AF)
                from libcamera import controls
                self.picam2.set_controls(
                    {"AfMode": controls.AfModeEnum.Continuous})
            except Exception:
                pass
            self._wait_kwarg = True   # newer picamera2: capture(wait=seconds)
        except Exception:
            # A half-built Picamera2 keeps the camera acquired forever (the
            # global camera manager holds a reference) — release it before
            # letting the error bubble up, or no retry can ever succeed.
            self.close()
            raise

    def read(self):
        # Bounded wait: with a dead sensor/ribbon no request ever completes;
        # an indefinite capture_array() would disable all self-healing.
        if self._wait_kwarg:
            try:
                arr = self.picam2.capture_array(wait=self.READ_TIMEOUT)
            except TypeError:            # older picamera2 without wait=
                self._wait_kwarg = False
                arr = self.picam2.capture_array()
        else:
            arr = self.picam2.capture_array()
        if arr is None:
            raise RuntimeError("camera returned no frame")
        # XRGB8888 memory layout is B,G,R,X — drop X and we have OpenCV BGR.
        return arr[:, :, :3].copy()

    def close(self):
        # stop() alone keeps the camera acquired (fds, DMA buffers) — only
        # close() releases it for the next open attempt.
        try:
            self.picam2.stop()
        except Exception:
            pass
        try:
            self.picam2.close()
        except Exception:
            pass


class WebcamSource:
    """Any UVC webcam via OpenCV (also used for laptop dev mode)."""

    name = "USB-Webcam"

    # On a Pi the CSI camera exposes kernel V4L2 nodes (rp1-cfe/pisp/...)
    # that VideoCapture happily "opens" but that never deliver frames — and
    # holding them can even block libcamera from reacquiring the camera.
    NON_UVC = ("rp1", "cfe", "unicam", "bcm2835", "pisp", "isp",
               "hevc", "codec", "rpivid")

    @classmethod
    def _is_real_webcam(cls, index):
        import os
        sysname = f"/sys/class/video4linux/video{index}/name"
        if not os.path.exists(sysname):        # macOS/dev: no sysfs → allow
            return True
        try:
            name = open(sysname).read().strip().lower()
        except OSError:
            return True
        return not any(tag in name for tag in cls.NON_UVC)

    def __init__(self, index=0):
        if not self._is_real_webcam(index):
            raise RuntimeError(f"/dev/video{index} is not a USB camera")
        backend = cv2.CAP_V4L2 if hasattr(cv2, "CAP_V4L2") else 0
        self.cap = cv2.VideoCapture(index, backend) if backend \
            else cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Webcam {index} could not be opened")
        # MJPEG first: high-resolution UVC cameras (ELP 48MP & friends) only
        # manage smooth frame rates as MJPEG — raw YUYV over USB is slow and
        # prone to torn frames. Harmless if a camera ignores it.
        try:
            self.cap.set(cv2.CAP_PROP_FOURCC,
                         cv2.VideoWriter_fourcc(*"MJPG"))
        except Exception:
            pass
        # Ask for a real 16:9 HD mode; many of these sensors are 4:3-native
        # and would otherwise hand us 640x480. Whatever we actually get is
        # aspect-corrected in read() — never distorted.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, config.WEBCAM_FPS)
        # Optional fixed focus (see config): cap.set just returns False on
        # cameras that don't support the control — never an error.
        if config.WEBCAM_AUTOFOCUS is not None:
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS,
                         1 if config.WEBCAM_AUTOFOCUS else 0)
            if not config.WEBCAM_AUTOFOCUS and config.WEBCAM_FOCUS is not None:
                self.cap.set(cv2.CAP_PROP_FOCUS, config.WEBCAM_FOCUS)

    @staticmethod
    def _fit(frame):
        """Centre-crop to the target aspect ratio, then scale — a 4:3 camera
        must never be squeezed into the 16:9 canvas (squashed faces!)."""
        tw, th = config.FRAME_SIZE
        h, w = frame.shape[:2]
        target = tw / th
        if abs(w / h - target) > 0.01:
            if w / h > target:                    # too wide → trim sides
                new_w = int(h * target)
                x0 = (w - new_w) // 2
                frame = frame[:, x0:x0 + new_w]
            else:                                 # too tall (4:3) → trim bands
                new_h = int(w / target)
                y0 = (h - new_h) // 2
                frame = frame[y0:y0 + new_h]
        if (frame.shape[1], frame.shape[0]) != (tw, th):
            frame = cv2.resize(frame, (tw, th),
                               interpolation=cv2.INTER_AREA)
        return frame

    def read(self):
        ok, frame = self.cap.read()
        if not ok or frame is None or frame.size == 0:
            raise RuntimeError("Webcam stopped delivering frames")
        return self._fit(frame)

    def close(self):
        self.cap.release()


class FakeSource:
    """Synthetic moving test pattern, for development without a camera.

    Emits two moving objects and matching fake detections whose confidence
    oscillates — so the threshold slider and every station can be tried out.
    """

    name = "Testbild"

    def __init__(self):
        self.t0 = time.time()

    def read(self):
        w, h = config.FRAME_SIZE
        t = time.time() - self.t0

        # soft vertical gradient background
        frame = np.zeros((h, w, 3), np.uint8)
        frame[:] = (40, 32, 24)
        frame[:, :, 0] += (np.linspace(0, 60, h, dtype=np.uint8))[:, None]

        # bouncing ball
        bx = int(w * (0.5 + 0.38 * math.sin(t * 0.9)))
        by = int(h * (0.5 + 0.30 * math.sin(t * 1.7 + 1)))
        cv2.circle(frame, (bx, by), 34, (60, 200, 255), -1)
        cv2.circle(frame, (bx, by), 34, (30, 120, 200), 3)

        # drifting "book" rectangle
        rx = int(w * (0.5 + 0.35 * math.cos(t * 0.5)))
        ry = int(h * 0.65)
        cv2.rectangle(frame, (rx - 45, ry - 28), (rx + 45, ry + 28), (80, 160, 60), -1)
        cv2.rectangle(frame, (rx - 45, ry - 28), (rx + 45, ry + 28), (50, 100, 40), 3)

        cv2.putText(frame, "TESTBILD (keine Kamera)", (12, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 140), 1, cv2.LINE_AA)

        self._last = (t, bx, by, rx, ry)
        return frame

    @property
    def fake_detections(self):
        """[(class_id, confidence, (x0, y0, x1, y1) normalised)] like Hailo."""
        w, h = config.FRAME_SIZE
        t, bx, by, rx, ry = self._last
        ball_conf = 0.55 + 0.35 * math.sin(t * 0.7)          # oscillates 0.20–0.90
        book_conf = 0.65 + 0.25 * math.sin(t * 0.4 + 2)
        return [
            (32, max(0.05, ball_conf),                        # sports ball
             ((bx - 40) / w, (by - 40) / h, (bx + 40) / w, (by + 40) / h)),
            (73, max(0.05, book_conf),                        # book
             ((rx - 50) / w, (ry - 34) / h, (rx + 50) / w, (ry + 34) / h)),
        ]

    def close(self):
        pass


def _try_open(kind, webcam_index=0):
    """Open one concrete source or return None — never raises."""
    try:
        if kind == "picamera":
            return PiCameraSource()
        if kind == "webcam":
            return WebcamSource(webcam_index)
        if kind == "fake":
            return FakeSource()
    except Exception:
        return None
    return None


class CameraManager:
    """Self-healing frame source for unattended use (schools, exhibitions).

    Wraps whichever camera is available (Pi/CSI camera incl. the AI Camera,
    or any USB webcam) and guarantees that read() ALWAYS returns a frame:

    - a few read errors in a row → the source is considered dead, gets
      closed, and read() switches to a friendly bilingual placeholder frame
      ("check the cable") instead of a frozen/broken picture;
    - in the background it keeps trying to reopen a camera every few
      seconds (Pi camera first, then USB indices 0-3) and switches back
      the moment one answers — unplugging and replugging just works;
    - `fake` mode is explicit dev behaviour and is never left automatically.

    The pipeline needs no special cases: `connected` and `name` feed the
    status line, everything else is a normal source.
    """

    FAIL_LIMIT = 5           # consecutive read errors → source is dead
    RETRY_EVERY = 3.0        # seconds between reconnect attempts
    WEBCAM_INDICES = (0, 1, 2, 3)   # a replugged USB cam may change index

    def __init__(self, kind="auto", webcam_index=0):
        self.kind = kind
        self.webcam_index = webcam_index
        self.reconnects = 0
        self._fails = 0
        self._blink = 0
        self._log = logging.getLogger("camera")
        self._lock = threading.Lock()   # guards _source and _pending
        self._pending = None            # opened+verified by the prober thread
        self._closing = False
        # Initial open happens synchronously (we are still in startup) but
        # WITH the sanity read: a half-seated ribbon must degrade to the
        # placeholder, not into a boot loop of watchdog restarts.
        self._source = self._open_any()
        if self._source is None:
            self._log.warning("No camera at startup — showing placeholder, "
                              "probing continues in the background")
        # Reconnect probing runs on its own thread: opening cameras can
        # block for seconds, and the pipeline must keep streaming the
        # placeholder at full rate meanwhile.
        self._prober = threading.Thread(target=self._probe_loop, daemon=True,
                                        name="camera-prober")
        self._prober.start()

    # -- source discovery ---------------------------------------------------

    def _candidate_indices(self):
        seen, out = set(), []
        for idx in (self.webcam_index, *self.WEBCAM_INDICES):
            if idx not in seen:
                seen.add(idx)
                out.append(idx)
        return out

    def _open_any(self):
        """Open AND verify (one real frame) a source; None if unavailable."""
        if self.kind == "fake":
            return FakeSource()
        candidates = []
        if self.kind in ("picamera", "auto"):
            candidates.append(("picamera", 0))
        if self.kind in ("webcam", "auto"):
            candidates += [("webcam", i) for i in self._candidate_indices()]
        for kind, idx in candidates:
            src = _try_open(kind, idx)
            if src is None:
                continue
            try:
                src.read()               # sanity: must deliver a real frame
                return src
            except Exception:
                try:
                    src.close()
                except Exception:
                    pass
        return None

    def _probe_loop(self):
        while not self._closing:
            time.sleep(self.RETRY_EVERY)
            with self._lock:
                idle = self._source is None and self._pending is None
            if not idle:
                continue
            src = self._open_any()       # may take seconds — that's fine here
            if src is not None:
                with self._lock:
                    if self._source is None and not self._closing:
                        self._pending = src
                    else:                # raced: someone else got there
                        try:
                            src.close()
                        except Exception:
                            pass

    # -- public interface ---------------------------------------------------

    @property
    def connected(self):
        return self._source is not None

    @property
    def name(self):
        return self._source.name if self._source else "Keine Kamera"

    @property
    def fake_detections(self):
        # pass-through so the demo pipeline keeps working in fake mode
        if isinstance(self._source, FakeSource):
            return self._source.fake_detections
        return []

    def read(self):
        """Always returns a BGR frame at FRAME_SIZE. Never raises, and never
        blocks longer than one bounded source read."""
        if self._source is not None:
            try:
                frame = self._source.read()
                self._fails = 0
                return frame
            except Exception:
                self._fails += 1
                if self._fails >= self.FAIL_LIMIT:
                    self._drop_source()
                else:
                    time.sleep(0.05)     # brief hiccup — don't spin hot
                    return self._placeholder(brief=True)
        # adopt whatever the background prober has verified for us
        with self._lock:
            if self._pending is not None:
                self._source, self._pending = self._pending, None
                self._fails = 0
                self.reconnects += 1
                self._log.info("Camera back: %s (reconnect #%d)",
                               self._source.name, self.reconnects)
                return self._placeholder()   # next read delivers live frames
        return self._placeholder()

    def close(self):
        self._closing = True
        with self._lock:
            pending, self._pending = self._pending, None
        if pending is not None:
            try:
                pending.close()
            except Exception:
                pass
        self._drop_source(log=False)

    # -- internals ----------------------------------------------------------

    def _drop_source(self, log=True):
        src, self._source = self._source, None
        if src is not None:
            if log:
                self._log.warning("Camera lost (%s) — showing placeholder, "
                                  "probing for reconnection", src.name)
            try:
                src.close()
            except Exception:
                pass
        self._fails = 0

    def _placeholder(self, brief=False):
        """Friendly bilingual 'no camera' frame — for facilitators who
        cannot debug: it says what to do and heals on its own."""
        w, h = config.FRAME_SIZE
        frame = np.zeros((h, w, 3), np.uint8)
        frame[:] = (23, 17, 13)
        self._blink += 1
        f = cv2.FONT_HERSHEY_SIMPLEX
        cx = w // 2
        # camera pictogram
        bx0, by0, bx1, by1 = cx - 42, h // 2 - 78, cx + 30, h // 2 - 30
        cv2.rectangle(frame, (bx0, by0), (bx1, by1), (90, 100, 110), 3)
        cv2.rectangle(frame, (bx1, by0 + 10), (bx1 + 22, by1 - 10),
                      (90, 100, 110), 3)
        if (self._blink // 15) % 2 == 0:   # gentle blink = alive, not frozen
            cv2.line(frame, (bx0 - 14, by1 + 14), (bx1 + 34, by0 - 14),
                     (60, 60, 230), 4)
        msgs = [("Keine Kamera gefunden", 0.85, (235, 235, 235)),
                ("Bitte Kamera-Kabel pruefen - ich versuche es weiter ...",
                 0.55, (170, 175, 185)),
                ("No camera found - check the cable, retrying ...",
                 0.5, (130, 135, 145))]
        if brief:
            msgs[0] = ("Kamerabild stockt ...", 0.85, (235, 235, 235))
        y = h // 2 + 16
        for text, size, col in msgs:
            (tw, _), _ = cv2.getTextSize(text, f, size, 2)
            cv2.putText(frame, text, (cx - tw // 2, y), f, size, col, 2,
                        cv2.LINE_AA)
            y += 34
        return frame


def open_source(kind="auto", webcam_index=0):
    """Open the self-healing camera manager (see CameraManager)."""
    return CameraManager(kind, webcam_index)
