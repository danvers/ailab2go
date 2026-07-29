#!/usr/bin/env python3
"""KI-Werkstatt — an interactive computer-vision & privacy-literacy exhibit
for the Raspberry Pi 5 with AI HAT.

Run on the Pi:      python3 app/main.py
Dev on a laptop:    python3 app/main.py --source webcam   (or --source fake)
"""

import argparse
import logging
import os
import threading
import time

import camera
import config
import stations
import vision
import webserver


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["auto", "picamera", "webcam", "fake"],
                        default="auto", help="frame source (default: auto)")
    parser.add_argument("--webcam-index", type=int, default=0)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--hef", default=None,
                        help="path to a specific Hailo .hef model")
    return parser.parse_args()


def _start_watchdog(pipeline, log):
    """Last line of defence for unattended use: if the frame loop stops
    making progress (a wedged camera/AI driver can block a read forever),
    exit the process — systemd restarts it within seconds with a clean
    camera re-detection. An unplugged camera does NOT trigger this: the
    placeholder frames keep the loop progressing on purpose.
    """
    def watch():
        last, stalled = -1, 0
        while True:
            time.sleep(10)
            current = pipeline.published_total
            if current != last:
                last, stalled = current, 0
                continue
            stalled += 10
            if stalled >= 60:
                log.error("Watchdog: pipeline stalled for 60 s - exiting "
                          "so systemd can restart us cleanly")
                os._exit(70)
    threading.Thread(target=watch, daemon=True, name="watchdog").start()


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    # Werkzeug logs every HTTP request at INFO — with 30 phones polling each
    # second that is millions of journald lines per day on the SD card.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    log = logging.getLogger("ki-werkstatt")
    args = parse_args()

    if args.hef:
        config.HEF_CANDIDATES.insert(0, args.hef)

    source = camera.open_source(args.source, args.webcam_index)
    log.info("Frame source: %s", source.name)

    detector, detector_status = vision.open_detector()
    log.info("AI accelerator: %s", detector_status)

    pose, pose_status = vision.open_pose() if detector else (None, "ohne KI-Chip")
    log.info("Pose model: %s", pose_status)

    pipeline = stations.Pipeline(source, detector, detector_status,
                                 pose, pose_status)
    log.info("Face guard backend: %s", pipeline.faces.backend)
    pipeline.start()
    _start_watchdog(pipeline, log)

    app = webserver.create_app(pipeline)
    log.info("Serving on http://%s:%d — students join the hotspot and open "
             "http://10.42.0.1%s", args.host, args.port,
             "" if args.port == 80 else f":{args.port}")
    # Bounded sends: an MJPEG write to a phone that walked out of Wi-Fi
    # range would otherwise block its thread (and stream slot) for many
    # minutes of TCP retries.
    from werkzeug.serving import WSGIRequestHandler

    class TimeoutHandler(WSGIRequestHandler):
        timeout = 30

    try:
        app.run(host=args.host, port=args.port, threaded=True,
                use_reloader=False, request_handler=TimeoutHandler)
    finally:
        pipeline.stop()
        source.close()
        # Deliberately NOT closing the Hailo handles: tearing down two model
        # instances raced a C++ "Resource deadlock avoided" abort in testing.
        # Process exit cleans up the device just fine.


if __name__ == "__main__":
    main()
