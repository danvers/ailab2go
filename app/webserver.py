"""Flask web app: MJPEG stream + JSON API for the exhibit UI."""

import threading
import time

from flask import Flask, Response, jsonify, render_template, request

import config
import vision


def create_app(pipeline):
    app = Flask(__name__)

    def _pin_ok(payload):
        return payload.get("pin") == config.ADMIN_PIN

    def _allowed(payload):
        """Station switching etc. — blocked for guests while locked."""
        return not pipeline.locked or _pin_ok(payload)

    @app.get("/")
    def index():
        return render_template("index.html", event_name=config.EVENT_NAME)

    @app.get("/system")
    def system():
        """Technical readout in its own window: temperatures, fan, camera.
        Deliberately off the visitor UI — nobody at a station needs this,
        but a facilitator debugging a warm or stuttering exhibit does."""
        return render_template("system.html", event_name=config.EVENT_NAME)

    @app.get("/beamer")
    def beamer():
        # QR for passers-by; python3-qrcode is installed by install.sh, but
        # the wall must not break without it
        qr_uri = ""
        try:
            import base64
            import io
            import qrcode
            buf = io.BytesIO()
            qrcode.make(config.PUBLIC_URL, box_size=8, border=1).save(buf, "PNG")
            qr_uri = ("data:image/png;base64," +
                      base64.b64encode(buf.getvalue()).decode())
        except Exception:
            pass
        return render_template("beamer.html", event_name=config.EVENT_NAME,
                               qr_uri=qr_uri, public_url=config.PUBLIC_URL,
                               ssid=config.HOTSPOT_SSID)

    # Stream slots: a semaphore is atomic (the old check-then-act counter
    # could overshoot under simultaneous joins), and call_on_close releases
    # the slot exactly once even if the generator never starts.
    stream_slots = threading.BoundedSemaphore(config.MAX_STREAM_CLIENTS)

    @app.get("/stream.mjpg")
    def stream():
        if not stream_slots.acquire(blocking=False):
            return "Zu viele Zuschauer — bitte später erneut versuchen.", 503
        pipeline.stream_clients += 1     # display only; slots gate for real

        # Slot release is belt-and-braces: call_on_close AND the generator's
        # finally. Relying on call_on_close alone leaked slots in the field
        # (clients vanished without werkzeug ever closing the response, and
        # after enough churn the wall went dark with "Zu viele Zuschauer").
        # The finally fires at the latest when the abandoned generator is
        # garbage-collected, so a slot can no longer be lost for good. The
        # once-lock keeps the pair idempotent — BoundedSemaphore raises on
        # a double release.
        release_once = threading.Lock()

        def release():
            if release_once.acquire(blocking=False):
                pipeline.stream_clients = max(0, pipeline.stream_clients - 1)
                stream_slots.release()

        def generate():
            try:
                min_interval = 1.0 / config.STREAM_MAX_FPS
                last = 0.0
                while pipeline.running:
                    with pipeline.frame_ready:
                        pipeline.frame_ready.wait(timeout=2.0)
                        jpeg = pipeline.jpeg
                    if jpeg is None:
                        continue
                    now = time.monotonic()
                    if now - last < min_interval:
                        time.sleep(min_interval - (now - last))
                    last = time.monotonic()
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
            finally:
                release()

        resp = Response(generate(),
                        mimetype="multipart/x-mixed-replace; boundary=frame")
        resp.call_on_close(release)
        return resp

    @app.get("/api/state")
    def state():
        return jsonify(pipeline.state)

    @app.post("/api/mode")
    def set_mode():
        payload = request.get_json(force=True, silent=True) or {}
        if not _allowed(payload):
            return jsonify(error="locked"), 403
        if not pipeline.set_mode(payload.get("mode", "")):
            return jsonify(error="unknown mode"), 400
        pipeline.touch()
        return jsonify(ok=True)

    @app.post("/api/params")
    def set_params():
        payload = request.get_json(force=True, silent=True) or {}
        if "threshold" in payload:  # pedagogical, harmless — never locked
            try:
                pipeline.threshold = min(0.95, max(0.05, float(payload["threshold"])))
            except (TypeError, ValueError):
                pass
        # Privacy/pose switches affect every viewer in the room — while the
        # moderator lock is on, guests must not be able to flip them
        # (especially not switch the face shield OFF).
        guarded = {"privacy_on", "privacy_style", "pose_ghost"}
        if guarded & payload.keys() and not _allowed(payload):
            return jsonify(error="locked"), 403
        if "privacy_on" in payload:
            pipeline.privacy_on = bool(payload["privacy_on"])
        if payload.get("privacy_style") in vision.FaceGuard.STYLES:
            pipeline.privacy_style = payload["privacy_style"]
        if "pose_ghost" in payload:
            # Only meaningful with a pose model; without one the "ghost" frame
            # would be raw camera video (see stations.Pipeline._process).
            pipeline.pose_ghost = bool(payload["pose_ghost"]) \
                and pipeline.pose is not None
        pipeline.touch()
        return jsonify(ok=True)

    # The teach/heatmap endpoints all change shared room state (and two of
    # them destroy data everyone contributed), so they respect the lock.

    @app.post("/api/teach/capture")
    def teach_capture():
        payload = request.get_json(force=True, silent=True) or {}
        if not _allowed(payload):
            return jsonify(error="locked"), 403
        count = pipeline.teach_capture(payload.get("slot", ""))
        pipeline.touch()
        return jsonify(ok=count > 0, count=count)

    @app.post("/api/teach/rename")
    def teach_rename():
        payload = request.get_json(force=True, silent=True) or {}
        if not _allowed(payload):
            return jsonify(error="locked"), 403
        pipeline.teach.rename(payload.get("slot", ""), payload.get("name", ""))
        return jsonify(ok=True)

    @app.post("/api/teach/reset")
    def teach_reset():
        payload = request.get_json(force=True, silent=True) or {}
        if not _allowed(payload):
            return jsonify(error="locked"), 403
        pipeline.teach.reset()
        return jsonify(ok=True)

    @app.post("/api/heatmap/reset")
    def heatmap_reset():
        payload = request.get_json(force=True, silent=True) or {}
        if not _allowed(payload):
            return jsonify(error="locked"), 403
        pipeline.heatmap.reset()
        return jsonify(ok=True)

    @app.post("/api/admin")
    def admin():
        payload = request.get_json(force=True, silent=True) or {}
        if not _pin_ok(payload):
            return jsonify(error="wrong pin"), 403
        action = payload.get("action")
        if action == "lock":
            pipeline.locked = True
        elif action == "unlock":
            pipeline.locked = False
        elif action == "reset_all":
            pipeline.reset_all()
        else:
            return jsonify(error="unknown action"), 400
        return jsonify(ok=True, locked=pipeline.locked)

    return app
