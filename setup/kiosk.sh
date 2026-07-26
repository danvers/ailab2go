#!/usr/bin/env bash
# Turn the Pi itself into the projector player: on every boot, Chromium
# starts full-screen on the wall display (/beamer) — plug the beamer or TV
# into the Pi's HDMI port and you have a self-contained exhibition wall.
#
#   bash setup/kiosk.sh          # enable autostart kiosk
#   bash setup/kiosk.sh off      # disable it again
#
# Works on Raspberry Pi OS with desktop (X11 and labwc/Wayland sessions both
# honour XDG autostart). The exhibit app itself keeps running as a systemd
# service either way — phones on the hotspot are unaffected.
set -euo pipefail

AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/kiwerkstatt-beamer.desktop"
URL="http://localhost/beamer"

if [[ "${1:-}" == "off" ]]; then
    rm -f "$DESKTOP_FILE"
    echo "Kiosk-Autostart entfernt. (Laufendes Chromium ggf. mit Alt+F4 beenden.)"
    exit 0
fi

BROWSER="$(command -v chromium-browser || command -v chromium || true)"
if [[ -z "$BROWSER" ]]; then
    echo "Chromium fehlt — installieren mit:  sudo apt install -y chromium-browser"
    exit 1
fi

mkdir -p "$AUTOSTART_DIR"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=KI-Werkstatt Beamer
Comment=Full-screen exhibition wall (/beamer)
Exec=$BROWSER --kiosk --noerrdialogs --disable-infobars --incognito \
  --autoplay-policy=no-user-gesture-required --check-for-update-interval=31536000 $URL
X-GNOME-Autostart-enabled=true
EOF

# keep the screen awake — a projector wall must not blank after 10 minutes
if command -v raspi-config >/dev/null; then
    sudo raspi-config nonint do_blanking 1 || true
fi

echo "══════════════════════════════════════════════════"
echo "  Kiosk eingerichtet: beim nächsten Boot startet"
echo "  Chromium vollbild auf $URL"
echo "  Jetzt sofort testen:"
echo "    $BROWSER --kiosk $URL &"
echo "  Wieder aus: bash setup/kiosk.sh off"
echo "══════════════════════════════════════════════════"
