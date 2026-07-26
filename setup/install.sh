#!/usr/bin/env bash
# One-shot installer for the KI-Werkstatt exhibit.
# Run on Raspberry Pi OS Bookworm (64-bit) on a Raspberry Pi 5:
#   bash setup/install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR=/opt/ki-werkstatt

echo "══════════════════════════════════════════════════"
echo "  KI-Werkstatt installer"
echo "══════════════════════════════════════════════════"

echo "[1/5] Installing packages (this can take a while)…"
sudo apt update

# Pick the Hailo stack matching the detected chip generation (vendor 1e60):
# the AI HAT+ 2 carries a Hailo-10H and needs hailo-h10-all — with the
# plain hailo-all package its firmware is missing and /dev/hailo0 never
# appears (the app then runs in CPU demo mode).
if lspci -d 1e60: 2>/dev/null | grep -qi "hailo-10"; then
    HAILO_PKG=hailo-h10-all     # AI HAT+ 2 (Hailo-10H)
elif lspci -d 1e60: 2>/dev/null | grep -qi "hailo"; then
    HAILO_PKG=hailo-all         # AI Kit / AI HAT+ (Hailo-8 / 8L)
else
    HAILO_PKG=hailo-all
    echo "    (No Hailo device on the PCIe bus yet — defaulting to $HAILO_PKG."
    echo "     If your HAT is an AI HAT+ 2, re-run this script once it shows"
    echo "     up in lspci, or install hailo-h10-all manually.)"
fi
echo "    Hailo package: $HAILO_PKG"

sudo apt install -y \
    "$HAILO_PKG" \
    python3-picamera2 \
    python3-opencv \
    opencv-data \
    python3-flask \
    python3-numpy \
    python3-qrcode \
    python3-pil \
    rsync

echo "[2/5] Copying app to ${APP_DIR}…"
sudo mkdir -p "$APP_DIR"
sudo rsync -a --delete --exclude '.git' "$REPO_DIR"/ "$APP_DIR"/

echo "[3/5] Installing systemd service (autostart on boot, port 80)…"
sudo cp "$REPO_DIR/setup/ki-werkstatt.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ki-werkstatt

echo "[4/5] Checking for the Hailo accelerator…"
if hailortcli fw-control identify >/dev/null 2>&1; then
    hailortcli fw-control identify | sed 's/^/    /'
    echo "    ✓ AI HAT detected."
else
    echo "    ✗ No Hailo device answered (yet)."
    echo "      A REBOOT is usually required after the first install"
    echo "      so firmware and PCIe driver load. The app still runs"
    echo "      without it, in CPU demo mode."
fi

echo "[5/5] Checking for available models…"
ls /usr/share/hailo-models/*.hef 2>/dev/null | sed 's/^/    /' || \
    echo "    (none found — they come with the hailo-all package)"

echo
echo "Done! Next steps:"
echo "  1. Reboot once:                sudo reboot"
echo "  2. The exhibit auto-starts on http://<pi>:80"
echo "  3. For the student hotspot:    bash setup/hotspot.sh"
echo "  4. For the printable poster:   python3 setup/make_poster.py"
