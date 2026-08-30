"""
Forced aligners. An engine that returns a waveform but no word timing
(Chatterbox; any future voice) calls one of these to find where each word
starts; an engine that does return timing can be checked against one
(scripts/verify_timing.py). One module per aligner, all with the same
contract:

    align(wav_path, text, device=None)
        -> [[char offset, start seconds]] per word of `text` (subtitles.words_with_offsets
           order), in order, monotonic; a word the aligner cannot place — pure
           punctuation, a dash — inherits the previous word's time
    align_samples(samples, rate, text, device=None)
        the same for audio already in memory (float32 numpy, mono)

An aligner needs torch, so it runs inside an engine's virtualenv (the worker
half of an engine) or under ALIGNER_PYTHON — never in build_audio.py's own
interpreter. Adding one is a new module here plus its name in ALIGNERS.
"""

from importlib import import_module

ALIGNERS = ("mms",)
DEFAULT = "mms"


def load(name=DEFAULT):
    return import_module(f"aligners.{name}")
