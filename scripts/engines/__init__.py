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

Adding an engine is one new module here plus its name in ENGINES.
"""

from importlib import import_module

ENGINES = ("kokoro", "elevenlabs")
DEFAULT = "kokoro"
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
