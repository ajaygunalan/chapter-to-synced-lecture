"""Kokoro engine: scripts/kokoro_worker.py in its own virtualenv. Setup, device, voices:
references/kokoro.md."""

import os
from pathlib import Path

from engines import Worker

FINAL = False
_ENGLISH = {                                   # hexgrad/Kokoro-82M: a = American, b = British; f/m = female/male
    "af": "alloy aoede bella heart jessica kore nicole nova river sarah sky",
    "am": "adam echo eric fenrir liam michael onyx puck santa",
    "bf": "alice emma isabella lily",
    "bm": "daniel fable george lewis",
}
VOICES = {n: f"{p}_{n}" for p, names in _ENGLISH.items() for n in names.split()}
DEFAULT = "sky"
WORKER = Worker("kokoro", os.environ.get("KOKORO_PYTHON", Path.home() / ".local/share/kokoro-venv/bin/python"),
                Path(__file__).resolve().parents[1] / "kokoro_worker.py", "references/kokoro.md")


def add_args(ap):
    g = ap.add_argument_group("kokoro")
    g.add_argument("--speed", type=float, default=1.0)
    g.add_argument("--device", choices=["cuda", "cpu"], help="default: cuda when available, else cpu")


def check(args):
    WORKER.check(args)


def synth(paragraphs, args, tmp):
    return WORKER.synth({"voice": args.voice, "speed": args.speed}, paragraphs, args, tmp, "Kokoro-82M")
