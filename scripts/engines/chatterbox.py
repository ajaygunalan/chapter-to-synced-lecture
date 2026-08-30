"""Chatterbox engine (Resemble AI's open 500M model): scripts/chatterbox_worker.py in its
own virtualenv. The model returns no word timing, so the worker runs a forced aligner
(scripts/aligners/) over every chunk. Setup, knobs, voices, limits: references/chatterbox.md."""

import os
from pathlib import Path

from engines import Fail, Worker

FINAL = False
WORKER = Worker("chatterbox", os.environ.get("CHATTERBOX_PYTHON", Path.home() / ".local/share/chatterbox-venv/bin/python"),
                Path(__file__).resolve().parents[1] / "chatterbox_worker.py", "references/chatterbox.md")
VOICE_DIR = Path(os.environ.get("CHATTERBOX_VOICES", Path.home() / ".config/chatterbox-voices"))
# a voice is a reference clip, NAME.wav in VOICE_DIR (6-15 s of one speaker; no transcript needed);
# "default" is the voice that ships with the model
VOICES = {"default": "default"}
VOICES.update({p.stem: str(p) for p in sorted(VOICE_DIR.glob("*.wav"))})
DEFAULT = "default"


def add_args(ap):
    g = ap.add_argument_group("chatterbox")
    g.add_argument("--exaggeration", type=float, default=0.5, help="emotion, 0.25-2; 0.5 is neutral (default)")
    g.add_argument("--cfg", type=float, default=0.5, help="pacing / adherence to the reference, 0-1; lower is faster")
    g.add_argument("--temperature", type=float, default=0.8)
    g.add_argument("--seed", type=int, default=0, help="reproducibility")
    g.add_argument("--device", choices=["cuda", "cpu"], help="default: cuda when available, else cpu")


def check(args):
    info = WORKER.check(args)
    print(f"voices: {', '.join(sorted(VOICES))} (default {DEFAULT}); add NAME.wav to {VOICE_DIR}; "
          f"aligner {info['aligner']}")
    print(f"knobs: --exaggeration {args.exaggeration} --cfg {args.cfg} --temperature {args.temperature} --seed {args.seed}")


def synth(paragraphs, args, tmp):
    if args.voice != DEFAULT and not Path(args.voice).exists():
        raise Fail(f"chatterbox: no voice '{args.voice}' — a name from {sorted(VOICES)} or a path to a .wav clip", stop=True)
    knobs = {"exaggeration": args.exaggeration, "cfg": args.cfg, "temperature": args.temperature, "seed": args.seed}
    return WORKER.synth({"voice": args.voice, "knobs": knobs}, paragraphs, args, tmp, "Chatterbox-500M")
