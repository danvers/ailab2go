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
BAND="a"                   # "a"  = 5 GHz  (faster — better with >10
                           #        viewers; devices without 5 GHz won't
                           #        see the SSID at all)
                           # "bg" = 2.4 GHz (max compatibility & range)
CHANNEL="36"               # 5 GHz needs an explicit channel for AP mode;
                           # 36 is indoor-legal everywhere (DE incl.).
                           # Ignored for band "bg" (auto-pick works there).
CON_NAME="ki-werkstatt-hotspot"
IP="10.10.10.1"            # short and easy to dictate; on the poster + QR
# Changing it? Mirror it in app/config.py (PUBLIC_URL) and
# setup/make_poster.py, then reprint the poster.
# ────────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "off" ]]; then
    # autoconnect off first, so "off" survives reboots
    sudo nmcli connection modify "$CON_NAME" connection.autoconnect no 2>/dev/null || true
    sudo nmcli connection down "$CON_NAME" 2>/dev/null || true
    echo "Hotspot off — stays off after reboot. Normal Wi-Fi will reconnect."
    echo "Re-enable any time with: bash setup/hotspot.sh"
    exit 0
fi

# Captive portal, part 1: the hotspot's DNS (NetworkManager runs dnsmasq
# for shared connections) answers EVERY hostname with the Pi. Phones probe
# a known URL right after joining; our webserver bounces that probe to the
# exhibit, so the "sign in to network" sheet opens the start page on its
# own. (A single friendly name — ki.lokal — was tried and dropped: browsers
# with their own DNS-over-HTTPS never ask us. The OS connectivity check
# does, which is why the wildcard works where the name failed.)
sudo mkdir -p /etc/NetworkManager/dnsmasq-shared.d
echo "address=/#/$IP" | sudo tee /etc/NetworkManager/dnsmasq-shared.d/ki-werkstatt.conf >/dev/null

# Wired ethernet keeps working alongside — handy for maintenance.
sudo nmcli connection delete "$CON_NAME" >/dev/null 2>&1 || true
# autoconnect + high priority: after a power cycle the hotspot always wins
# over any saved home-Wi-Fi profile — the exhibit comes up unattended.
sudo nmcli connection add type wifi ifname wlan0 mode ap \
    con-name "$CON_NAME" ssid "$SSID" autoconnect yes \
    connection.autoconnect-priority 100 \
    802-11-wireless.band "$BAND" \
    $( [[ "$BAND" == "a" ]] && echo 802-11-wireless.channel "$CHANNEL" ) \
    802-11-wireless.ap-isolation 1 \
    wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PASSWORD" \
    ipv4.method shared ipv4.addresses "$IP/24" ipv6.method disabled
# ap-isolation 1: guests only ever talk to the Pi, never to each other —
# in a class full of phones nobody can poke at a classmate's device.
# Guests must never be ROUTED anywhere either: "shared" mode NATs the
# hotspot onto any uplink, so a maintenance ethernet cable into a school
# network would silently connect every student phone to that network.
# The dispatcher drops all forwarding from wlan0, on every activation,
# reboots included. Captive portal and exhibit need no forwarding at all.
sudo tee /etc/NetworkManager/dispatcher.d/99-ki-werkstatt-no-forward >/dev/null << 'DISPATCH'
#!/bin/bash
# Own nftables table at priority -10: its drop verdict is final before
# NetworkManager's shared-mode rules ever run. (Bookworm has no iptables.)
[ "$CONNECTION_ID" = "ki-werkstatt-hotspot" ] || exit 0
case "$2" in
  up)
    nft delete table ip ki_werkstatt 2>/dev/null || true
    nft add table ip ki_werkstatt
    nft add chain ip ki_werkstatt forward \
        '{ type filter hook forward priority -10 ; policy accept ; }'
    nft add rule ip ki_werkstatt forward iifname "wlan0" drop
    ;;
  down)
    nft delete table ip ki_werkstatt 2>/dev/null || true
    ;;
esac
DISPATCH
sudo chmod 755 /etc/NetworkManager/dispatcher.d/99-ki-werkstatt-no-forward

sudo nmcli connection up "$CON_NAME"

echo
echo "══════════════════════════════════════════════════"
echo "  Hotspot active!"
echo "  WLAN:     $SSID"
echo "  Passwort: $PASSWORD"
echo "  Adresse:  http://$IP"
echo "══════════════════════════════════════════════════"
echo "Note: while the hotspot is on, the Pi has no internet via Wi-Fi."
echo "That is a feature — the exhibit is fully offline. Use ethernet"
echo "if you need to update something."
