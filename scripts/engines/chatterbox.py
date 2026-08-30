"""Chatterbox engine (Resemble AI's open 500M model): drives one scripts/chatterbox_worker.py
process in its own virtualenv for the whole run, one JSON job per line. The model returns
no word timing, so the worker runs a forced aligner (scripts/aligners/) over every chunk it
makes. Setup, knobs, voices, limits: references/chatterbox.md."""

import atexit
import json
import os
import subprocess
import time
from pathlib import Path

from engines import Fail
from lecture_format import ffmpeg, para_offsets
from subtitles import align_from_char_starts

FINAL = False
PYTHON = Path(os.environ.get("CHATTERBOX_PYTHON", Path.home() / ".local/share/chatterbox-venv/bin/python"))
WORKER = Path(__file__).resolve().parents[1] / "chatterbox_worker.py"
VOICE_DIR = Path(os.environ.get("CHATTERBOX_VOICES", Path.home() / ".config/chatterbox-voices"))
# a voice is a reference clip, NAME.wav in VOICE_DIR (6-15 s of one speaker; no transcript needed);
# "default" is the voice that ships with the model
VOICES = {"default": "default"}
VOICES.update({p.stem: str(p) for p in sorted(VOICE_DIR.glob("*.wav"))})
DEFAULT = "default"
_worker = None


def add_args(ap):
    g = ap.add_argument_group("chatterbox")
    g.add_argument("--exaggeration", type=float, default=0.5, help="emotion, 0.25-2; 0.5 is neutral (default)")
    g.add_argument("--cfg", type=float, default=0.5, help="pacing / adherence to the reference, 0-1; lower is faster")
    g.add_argument("--temperature", type=float, default=0.8)
    g.add_argument("--seed", type=int, default=0, help="re-applied before every chunk, so a run is reproducible")
    g.add_argument("--device", choices=["cuda", "cpu"], help="default: cuda when available, else cpu")


def _voice(args):
    """-> path of the reference clip for --voice, or None for the model's own voice."""
    v = args.voice or DEFAULT
    if v == "default":
        return None
    p = Path(v)
    if not p.exists():
        raise Fail(f"chatterbox: no voice '{v}' — a name from {sorted(VOICES)} or a path to a .wav clip", stop=True)
    return str(p)


def _run(job, args):
    global _worker
    if _worker is None:
        if not PYTHON.exists():
            raise Fail(f"Chatterbox is not installed: {PYTHON} not found (references/chatterbox.md)", stop=True)
        _worker = subprocess.Popen([str(PYTHON), str(WORKER)] + ([args.device] if args.device else []),
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        atexit.register(lambda: _worker.stdin.close() or _worker.wait())
    _worker.stdin.write(json.dumps(job) + "\n")
    _worker.stdin.flush()
    line = _worker.stdout.readline()
    if not line:
        _worker.wait()
        _worker = None
        raise Fail("chatterbox worker died (its stderr is above)", stop=True)
    return json.loads(line)


def check(args):
    info = _run({"check": True}, args)
    print(f"chatterbox: torch {info['torch']}, device {info['device']}"
          + (f" ({info['gpu']})" if info.get("gpu") else "")
          + f"; cuda available: {info['cuda']}; aligner {info['aligner']}")
    print(f"voices: {', '.join(sorted(VOICES))} (default {DEFAULT}); add NAME.wav to {VOICE_DIR}")
    print(f"knobs: --exaggeration {args.exaggeration} --cfg {args.cfg} --temperature {args.temperature} --seed {args.seed}")


def synth(paragraphs, args, tmp):
    wav, mp3 = tmp / "part.wav", tmp / "part.mp3"
    t = time.time()
    info = _run({"voice": _voice(args), "exaggeration": args.exaggeration, "cfg": args.cfg,
                 "temperature": args.temperature, "seed": args.seed,
                 "paragraphs": paragraphs, "wav": str(wav)}, args)
    align = []
    for para, starts, off0 in zip(paragraphs, info["starts"], para_offsets(paragraphs)):
        align += align_from_char_starts(para, starts, 0.0, off0)
    ffmpeg("-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3))
    print(f"    chatterbox on {info['device']}: {sum(map(len, paragraphs)):,} chars -> {info['duration']:.1f}s "
          f"in {time.time() - t:.0f}s")
    return mp3, align, info["duration"], 0, "Chatterbox-500M"
