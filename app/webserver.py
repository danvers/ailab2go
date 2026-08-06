"""Flask web app: MJPEG stream + JSON API for the exhibit UI."""

import threading
import time

import ipaddress

from flask import Flask, Response, jsonify, redirect, render_template, request

import config
import vision


def create_app(pipeline):
    app = Flask(__name__)

    def _pin_ok(payload):
        return payload.get("pin") == config.ADMIN_PIN

    def _allowed(payload):
        """Station switching etc. — blocked for guests while locked."""
        return not pipeline.locked or _pin_ok(payload)

    # Captive portal, part 2: with the hotspot DNS answering every name
    # with our IP, any request addressed to a HOSTNAME (Apple/Android/
    # Windows connectivity probes, or someone typing example.com) lands
    # here. The flow mirrors a real hotel portal:
    #   1. Unknown device probes → 302 to the exhibit → the phone pops its
    #      "sign in to network" sheet showing the start page.
    #   2. Loading the exhibit once "signs the device in": its later probes
    #      get the answer the OS expects (204/"Success"), so the phone treats
    #      the Wi-Fi as usable and the normal browser reaches 10.10.10.1
    #      after the sheet closes. Honest limit: Android 9+ additionally
    #      probes https://… — port 443 answers nothing here (serving a fake
    #      cert would be worse), so Android shows ONE "stay connected?"
    #      dialog; after confirming, everything works. Without the sign-in
    #      step phones route browser traffic to mobile data instead.
    # Requests aimed at an IP, localhost or .local always pass untouched,
    # so ethernet/dev access keeps working no matter which address is used.
    PROBE_SUCCESS = {
        "/generate_204": ("", 204, {}),                       # Android
        "/gen_204": ("", 204, {}),
        "/hotspot-detect.html": (                             # Apple
            "<HTML><HEAD><TITLE>Success</TITLE></HEAD>"
            "<BODY>Success</BODY></HTML>", 200,
            {"Content-Type": "text/html"}),
        "/library/test/success.html": (                       # older iOS
            "<HTML><HEAD><TITLE>Success</TITLE></HEAD>"
            "<BODY>Success</BODY></HTML>", 200,
            {"Content-Type": "text/html"}),
        "/connecttest.txt": ("Microsoft Connect Test", 200,   # Windows
                             {"Content-Type": "text/plain"}),
        "/ncsi.txt": ("Microsoft NCSI", 200,
                      {"Content-Type": "text/plain"}),
        "/success.txt": ("success\n", 200,                    # Firefox
                         {"Content-Type": "text/plain"}),
        "/canonical.html": (                                  # Firefox portal
            '<meta http-equiv="refresh" '
            'content="0;url=https://support.mozilla.org/kb/captive-portal"/>',
            200, {"Content-Type": "text/html"}),
        "/check_network_status.txt": (                        # GNOME/Fedora
            "NetworkManager is online\n", 200,
            {"Content-Type": "text/plain"}),
        "/nm": ("NetworkManager is online\n", 200,           # Debian NM
                {"Content-Type": "text/plain"}),
    }
    # Ubuntu's NetworkManager probes "/" on this host and expects 204 — the
    # generic "/" redirect must not apply there once the device is signed in.
    PROBE_204_HOSTS = ("connectivity-check.ubuntu.com",)
    # Sign-ins expire: a device that rejoins hours later should get the
    # welcome sheet again (and a recycled DHCP address must not inherit an
    # old sign-in forever). 2 h comfortably outlasts one visit.
    SIGNIN_TTL = 2 * 3600
    signed_in = {}      # client IP -> monotonic time of sign-in

    def sign_in(ip):
        signed_in[ip] = time.monotonic()

    def is_signed_in(ip):
        ts = signed_in.get(ip)
        if ts is None:
            return False
        if time.monotonic() - ts > SIGNIN_TTL:
            signed_in.pop(ip, None)
            return False
        return True

    @app.before_request
    def captive_redirect():
        host = (request.host or "").lower()
        if host.startswith("["):                  # [fdfb::1]:80 → fdfb::1
            host = host[1:].split("]", 1)[0]
        else:                                     # example.com:8099 → example.com
            host = host.split(":", 1)[0]
        is_ours = host == "localhost" or host.endswith(".local")
        if not is_ours:
            try:
                ipaddress.ip_address(host)
                is_ours = True                    # explicit IP — ours
            except ValueError:
                pass
        if is_ours:
            if request.path == "/":               # the exhibit was opened
                sign_in(request.remote_addr)
            return None
        # foreign hostname: an OS connectivity probe or a typed URL
        if is_signed_in(request.remote_addr):
            if host.endswith(PROBE_204_HOSTS):
                return Response("", 204)
            probe = PROBE_SUCCESS.get(request.path)
            if probe is not None:
                body, code, headers = probe
                return Response(body, code, headers)
            # signed in + typing any address in the real browser → straight
            # to the exhibit; the welcome sheet is for first contact only
            return redirect(config.PUBLIC_URL.rstrip("/") + "/", code=302)
        return redirect(config.PUBLIC_URL.rstrip("/") + "/portal", code=302)

    @app.get("/")
    def index():
        return render_template("index.html", event_name=config.EVENT_NAME)

    @app.get("/portal")
    def portal():
        """Captive-portal landing page: poster look, one big button.
        Loading it does NOT sign the device in — only the button
        (→ /portal/go) does, so the sheet isn't dismissed before the tap."""
        return render_template(
            "portal.html", event_name=config.EVENT_NAME,
            url_short=config.PUBLIC_URL.rstrip("/").removeprefix("http://"))

    @app.get("/portal/go")
    def portal_go():
        """The button target: sign the device in, then guide it OUT of the
        captive sheet. There is NO reliable programmatic escape from these
        webviews (the x-safari:// scheme errors on current iOS — tried), so
        the page teaches each platform its own supported exit: iOS "Done"
        keeps the Wi-Fi BECAUSE the sign-in makes the next probe succeed;
        Android's sheet menu has a built-in "open in browser"."""
        sign_in(request.remote_addr)
        ua = (request.user_agent.string or "").lower()
        platform = ("ios" if any(k in ua for k in ("iphone", "ipad", "ipod"))
                    else "android" if "android" in ua else "other")
        base = config.PUBLIC_URL.rstrip("/")
        return render_template(
            "portal_done.html", event_name=config.EVENT_NAME,
            platform=platform, url=base,
            url_short=base.removeprefix("http://"))

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

    # stream_clients is no longer display-only: the camera-standby feature
    # powers the camera down when it reads 0, so lost increments/decrements
    # would sleep a watched camera (or keep an unwatched one hot). += is not
    # atomic across Flask threads — guard it.
    clients_lock = threading.Lock()

    @app.get("/stream.mjpg")
    def stream():
        if not stream_slots.acquire(blocking=False):
            return "Zu viele Zuschauer — bitte später erneut versuchen.", 503
        with clients_lock:
            pipeline.stream_clients += 1

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
                with clients_lock:
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
