#!/usr/bin/env python3
"""
The half of the Chatterbox engine (engines/chatterbox.py) that runs inside
the Chatterbox virtualenv (references/chatterbox.md). Same protocol as
tada_worker.py:

    chatterbox_worker.py [cuda|cpu]      jobs on stdin, one JSON per line; one JSON answer per line

    {"check": true}
        -> {"torch": version, "device": "cuda"|"cpu", "cuda": bool, "gpu": name|null,
            "aligner": name}
    {"voice": "/path/clip.wav" | null, "exaggeration": 0.5, "cfg": 0.5, "temperature": 0.8,
     "seed": 0, "paragraphs": ["…", …], "wav": "out.wav"}
        -> {"duration": seconds, "device": …, "starts": [[per-character start
            time of paragraph 0], …]}   (align_from_char_starts' input)

Chatterbox returns a waveform and nothing about time, so after every chunk
it generates, the forced aligner (aligners/, default "mms") is run over
that chunk with the chunk's own text, and the word starts it finds are
shifted by the running clock. A chunk is at most MAX_CHARS of whole
sentences, well inside the model's 40 s generation cap; the seed is
re-applied before every generate() so the same words give the same audio.
"""

import json
import random
import sys
import warnings

import aligners
from lecture_format import BREAK_RE
from subtitles import sentences_with_offsets, words_with_offsets

warnings.filterwarnings("ignore")
RATE = 24000                  # ChatterboxTTS.sr
PARAGRAPH_GAP = 0.45
SENTENCE_GAP = 0.12           # between two generate() calls inside one paragraph
MAX_CHARS = 300               # one generate() call; the model caps generation at ~40 s (issue #76)
TAIL_S = 0.25                 # trailing silence kept on a chunk (the model often leaves a longer one)
TAIL_LEVEL = 1e-3


def pick_device(wanted):
    import torch
    cuda = torch.cuda.is_available()
    device = wanted or ("cuda" if cuda else "cpu")
    if device == "cuda" and not cuda:
        sys.exit("cuda requested but torch.cuda.is_available() is False (references/chatterbox.md)")
    return {"torch": torch.__version__, "device": device, "cuda": cuda,
            "gpu": torch.cuda.get_device_name(0) if cuda else None, "aligner": aligners.DEFAULT}


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
        self.voice = None

    def use_voice(self, path, exaggeration):
        """Conditionals for one reference clip, built once per run, so every chunk has the same voice."""
        if path == self.voice:
            return
        if path is None:
            self.model.conds = self.default_conds
        else:
            self.model.prepare_conditionals(path, exaggeration=exaggeration)
        self.voice = path

    def speak(self, text, knobs):
        """-> float32 numpy audio at RATE, trailing silence cut to TAIL_S."""
        import numpy as np
        seed_everything(knobs["seed"])
        wav = self.model.generate(text, exaggeration=knobs["exaggeration"], cfg_weight=knobs["cfg"],
                                  temperature=knobs["temperature"])
        wav = wav[0].float().cpu().numpy()
        loud = np.flatnonzero(np.abs(wav) > TAIL_LEVEL)
        if len(loud):
            wav = wav[:min(len(wav), loud[-1] + int(TAIL_S * RATE))]
        return wav


class Track:
    """Audio pieces and the running clock; per-character start times of the current paragraph."""

    def __init__(self, tts, knobs, device):
        import numpy as np
        self.np, self.tts, self.knobs, self.device = np, tts, knobs, device
        self.aligner = aligners.load()
        self.chunks, self.t, self.starts = [], 0.0, []

    def silence(self, seconds):
        n = int(seconds * RATE)
        if n > 0:
            self.chunks.append(self.np.zeros(n, dtype=self.np.float32))
            self.t += n / RATE

    def speak(self, piece, base):
        """One stretch of text at paragraph[base:]; fill starts for its characters."""
        wav = self.tts.speak(piece, self.knobs)
        timed = self.aligner.align_samples(wav, RATE, piece, self.device)
        for (off, word), (_, at) in zip(words_with_offsets(piece), timed):
            for k in range(off, off + len(word)):
                self.starts[base + k] = round(self.t + at, 3)
        self.chunks.append(wav)
        self.t += len(wav) / RATE

    def say(self, seg, base):
        """A stretch with no break tags: sentences packed into calls of at most MAX_CHARS."""
        group, goff, first = [], None, True
        for off, s in sentences_with_offsets(seg):
            if group and sum(len(x) for x in group) + len(s) > MAX_CHARS:
                if not first:
                    self.silence(SENTENCE_GAP)
                self.speak(seg[goff:off].strip(), base + goff)
                group, goff, first = [], None, False
            if goff is None:
                goff = off
            group.append(s)
        if group:
            if not first:
                self.silence(SENTENCE_GAP)
            self.speak(seg[goff:].strip(), base + goff)

    def paragraph(self, para):
        self.starts = [None] * len(para)
        p = 0
        for m in BREAK_RE.finditer(para):
            self.say(para[p:m.start()], p)
            for k in range(m.start(), m.end()):
                self.starts[k] = round(self.t, 3)
            self.silence(float(m.group(1)))
            p = m.end()
        self.say(para[p:], p)
        last = round(self.t, 3)
        for i, s in enumerate(self.starts):
            if s is None:
                self.starts[i] = last
            else:
                last = s
        return self.starts


def synthesise(job, state, device):
    import soundfile as sf
    if "tts" not in state:
        state["tts"] = Chatterbox(device)
    tts = state["tts"]
    knobs = {"exaggeration": float(job.get("exaggeration", 0.5)), "cfg": float(job.get("cfg", 0.5)),
             "temperature": float(job.get("temperature", 0.8)), "seed": int(job.get("seed", 0))}
    tts.use_voice(job.get("voice"), knobs["exaggeration"])
    track = Track(tts, knobs, device)
    all_starts = []
    for pi, para in enumerate(job["paragraphs"]):
        if pi:
            track.silence(PARAGRAPH_GAP)
        all_starts.append(track.paragraph(para))
    np = track.np
    audio = np.concatenate(track.chunks) if track.chunks else np.zeros(RATE // 10, dtype=np.float32)
    sf.write(job["wav"], audio, RATE)
    return {"duration": round(len(audio) / RATE, 3), "device": device, "starts": all_starts}


def main():
    answers, sys.stdout = sys.stdout, sys.stderr      # the library prints; only answers may reach the engine
    info = pick_device(sys.argv[1] if len(sys.argv) > 1 else None)
    state = {}
    for line in sys.stdin:
        job = json.loads(line)
        out = info if job.get("check") else synthesise(job, state, info["device"])
        print(json.dumps(out), file=answers, flush=True)


if __name__ == "__main__":
    main()
