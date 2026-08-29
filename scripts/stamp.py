#!/usr/bin/env python3
"""
Mark a phase of the run as finished:

    stamp.py <outdir> plan
    stamp.py <outdir> slides "8 parts, 118 frames"

The phases are read · plan · slides · script · review · record · open
(lecture_format.PHASES). extract.py, build_audio.py and open.py stamp their
own; the ones a model does — plan, slides, script, review — are stamped with
this, so open.py can print where the time went.
"""

import sys
from pathlib import Path

from lecture_format import PHASES, stamp


def main():
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    out, phase, detail = Path(sys.argv[1]), sys.argv[2], " ".join(sys.argv[3:])
    if phase not in PHASES:
        sys.exit(f"unknown phase {phase!r}; one of: {', '.join(PHASES)}")
    stamp(out, phase, detail)


if __name__ == "__main__":
    main()
