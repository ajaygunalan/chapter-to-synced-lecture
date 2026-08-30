"""
Voice engines. One module per engine, all with the same contract, so
build_audio.py never names one:

    FINAL                True if a part it recorded must not be replaced by another
                         engine's run unless forced (a paid recording)
    VOICES               {short name: engine voice id}
    DEFAULT              a key of VOICES
    add_args(parser)     the engine's own options, in one argument group
    check(args)          print what the engine can do right now (device, account)
    synth(paragraphs, args, tmp)
                         -> (mp3 path, align, duration, cost, model)
                            align: [[char offset, seconds]] per word of SEP.join(paragraphs)
                            cost:  credits spent (0 for a local engine)
                            model: what cues/<part>.json records as "model"
                         raises Fail(message); Fail.stop means give up on the whole run
                         (no key, quota exhausted) rather than just this part

A local engine is a Worker: one process in the engine's own virtualenv for
the whole run, speaking scripts/worker.py's protocol. Adding an engine is
one new module here plus its name in ENGINES.
"""

import atexit
import json
import subprocess
import time
from importlib import import_module
from pathlib import Path

from lecture_format import ffmpeg, para_offsets
from subtitles import align_from_char_starts

ENGINES = ("chatterbox", "tada", "kokoro", "elevenlabs")
DEFAULT = "chatterbox"
LEGACY = "elevenlabs"        # what recorded the cues written before they carried an "engine" key


class Fail(Exception):
    def __init__(self, message, stop=False):
        super().__init__(message)
        self.stop = stop


def load(name):
    return import_module(f"engines.{name}")


def resolve_voice(args, engine):
    """--voice as a short name or a raw id; else the engine's default."""
    v = args.voice or engine.DEFAULT
    return engine.VOICES.get(v.lower(), v)


class Worker:
    """The engine side of scripts/worker.py: the process is started on first use
    (with --device, if given) and answers one JSON line per job."""

    def __init__(self, name, python, script, doc):
        self.name, self.python, self.script, self.doc = name, Path(python), Path(script), doc
        self.proc = None

    def run(self, job, args):
        if self.proc is None:
            if not self.python.exists():
                raise Fail(f"{self.name} is not installed: {self.python} not found ({self.doc})", stop=True)
            self.proc = subprocess.Popen([str(self.python), str(self.script)] + ([args.device] if args.device else []),
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            atexit.register(self.close)
        self.proc.stdin.write(json.dumps(job) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            self.proc.wait()
            self.proc = None
            raise Fail(f"{self.name} worker died (its stderr is above)", stop=True)
        return json.loads(line)

    def close(self):
        if self.proc is not None:
            self.proc.stdin.close()
            self.proc.wait()

    def check(self, args):
        """Print the torch build and device the worker will use -> its check answer."""
        info = self.run({"check": True}, args)
        print(f"{self.name}: torch {info['torch']}, device {info['device']}"
              + (f" ({info['gpu']})" if info.get("gpu") else "")
              + f"; cuda available: {info['cuda']}")
        return info

    def synth(self, job, paragraphs, args, tmp, model):
        """Send the engine's job with the paragraphs -> what engine.synth() returns."""
        wav, mp3 = tmp / "part.wav", tmp / "part.mp3"
        t = time.time()
        info = self.run({**job, "paragraphs": paragraphs, "wav": str(wav)}, args)
        align = []
        for para, starts, off0 in zip(paragraphs, info["starts"], para_offsets(paragraphs)):
            align += align_from_char_starts(para, starts, 0.0, off0)
        ffmpeg("-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3))
        print(f"    {self.name} on {info['device']}: {sum(map(len, paragraphs)):,} chars -> "
              f"{info['duration']:.1f}s in {time.time() - t:.0f}s")
        return mp3, align, info["duration"], 0, model
