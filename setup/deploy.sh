#!/usr/bin/env bash
# Push the current project from your laptop to the Pi and restart the exhibit.
#
#   bash setup/deploy.sh                      # uses your saved target
#   bash setup/deploy.sh pi@10.10.10.1        # e.g. while the hotspot is running
#
# Save your own Pi once, so plain `bash setup/deploy.sh` just works:
#
#   echo 'DEPLOY_TARGET="pi@raspberrypi.local"' > setup/deploy.local
#
# setup/deploy.local is git-ignored — your username and hostname stay on your
# machine and never reach the public repository.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$HERE/.." && pwd)"

# precedence: command-line argument > setup/deploy.local > $DEPLOY_TARGET
if [[ -z "${1:-}" && -f "$HERE/deploy.local" ]]; then
    # shellcheck source=/dev/null
    source "$HERE/deploy.local"
fi
TARGET="${1:-${DEPLOY_TARGET:-}}"
if [[ -z "$TARGET" ]]; then
    echo "No target set. Either pass one:" >&2
    echo "    bash setup/deploy.sh pi@raspberrypi.local" >&2
    echo "  or save it once:" >&2
    echo "    echo 'DEPLOY_TARGET=\"pi@raspberrypi.local\"' > setup/deploy.local" >&2
    exit 2
fi

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
