"""Central configuration for the KI-Werkstatt exhibit app.

Everything an event facilitator might want to tweak lives here.
"""

# --- Video -----------------------------------------------------------------
FRAME_SIZE = (640, 360)     # display/stream resolution (16:9)
JPEG_QUALITY = 70           # stream compression (lower = less bandwidth)
STREAM_MAX_FPS = 24         # per-client ceiling with FEW viewers; the
                            # cap scales down as viewers join (24 up to 4,
                            # 15 up to 8, 10 beyond) so a full class does
                            # not saturate the hotspot radio.
PROCESS_MAX_FPS = 30        # video passes (overlays + JPEG) per second.
                            # Keep this AT or ABOVE the camera rate: frames
                            # arrive on the camera's grid, so a cap between
                            # half and full rate just quantizes DOWN (a 24
                            # cap on a 30 fps camera lands on 15), and the
                            # per-viewer caps then starve on a slow
                            # publisher. Cheap per-frame work (draw + JPEG)
                            # makes full rate affordable — the heat lives
                            # in INFER_MAX_FPS below.
INFER_MAX_FPS = 12          # AI passes (Hailo detect/pose, trainer) per
                            # second — heat. Video and AI are decoupled:
                            # frames publish at PROCESS_MAX_FPS with the
                            # latest smoothed overlays drawn on, while the
                            # accelerator only runs this often.
WEBCAM_FPS = 20             # requested from USB cameras (phone stream is
                            # capped at 12 fps anyway). NOTE: many UVC models
                            # only offer fixed rates per mode — the ELP 48MP
                            # ignores this at 720p and always runs 30 fps.
MAX_STREAM_CLIENTS = 30     # hard cap on simultaneous MJPEG viewers

# Camera standby: after this many seconds with NO connected viewer the
# camera is closed — it cools down (the ELP 48MP runs hot) and, fittingly
# for a privacy exhibit, literally stops filming when nobody watches.
# It wakes automatically within ~2 s when the next person joins. 0 = never.
CAMERA_STANDBY_AFTER = 600

# USB camera autofocus. None = leave the camera's default (ELP: continuous
# AF). False = switch AF off and use WEBCAM_FOCUS — saves a little power/
# heat and stops focus hunting when people wave; the right focus value is
# camera-specific (ELP scale 0-1023ish, try on site), so test before events.
WEBCAM_AUTOFOCUS = None
WEBCAM_FOCUS = None

# --- Hailo / AI HAT --------------------------------------------------------
# The first existing .hef wins. Add your own path first if you use a custom
# model. hailo-models ships these under /usr/share/hailo-models/.
# NOTE: install the matching runtime — hailo-h10-all for the AI HAT+ 2
# (Hailo-10H), hailo-all for AI Kit / AI HAT+ (Hailo-8/8L).
HEF_CANDIDATES = [
    "/usr/share/hailo-models/yolov8m_h10.hef",   # AI HAT+ 2 (Hailo-10H)
    "/usr/share/hailo-models/yolov11m_h10.hef",  # AI HAT+ 2 alternative
    "/usr/share/hailo-models/yolov8s_h8l.hef",   # AI Kit / AI HAT+ 13 TOPS (Hailo-8L)
    "/usr/share/hailo-models/yolov8s_h8.hef",    # AI HAT+ 26 TOPS (Hailo-8)
    "/usr/share/hailo-models/yolov6n_h8l.hef",
]
# The model expects RGB input. Set to False if colours in detections seem
# off (red/blue swapped) on your setup.
MODEL_EXPECTS_RGB = True

# Pose estimation (Skelett-Spiegel station). Same rule: first existing wins.
POSE_HEF_CANDIDATES = [
    "/usr/share/hailo-models/yolov8s_pose_h10.hef",   # AI HAT+ 2 (Hailo-10H)
    "/usr/share/hailo-models/yolov8s_pose_h8.hef",    # Hailo-8
    "/usr/share/hailo-models/yolov8s_pose_h8l_pi.hef",  # Hailo-8L
]
POSE_SCORE_THRESHOLD = 0.5   # person confidence for skeletons
POSE_KPT_THRESHOLD = 0.3     # per-joint confidence to draw/use a keypoint
POSE_HOLD_SECONDS = 0.8      # how long a pose must be held to pass a challenge

# --- Stations --------------------------------------------------------------
DEFAULT_MODE = "start"
DETECT_THRESHOLD_DEFAULT = 0.4   # confidence slider start value — COCO
                                 # scores real-world props conservatively;
                                 # 0.5 hid too much (the slider stays)
# Steadiness of the detection overlay (anti-flicker). An object must be seen
# for ENTER consecutive frames before it appears, and survives HOLD frames of
# dropout before it disappears. Higher = calmer but more sluggish.
DETECT_STEADY_ENTER = 3
DETECT_STEADY_HOLD = 8
TEACH_MIN_SAMPLES = 5            # per class before predictions start
TEACH_KNN_K = 7
FACE_DETECT_EVERY_N_FRAMES = 2   # Haar cascade cost saver
FACE_GUARD_GLOBAL_DEFAULT = True # anonymise faces in every station by default

# --- Beamer / exhibition view ---------------------------------------------
# /beamer is a passive full-screen wall display (projector or TV): live
# stream, big counters, rotating "did you know" facts. No controls.
EXHIBIT_AUTOROTATE = True     # tour the stations while nobody interacts
EXHIBIT_IDLE_AFTER = 300      # seconds without interaction → attract mode.
                              # Generous on purpose: someone holding props
                              # in front of the camera taps nothing for a
                              # while — at 90 s the tour yanked the station
                              # away mid-experiment (and, since the
                              # reset-on-switch feature, snapped their
                              # threshold slider back too).
EXHIBIT_ROTATE_EVERY = 25     # seconds per station while touring
EXHIBIT_TOUR = ["detektiv", "schild", "pose", "spur"]  # the visual ones

# What the wall display tells passers-by (must match setup/hotspot.sh)
PUBLIC_URL = "http://10.10.10.1"
HOTSPOT_SSID = "KI-Werkstatt"

# --- Exhibit / admin -------------------------------------------------------
ADMIN_PIN = "2468"          # unlocks the moderator bar in the web UI.
# The PIN can be changed in the /system window; the choice is stored in
# PIN_FILE (outside /opt, so deploys and reboots keep it). Forgot it?
# Delete that file on the Pi and restart — the value above applies again.
PIN_FILE = "/var/lib/ki-werkstatt/pin"
try:
    with open(PIN_FILE) as _f:
        ADMIN_PIN = _f.read().strip() or ADMIN_PIN
except OSError:
    pass
EVENT_NAME = "KI-Werkstatt" # shown in the header (German)
EVENT_NAME_EN = "AI-Lab2go"  # the same exhibit when the UI runs in English
# Language of the captive welcome pages (Wi-Fi login) and /system:
#   "auto" — follow each phone's own language (German otherwise)
#   "de" / "en" — force ONE language for the whole event; set this once
#                 when you configure the kit for a German or English group
PORTAL_LANG = "auto"
