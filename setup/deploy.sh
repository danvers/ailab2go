#!/usr/bin/env bash
# Push the current project from your laptop to the Pi and restart the exhibit.
#
#   bash setup/deploy.sh                 # uses dan@raspi5-1.local
#   bash setup/deploy.sh dan@10.42.0.1   # e.g. while the hotspot is running
set -euo pipefail

TARGET="${1:-dan@raspi5-1.local}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "→ Syncing $REPO_DIR → $TARGET:ki-werkstatt/"
rsync -rlt --delete \
    --exclude .venv --exclude __pycache__ --exclude .DS_Store \
    --exclude .claude --exclude .git \
    "$REPO_DIR"/ "$TARGET":ki-werkstatt/

echo "→ Installing to /opt and restarting the service"
ssh "$TARGET" '
    sudo rsync -a --delete --exclude .git ~/ki-werkstatt/ /opt/ki-werkstatt/
    sudo systemctl restart ki-werkstatt
    sleep 6
    journalctl -u ki-werkstatt -b --no-pager | \
        grep -E "Frame source|AI accelerator|Pose model|Face guard" | tail -4
'
echo "✓ Done — open the exhibit and check the footer status chips."
