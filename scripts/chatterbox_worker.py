#!/usr/bin/env python3
"""
The half of the Chatterbox engine (engines/chatterbox.py) that runs inside
the Chatterbox virtualenv (references/chatterbox.md); protocol in worker.py.
Job: {"voice": "default" | "/path/clip.wav", "knobs": {"exaggeration", "cfg",
"temperature", "seed"}, "paragraphs", "wav"}.

Chatterbox returns a waveform and nothing about time, so every chunk it
generates goes through the forced aligner (aligners/) with the chunk's own
text, and the word starts come back shifted by the running clock.
"""

import random
import sys

import aligners
import worker
from subtitles import words_with_offsets

RATE = worker.RATE            # ChatterboxTTS.sr
TAIL_S = 0.25                 # trailing silence kept on a chunk (the model leaves a longer, variable one)
TAIL_LEVEL = 1e-3


def seed_everything(n):
    import numpy as np
    import torch
    random.seed(n)
    np.random.seed(n)
    torch.manual_seed(n)
    torch.cuda.manual_seed_all(n)


class Chatterbox:
    def __init__(self, device):
        from chatterbox.tts import ChatterboxTTS
        self.device = device
        self.model = ChatterboxTTS.from_pretrained(device=device)
        self.default_conds = self.model.conds          # the voice that ships with the model
        self.voice = "default"

    def use_voice(self, voice, exaggeration):
        """Conditionals for one reference clip, built once per run, so every chunk has the same voice."""
        if voice == self.voice:
            return
        if voice == "default":
            self.model.conds = self.default_conds
        else:
            self.model.prepare_conditionals(voice, exaggeration=exaggeration)
        self.voice = voice

    def speak(self, text, knobs):
        """-> float32 numpy audio at RATE, trailing silence cut to TAIL_S. The seed is re-applied
        every call, so the same words give the same audio."""
        import numpy as np
        seed_everything(knobs["seed"])
        wav = self.model.generate(text, exaggeration=knobs["exaggeration"], cfg_weight=knobs["cfg"],
                                  temperature=knobs["temperature"])
        wav = wav[0].float().cpu().numpy()
        loud = np.flatnonzero(np.abs(wav) > TAIL_LEVEL)
        if len(loud):
            wav = wav[:min(len(wav), loud[-1] + int(TAIL_S * RATE))]
        return wav


class Track(worker.Track):
    max_chars = 300           # one generate() call; the model caps generation at ~40 s (issue #76)
    sentence_gap = 0.12

    def __init__(self, tts, knobs):
        super().__init__()
        self.tts, self.knobs = tts, knobs
        self.aligner = aligners.load()

    def speak(self, piece, base):
        wav = self.tts.speak(piece, self.knobs)
        timed = self.aligner.align(wav, RATE, piece, self.tts.device)
        for (off, word), (_, at) in zip(words_with_offsets(piece), timed):
            for k in range(off, off + len(word)):
                self.starts[base + k] = round(self.t + at, 3)
        self.add(wav)


def synthesise(job, state, device):
    if "tts" not in state:
        state["tts"] = Chatterbox(device)
    state["tts"].use_voice(job["voice"], job["knobs"]["exaggeration"])
    return Track(state["tts"], job["knobs"]).render(job["paragraphs"], job["wav"])


if __name__ == "__main__":
    worker.serve(worker.pick_device(sys.argv[1] if len(sys.argv) > 1 else None, "references/chatterbox.md",
                                    aligner=aligners.DEFAULT), synthesise)
