"""Frame sources: Pi camera, USB webcam, or a synthetic test pattern.

All sources deliver BGR frames at config.FRAME_SIZE via read().
The fake source additionally exposes fake_detections so the whole UI can be
demoed on a laptop without any camera or AI hardware.
"""

import math
import time

import cv2
import numpy as np

import config


class PiCameraSource:
    """CSI camera (e.g. Camera Module 3) via picamera2."""

    name = "Pi-Kamera"

    def __init__(self):
        from picamera2 import Picamera2  # lazy: only available on the Pi

        self.picam2 = Picamera2()
        cam_config = self.picam2.create_video_configuration(
            main={"size": config.FRAME_SIZE, "format": "XRGB8888"}
        )
        self.picam2.configure(cam_config)
        self.picam2.start()
        try:  # continuous autofocus (Camera Module 3; older modules lack AF)
            from libcamera import controls
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        except Exception:
            pass

    def read(self):
        arr = self.picam2.capture_array()
        # XRGB8888 memory layout is B,G,R,X — drop X and we have OpenCV BGR.
        return arr[:, :, :3].copy()

    def close(self):
        self.picam2.stop()


class WebcamSource:
    """Any UVC webcam via OpenCV (also used for laptop dev mode)."""

    name = "USB-Webcam"

    def __init__(self, index=0):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Webcam {index} could not be opened")
        w, h = config.FRAME_SIZE
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("Webcam stopped delivering frames")
        if (frame.shape[1], frame.shape[0]) != config.FRAME_SIZE:
            frame = cv2.resize(frame, config.FRAME_SIZE)
        return frame

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


def open_source(kind="auto", webcam_index=0):
    """Open the requested frame source; 'auto' prefers the Pi camera."""
    if kind == "fake":
        return FakeSource()
    if kind == "webcam":
        return WebcamSource(webcam_index)
    if kind == "picamera":
        return PiCameraSource()
    # auto
    try:
        return PiCameraSource()
    except Exception:
        pass
    try:
        return WebcamSource(webcam_index)
    except Exception:
        pass
    return FakeSource()
