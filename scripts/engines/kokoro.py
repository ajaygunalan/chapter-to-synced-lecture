"""Kokoro engine (the default): scripts/kokoro_worker.py in its own virtualenv. The model
returns the start of every word itself, so no aligner runs. Setup, device, voices,
pronunciation: references/kokoro.md."""

import json
import os
import re
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
DEFAULT = "michael"
WORKER = Worker("kokoro", os.environ.get("KOKORO_PYTHON", Path.home() / ".local/share/kokoro-venv/bin/python"),
                Path(__file__).resolve().parents[1] / "kokoro_worker.py", "references/kokoro.md")
LEXICON = Path(__file__).resolve().parents[2] / "references" / "kokoro-lexicon.json"   # word -> IPA, misaki's alphabet
_CAPS_RUN = re.compile(r"[A-Z]{2,}")


def add_args(ap):
    g = ap.add_argument_group("kokoro")
    g.add_argument("--speed", type=float, default=1.0)
    g.add_argument("--device", choices=["cuda", "cpu"], help="default: cuda when available, else cpu")
    g.add_argument("--lexicon", type=Path, action="append", default=[],
                   help=f"JSON {{word: IPA}} added to the built-in {LEXICON.name} (misaki's alphabet; repeatable)")


def lexicon(args):
    """{lower-cased word: IPA}: the built-in file, then every --lexicon in order."""
    out = {}
    for f in [LEXICON] + list(getattr(args, "lexicon", []) or []):
        if f.exists():
            out.update({k.lower(): v for k, v in json.loads(f.read_text()).items()})
    return out


def respell(say):
    """A respelling written for a BPE voice ("IGG-el-bear-ger") as misaki reads it: a run of two or
    more capitals is an acronym to misaki (I-G-G), so stressed syllables go lower case; a single capital
    letter (S-R-P, X eleven) stays a letter."""
    return _CAPS_RUN.sub(lambda m: m.group().lower(), say)


def adapt_rules(rules, args):
    """Drop the respelling of any word the lexicon pronounces (the IPA is the better fix), respell the rest."""
    known = lexicon(args)
    out = []
    for rx, say in rules:
        word = re.sub(r"\\(.)", r"\1", rx.pattern[2:-2])          # \bIglberger\b -> Iglberger
        if word.lower() in known:
            continue
        out.append((rx, respell(say)))
    return out


def check(args):
    WORKER.check(args)
    print(f"lexicon: {len(lexicon(args))} word(s) ({LEXICON}" + "".join(f", {f}" for f in args.lexicon) + ")")


def synth(paragraphs, args, tmp):
    return WORKER.synth({"voice": args.voice, "speed": args.speed, "lexicon": lexicon(args)}, paragraphs, args, tmp,
                        "Kokoro-82M")
