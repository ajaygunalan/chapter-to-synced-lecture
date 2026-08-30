#!/usr/bin/env python3
"""
A lint for a recording: does the audio say the words when the cues say it does?

    verify_timing.py <outdir> <part> [--tolerance 0.5] [--device cuda|cpu]

Decodes audio/<part>.mp3, runs the forced aligner (scripts/aligners/, default
"mms") over it with audio/<part>.txt — the exact words the engine was given —
and compares the start it finds for every word with cues/<part>.align.json,
the start the engine reported. Prints every word whose two times differ by
more than the tolerance (a word with no letters — a dash — is not compared),
and a summary: words, median |Δ|, 95th percentile,
the count over tolerance and the longest run of them. One word off is the
aligner's noise; a run of them is a word the voice skipped, repeated or
mangled, from that point on. Exit status 1 when any word is over.

Works on any engine's recording — for Chatterbox it re-derives its own
timing (so a clean result is a check of the aligner, not of the voice); for
TADA and ElevenLabs it is an independent second opinion. Needs torch, so it
runs itself under the Chatterbox virtualenv (ALIGNER_PYTHON overrides).
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON = Path(os.environ.get("ALIGNER_PYTHON", Path.home() / ".local/share/chatterbox-venv/bin/python"))


def in_aligner_venv():
    try:
        import torchaudio  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    if not in_aligner_venv():
        if not PYTHON.exists():
            sys.exit(f"no virtualenv with torchaudio: {PYTHON} not found (references/chatterbox.md; ALIGNER_PYTHON)")
        os.execv(str(PYTHON), [str(PYTHON), __file__] + sys.argv[1:])

    import aligners
    from lecture_format import SEP, align_path, audio_path, ffmpeg, text_path
    from subtitles import words_with_offsets

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", type=Path)
    ap.add_argument("part")
    ap.add_argument("--tolerance", type=float, default=0.5, help="seconds; a word further off than this is reported")
    ap.add_argument("--device", choices=["cuda", "cpu"])
    args = ap.parse_args()

    mp3, txt, alf = audio_path(args.out, args.part), text_path(args.out, args.part), align_path(args.out, args.part)
    for p in (mp3, txt, alf):
        if not p.exists():
            sys.exit(f"{p} is missing — the part is not recorded")
    text = txt.read_text()
    cued = json.loads(alf.read_text())["words"]
    words = words_with_offsets(text)
    if len(cued) != len(words):
        sys.exit(f"{alf} has {len(cued)} words, {txt} has {len(words)} — not the same recording")

    with tempfile.TemporaryDirectory(prefix="verify-") as tmp:
        wav = Path(tmp) / "part.wav"
        ffmpeg("-i", str(mp3), "-ac", "1", "-ar", str(aligners.load().RATE), str(wav))
        found = aligners.load().align(wav, text, args.device)

    paras = text.split(SEP)
    deltas, over, run, best_run = [], [], 0, 0
    for (off, word), (_, t_cue), (_, t_found) in zip(words, cued, found):
        if not any(c.isalnum() for c in word):             # a dash, a bracket: nothing was said, nothing to compare
            continue
        d = t_found - t_cue
        deltas.append(abs(d))
        if abs(d) > args.tolerance:
            over.append((t_cue, d, word, off))
            run += 1
            best_run = max(best_run, run)
        else:
            run = 0
    for t_cue, d, word, off in over:
        para = text.count(SEP, 0, off) + 1
        print(f"  {t_cue:8.2f}s  {d:+.2f}s  {word!r:24}  paragraph {para}/{len(paras)}")
    ds = sorted(deltas)
    print(f"{args.part}: {len(deltas)} words compared, median |Δ| {statistics.median(ds):.3f}s, "
          f"p95 {ds[int(0.95 * (len(ds) - 1))]:.3f}s, over {args.tolerance:g}s: {len(over)}"
          + (f" (longest run {best_run})" if over else ""))
    sys.exit(1 if over else 0)


if __name__ == "__main__":
    main()
