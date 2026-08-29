#!/usr/bin/env python3
"""
The last step of a run: open.py lecture.html

Stamps "open" into <outdir>/run.log (every script of the run stamped its
own finish there; extract.py stamped "started"), prints how long the run
took — in total and per stretch — and opens the page in the browser.
"""

import subprocess
import sys
from pathlib import Path

from lecture_format import run_summary, stamp


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    html = Path(sys.argv[1]).resolve()
    stamp(html.parent, "open")
    print("\n" + run_summary(html.parent) + "\n")
    subprocess.Popen(["xdg-open", str(html)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
