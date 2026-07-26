"""Flask web app: MJPEG stream + JSON API for the exhibit UI."""

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

    @app.get("/stream.mjpg")
    def stream():
        if pipeline.stream_clients >= config.MAX_STREAM_CLIENTS:
            return "Zu viele Zuschauer — bitte später erneut versuchen.", 503

        def generate():
            pipeline.stream_clients += 1
            min_interval = 1.0 / config.STREAM_MAX_FPS
            last = 0.0
            try:
                while pipeline.running:
                    with pipeline.frame_ready:
                        pipeline.frame_ready.wait(timeout=2.0)
                        jpeg = pipeline.jpeg
                    if jpeg is None:
                        continue
                    now = time.time()
                    if now - last < min_interval:
                        time.sleep(min_interval - (now - last))
                    last = time.time()
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
            finally:
                pipeline.stream_clients -= 1

        return Response(generate(),
                        mimetype="multipart/x-mixed-replace; boundary=frame")

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
        return jsonify(ok=True)

    # The teach/heatmap endpoints all change shared room state (and two of
    # them destroy data everyone contributed), so they respect the lock.

    @app.post("/api/teach/capture")
    def teach_capture():
        payload = request.get_json(force=True, silent=True) or {}
        if not _allowed(payload):
            return jsonify(error="locked"), 403
        count = pipeline.teach_capture(payload.get("slot", ""))
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
