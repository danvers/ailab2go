#!/usr/bin/env python3
"""Render the print-ready card deck from the PowerPoint masters.

    bash setup/tools.sh cards

The DESIGN LIVES IN THE PPTX — material/source/cards/cards_de.pptx and
cards_en.pptx are hand-made in PowerPoint and are the single source of
truth for the printed cards. This script only converts, never re-designs,
so whatever you change in PowerPoint is exactly what gets printed.

    material/source/cards/cards_<lang>.pptx   →   material/cards/cards_<lang>.pdf

Converters, tried in this order:

  1. PowerPoint   (AppleScript, macOS)  — pixel-identical to what you see
     in the app, because it IS the app. Needs one-time permission (see
     PERMISSIONS below); without it PowerPoint answers -9074 and we move on.
  2. LibreOffice  (soffice --headless)  — works everywhere, no GUI. Fonts
     must be installed locally, otherwise it substitutes them and the
     layout shifts, so it is the fallback rather than the default.
  3. Neither      → print the exact manual steps instead of failing
     silently. The committed PDFs stay valid until then.

Every conversion is verified: the PDF must have exactly as many pages as
the deck has slides, otherwise it is rejected.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "material" / "source" / "cards"
OUT = ROOT / "material" / "cards"

LIBREOFFICE_CANDIDATES = (
    "soffice", "libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)


def find_libreoffice():
    for c in LIBREOFFICE_CANDIDATES:
        path = shutil.which(c) or (c if Path(c).exists() else None)
        if path:
            return path
    return None


def convert_libreoffice(soffice, pptx, pdf):
    """Headless conversion. LibreOffice always names the output after the
    input, so we convert into the target folder and rename if needed."""
    subprocess.run([soffice, "--headless", "--norestore",
                    "--convert-to", "pdf", "--outdir", str(pdf.parent),
                    str(pptx)],
                   check=True, capture_output=True, timeout=600)
    produced = pdf.parent / (pptx.stem + ".pdf")
    if produced != pdf and produced.exists():
        produced.replace(pdf)
    return pdf.exists()


def convert_powerpoint(pptx, pdf):
    """macOS + Microsoft PowerPoint via AppleScript — highest fidelity.
    Returns False (rather than raising) when the sandbox denies access, so
    the caller can fall through to the manual instructions."""
    if sys.platform != "darwin":
        return False
    if not Path("/Applications/Microsoft PowerPoint.app").exists():
        return False
    script = f'''
    set target to POSIX file "{pdf}" as text
    tell application "Microsoft PowerPoint"
        with timeout of 900 seconds
            open POSIX file "{pptx}"
            save active presentation in target as save as PDF
            close active presentation saving no
        end timeout
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script],
                       check=True, capture_output=True, timeout=960)
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode(errors="replace")
        if "-9074" in err or "-1743" in err:
            return False        # sandbox / automation permission missing
        raise
    return pdf.exists()


def slide_count(pptx):
    import re
    import zipfile
    with zipfile.ZipFile(pptx) as z:
        return len([n for n in z.namelist()
                    if re.match(r"ppt/slides/slide\d+\.xml$", n)])


def page_count(pdf):
    """Page count straight from the PDF, without extra dependencies."""
    import re
    data = pdf.read_bytes()
    counts = [int(m.group(1)) for m in
              re.finditer(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", data, re.S)]
    return max(counts) if counts else None


MANUAL = """
  Neither LibreOffice nor a scriptable PowerPoint is available, so the PDFs
  were NOT rebuilt. The committed ones in material/cards/ are still fine —
  they just don't include your latest PowerPoint edits.

  Pick whichever suits you:

  a) Export by hand (2 minutes, no install):
       open material/source/cards/cards_de.pptx
       File → Export… → File Format: PDF
       save as material/cards/cards_de.pdf   (same for _en)

  b) Automate it with LibreOffice:
       brew install --cask libreoffice      # macOS
       sudo apt install libreoffice-impress # Raspberry Pi / Debian
     then run this command again.

  c) Automate it with PowerPoint (macOS, pixel-identical) — recommended:
       System Settings → Privacy & Security → Automation →
         Terminal (or your terminal app) → enable "Microsoft PowerPoint"
       System Settings → Privacy & Security → Full Disk Access →
         add the same terminal app
     then run this command again. PowerPoint will flash open briefly.
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    decks = sorted(SRC.glob("cards_*.pptx"))
    if not decks:
        sys.exit(f"No PowerPoint masters found in {SRC.relative_to(ROOT)}")

    soffice = find_libreoffice()
    done, failed = [], []
    for pptx in decks:
        pdf = OUT / (pptx.stem + ".pdf")
        # Convert to a side file first and only swap it in once verified —
        # a half-finished or wrong conversion must never destroy the
        # committed, print-ready PDF.
        staged = OUT / (pptx.stem + ".new.pdf")
        staged.unlink(missing_ok=True)
        slides = slide_count(pptx)
        ok = convert_powerpoint(pptx, staged)
        how = "PowerPoint"
        if not ok and soffice:
            ok = convert_libreoffice(soffice, pptx, staged)
            how = "LibreOffice"
        if ok:
            pages = page_count(staged)
            if pages and pages != slides:
                print(f"  ✗ {pptx.name}: converted to {pages} pages from "
                      f"{slides} slides — looks wrong, keeping the old PDF")
                staged.unlink(missing_ok=True)
                ok = False
        if ok:
            size = staged.stat().st_size / 1e6
            staged.replace(pdf)
            print(f"  ✓ {pdf.relative_to(ROOT)} — {slides} pages, "
                  f"{size:.1f} MB, via {how}, design untouched")
        (done if ok else failed).append(pdf)

    if failed:
        print(MANUAL)
        sys.exit(1)


if __name__ == "__main__":
    main()
