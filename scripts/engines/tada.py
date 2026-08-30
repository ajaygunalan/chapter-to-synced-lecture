"""TADA engine (Hume's open-weights TADA-1B): scripts/tada_worker.py in its own virtualenv.
Setup, voices, limits: references/tada.md."""

import os
import subprocess
from pathlib import Path

from engines import Fail, Worker

FINAL = False
WORKER = Worker("tada", os.environ.get("TADA_PYTHON", Path.home() / ".local/share/tada-venv/bin/python"),
                Path(__file__).resolve().parents[1] / "tada_worker.py", "references/tada.md")
VOICE_DIR = Path(os.environ.get("TADA_VOICES", Path.home() / ".config/tada-voices"))
# a voice is a reference recording plus its transcript: NAME.wav and NAME.txt in VOICE_DIR;
# "lj" is the LJSpeech sample shipped inside the tada package
VOICES = {"lj": "lj"}
VOICES.update({p.stem: str(p) for p in sorted(VOICE_DIR.glob("*.wav")) if p.with_suffix(".txt").exists()})
DEFAULT = "lj"


def add_args(ap):
    g = ap.add_argument_group("tada")
    g.add_argument("--speed", type=float, default=1.0, help="speed-up factor; 1.0 leaves the model's pacing alone")
    g.add_argument("--device", choices=["cuda", "cpu"], help="default: cuda when available, else cpu")


def _voice(args):
    """-> (wav path, transcript) for --voice: a name from VOICES, or a path to a .wav with a .txt beside it."""
    if args.voice == "lj":
        out = subprocess.run([str(WORKER.python), "-c", "import tada, pathlib; print(pathlib.Path(tada.__file__).parent / 'samples' / 'ljspeech.wav')"],
                             capture_output=True, text=True)
        return out.stdout.strip(), None
    p = Path(args.voice)
    if not p.exists():
        raise Fail(f"tada: no voice '{args.voice}' — a name from {sorted(VOICES)} or a path to NAME.wav with NAME.txt beside it", stop=True)
    txt = p.with_suffix(".txt")
    if not txt.exists():
        raise Fail(f"tada: {txt} is missing — the reference recording needs its transcript", stop=True)
    return str(p), txt.read_text().strip()


def check(args):
    WORKER.check(args)
    print(f"voices: {', '.join(sorted(VOICES))} (default {DEFAULT}); add NAME.wav + NAME.txt to {VOICE_DIR}")


def synth(paragraphs, args, tmp):
    voice, voice_text = _voice(args)
    return WORKER.synth({"voice": voice, "voice_text": voice_text, "speed": args.speed}, paragraphs, args, tmp, "TADA-1B")
