"""Central configuration for the KI-Werkstatt exhibit app.

Everything an event facilitator might want to tweak lives here.
"""

# --- Video -----------------------------------------------------------------
FRAME_SIZE = (640, 360)     # display/stream resolution (16:9)
JPEG_QUALITY = 70           # stream compression (lower = less bandwidth)
STREAM_MAX_FPS = 12         # per-client cap, keeps the hotspot happy
MAX_STREAM_CLIENTS = 30     # hard cap on simultaneous MJPEG viewers

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
DETECT_THRESHOLD_DEFAULT = 0.5   # confidence slider start value
TEACH_MIN_SAMPLES = 5            # per class before predictions start
TEACH_KNN_K = 7
FACE_DETECT_EVERY_N_FRAMES = 2   # Haar cascade cost saver
FACE_GUARD_GLOBAL_DEFAULT = True # anonymise faces in every station by default

# --- Exhibit / admin -------------------------------------------------------
ADMIN_PIN = "2468"          # unlocks the moderator bar in the web UI
EVENT_NAME = "KI-Werkstatt" # shown in the header
