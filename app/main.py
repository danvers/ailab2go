#!/usr/bin/env python3
"""KI-Werkstatt — an interactive computer-vision & privacy-literacy exhibit
for the Raspberry Pi 5 with AI HAT.

Run on the Pi:      python3 app/main.py
Dev on a laptop:    python3 app/main.py --source webcam   (or --source fake)
"""

import argparse
import logging

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


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
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

    app = webserver.create_app(pipeline)
    log.info("Serving on http://%s:%d — students join the hotspot and open "
             "http://10.42.0.1%s", args.host, args.port,
             "" if args.port == 80 else f":{args.port}")
    try:
        app.run(host=args.host, port=args.port, threaded=True,
                use_reloader=False)
    finally:
        pipeline.stop()
        source.close()
        # Deliberately NOT closing the Hailo handles: tearing down two model
        # instances raced a C++ "Resource deadlock avoided" abort in testing.
        # Process exit cleans up the device just fine.


if __name__ == "__main__":
    main()
