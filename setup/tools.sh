#!/usr/bin/env bash
# One-stop helper for the authoring tools (poster, station cards, card deck).
#
#   bash setup/tools.sh                 # set up .venv-tools, then build everything
#   bash setup/tools.sh poster          # only the two posters
#   bash setup/tools.sh cards           # only the A5 card deck
#   bash setup/tools.sh stations        # station images (add --editable for layers)
#   bash setup/tools.sh case            # 3D-print files for the camera housing
#
# "case" pulls in a CAD stack (trimesh, scipy) that the paper tools do not
# need, so it installs on first use only — and it is not part of "all".
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
    case)     echo "→ checking CAD dependencies"
              "$VENV/bin/pip" install --quiet -r "$ROOT/dev/requirements-cad.txt"
              echo; echo "── case_elp48mp.py"
              "$PY" "$ROOT/hardware/case_elp48mp.py" "$@"
              echo; echo "✓ done — STLs in hardware/stl/"; exit 0 ;;
    all)      run make_poster.py
              run make_cards.py
              run make_station_cards.py ;;
    *) echo "unknown target: $target (poster|cards|stations|case|all)"; exit 1 ;;
esac
echo
echo "✓ done — output in setup/ and assets/stations/"
