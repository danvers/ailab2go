#!/usr/bin/env bash
# One-stop helper for the authoring tools (poster, station cards, card deck).
#
#   bash setup/tools.sh                 # set up .venv-tools, then build everything
#   bash setup/tools.sh poster          # only the two posters
#   bash setup/tools.sh cards           # only the A5 card deck
#   bash setup/tools.sh stations        # station images (add --editable for layers)
#
# Why a venv: Homebrew/Debian Python refuse `pip install` into the system
# (PEP 668), so the tools get their own throwaway environment here.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv-tools"
PY="$VENV/bin/python3"

if [[ ! -x "$PY" ]]; then
    echo "→ creating $VENV"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
fi
echo "→ checking dependencies"
"$VENV/bin/pip" install --quiet -r "$ROOT/dev/requirements-tools.txt"

target="${1:-all}"; shift || true
run() { echo; echo "── $1"; "$PY" "$ROOT/setup/$1" "$@"; }

case "$target" in
    poster)   run make_poster.py ;;
    cards)    run make_cards.py ;;
    stations) run make_station_cards.py "$@" ;;
    all)      run make_poster.py
              run make_cards.py
              run make_station_cards.py ;;
    *) echo "unknown target: $target (poster|cards|stations|all)"; exit 1 ;;
esac
echo
echo "✓ done — output in setup/ and assets/stations/"
