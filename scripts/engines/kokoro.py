"""Kokoro engine: drives one scripts/kokoro_worker.py process (its own virtualenv)
for the whole run, one JSON job per line. Setup, device, voices: references/kokoro.md."""

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
_ENGLISH = {                                   # hexgrad/Kokoro-82M: a = American, b = British; f/m = female/male
    "af": "alloy aoede bella heart jessica kore nicole nova river sarah sky",
    "am": "adam echo eric fenrir liam michael onyx puck santa",
    "bf": "alice emma isabella lily",
    "bm": "daniel fable george lewis",
}
VOICES = {n: f"{p}_{n}" for p, names in _ENGLISH.items() for n in names.split()}
DEFAULT = "sky"
PYTHON = Path(os.environ.get("KOKORO_PYTHON", Path.home() / ".local/share/kokoro-venv/bin/python"))
WORKER = Path(__file__).resolve().parents[1] / "kokoro_worker.py"
_worker = None


def add_args(ap):
    g = ap.add_argument_group("kokoro")
    g.add_argument("--speed", type=float, default=1.0)
    g.add_argument("--device", choices=["cuda", "cpu"], help="default: cuda when available, else cpu")


def _run(job, args):
    """Send one job to the worker (started on first use); -> the JSON line it answers with."""
    global _worker
    if _worker is None:
        if not PYTHON.exists():
            raise Fail(f"Kokoro is not installed: {PYTHON} not found (references/kokoro.md)", stop=True)
        _worker = subprocess.Popen([str(PYTHON), str(WORKER)] + ([args.device] if args.device else []),
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        atexit.register(lambda: _worker.stdin.close() or _worker.wait())
    _worker.stdin.write(json.dumps(job) + "\n")
    _worker.stdin.flush()
    line = _worker.stdout.readline()
    if not line:
        _worker.wait()
        _worker = None
        raise Fail("kokoro worker died (its stderr is above)", stop=True)
    return json.loads(line)


def check(args):
    info = _run({"check": True}, args)
    print(f"kokoro: torch {info['torch']}, device {info['device']}"
          + (f" ({info['gpu']})" if info.get("gpu") else "")
          + f"; cuda available: {info['cuda']}")


def synth(paragraphs, args, tmp):
    wav, mp3 = tmp / "part.wav", tmp / "part.mp3"
    t = time.time()
    info = _run({"voice": args.voice, "speed": args.speed, "paragraphs": paragraphs, "wav": str(wav)}, args)
    align = []
    for para, starts, off0 in zip(paragraphs, info["starts"], para_offsets(paragraphs)):
        align += align_from_char_starts(para, starts, 0.0, off0)
    ffmpeg("-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3))
    print(f"    kokoro on {info['device']}: {sum(map(len, paragraphs)):,} chars -> {info['duration']:.1f}s "
          f"in {time.time() - t:.0f}s")
    return mp3, align, info["duration"], 0, "Kokoro-82M"
