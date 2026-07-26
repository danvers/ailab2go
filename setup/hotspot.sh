#!/usr/bin/env bash
# Turn the Pi into a Wi-Fi hotspot so students can join with their own
# devices — no venue network needed, and the whole exhibit stays offline.
#
#   bash setup/hotspot.sh          # create + activate the hotspot
#   bash setup/hotspot.sh off      # deactivate (back to normal Wi-Fi)
set -euo pipefail

# ── tweak these for your event ──────────────────────────────────────────
SSID="KI-Werkstatt"
PASSWORD="lernen-mit-ki"   # min. 8 characters, goes on the poster
BAND="bg"                  # "bg" = 2.4 GHz (max compatibility & range)
                           # "a"  = 5 GHz  (faster — better with >10 viewers,
                           #                if all devices support it)
CON_NAME="ki-werkstatt-hotspot"
# ────────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "off" ]]; then
    # autoconnect off first, so "off" survives reboots
    sudo nmcli connection modify "$CON_NAME" connection.autoconnect no 2>/dev/null || true
    sudo nmcli connection down "$CON_NAME" 2>/dev/null || true
    echo "Hotspot off — stays off after reboot. Normal Wi-Fi will reconnect."
    echo "Re-enable any time with: bash setup/hotspot.sh"
    exit 0
fi

# Wired ethernet keeps working alongside — handy for maintenance.
sudo nmcli connection delete "$CON_NAME" >/dev/null 2>&1 || true
# autoconnect + high priority: after a power cycle the hotspot always wins
# over any saved home-Wi-Fi profile — the exhibit comes up unattended.
sudo nmcli connection add type wifi ifname wlan0 mode ap \
    con-name "$CON_NAME" ssid "$SSID" autoconnect yes \
    connection.autoconnect-priority 100 \
    802-11-wireless.band "$BAND" \
    wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PASSWORD" \
    ipv4.method shared ipv6.method disabled
sudo nmcli connection up "$CON_NAME"

echo
echo "══════════════════════════════════════════════════"
echo "  Hotspot active!"
echo "  WLAN:     $SSID"
echo "  Passwort: $PASSWORD"
echo "  Adresse:  http://10.42.0.1"
echo "══════════════════════════════════════════════════"
echo "Note: while the hotspot is on, the Pi has no internet via Wi-Fi."
echo "That is a feature — the exhibit is fully offline. Use ethernet"
echo "if you need to update something."
