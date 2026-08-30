"""
Forced aligners. An engine that returns a waveform but no word timing
(Chatterbox; any future voice) calls one to find where each word starts; an
engine that does return timing can be checked against one
(scripts/verify_timing.py). One module per aligner, all with the same contract:

    align(samples, rate, text, device=None)
        samples: float32 numpy, mono, at rate Hz
        -> [[char offset, start seconds]] per word of `text` (subtitles.words_with_offsets
           order), monotonic; a word the aligner cannot place inherits the previous word's time
    normalise(word) -> the letters of a word the aligner listens for; '' means it will not be placed

An aligner needs torch, so it runs inside an engine's virtualenv — the worker
half of an engine, or PYTHON below for a standalone tool. Adding one is a new
module here plus its name in ALIGNERS.
"""

import os
from importlib import import_module
from pathlib import Path

from engines.chatterbox import WORKER as _chatterbox

ALIGNERS = ("mms",)
DEFAULT = "mms"
PYTHON = Path(os.environ.get("ALIGNER_PYTHON") or _chatterbox.python)   # where the aligner runs on its own


def load(name=DEFAULT):
    return import_module(f"aligners.{name}")
