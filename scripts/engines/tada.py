"""TADA engine (Hume's open-weights TADA-1B): drives one scripts/tada_worker.py process
in its own virtualenv for the whole run, one JSON job per line. Setup, voices,
limits: references/tada.md."""

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
PYTHON = Path(os.environ.get("TADA_PYTHON", Path.home() / ".local/share/tada-venv/bin/python"))
WORKER = Path(__file__).resolve().parents[1] / "tada_worker.py"
VOICE_DIR = Path(os.environ.get("TADA_VOICES", Path.home() / ".config/tada-voices"))
# a voice is a reference recording plus its transcript: NAME.wav and NAME.txt in VOICE_DIR;
# "lj" is the LJSpeech sample shipped inside the tada package
VOICES = {"lj": "lj"}
VOICES.update({p.stem: str(p) for p in sorted(VOICE_DIR.glob("*.wav")) if p.with_suffix(".txt").exists()})
DEFAULT = "lj"
_worker = None


def add_args(ap):
    g = ap.add_argument_group("tada")
    g.add_argument("--speed", type=float, default=1.0, help="speed-up factor; 1.0 leaves the model's pacing alone")
    g.add_argument("--device", choices=["cuda", "cpu"], help="default: cuda when available, else cpu")


def _voice(args):
    """-> (wav path, transcript) for --voice: a name from VOICES, or a path to a .wav with a .txt beside it."""
    v = args.voice or DEFAULT
    if v == "lj":
        out = subprocess.run([str(PYTHON), "-c", "import tada, pathlib; print(pathlib.Path(tada.__file__).parent / 'samples' / 'ljspeech.wav')"],
                             capture_output=True, text=True)
        return out.stdout.strip(), None
    p = Path(v)
    if not p.exists():
        raise Fail(f"tada: no voice '{v}' — a name from {sorted(VOICES)} or a path to NAME.wav with NAME.txt beside it", stop=True)
    txt = p.with_suffix(".txt")
    if not txt.exists():
        raise Fail(f"tada: {txt} is missing — the reference recording needs its transcript", stop=True)
    return str(p), txt.read_text().strip()


def _run(job, args):
    global _worker
    if _worker is None:
        if not PYTHON.exists():
            raise Fail(f"TADA is not installed: {PYTHON} not found (references/tada.md)", stop=True)
        _worker = subprocess.Popen([str(PYTHON), str(WORKER)] + ([args.device] if args.device else []),
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        atexit.register(lambda: _worker.stdin.close() or _worker.wait())
    _worker.stdin.write(json.dumps(job) + "\n")
    _worker.stdin.flush()
    line = _worker.stdout.readline()
    if not line:
        _worker.wait()
        _worker = None
        raise Fail("tada worker died (its stderr is above)", stop=True)
    return json.loads(line)


def check(args):
    info = _run({"check": True}, args)
    print(f"tada: torch {info['torch']}, device {info['device']}"
          + (f" ({info['gpu']})" if info.get("gpu") else "")
          + f"; cuda available: {info['cuda']}")
    print(f"voices: {', '.join(sorted(VOICES))} (default {DEFAULT}); add NAME.wav + NAME.txt to {VOICE_DIR}")


def synth(paragraphs, args, tmp):
    wav, mp3 = tmp / "part.wav", tmp / "part.mp3"
    voice, voice_text = _voice(args)
    t = time.time()
    info = _run({"voice": voice, "voice_text": voice_text, "speed": args.speed,
                 "paragraphs": paragraphs, "wav": str(wav)}, args)
    align = []
    for para, starts, off0 in zip(paragraphs, info["starts"], para_offsets(paragraphs)):
        align += align_from_char_starts(para, starts, 0.0, off0)
    ffmpeg("-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3))
    print(f"    tada on {info['device']}: {sum(map(len, paragraphs)):,} chars -> {info['duration']:.1f}s "
          f"in {time.time() - t:.0f}s")
    return mp3, align, info["duration"], 0, "TADA-1B"
