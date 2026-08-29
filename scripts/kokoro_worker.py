#!/usr/bin/env python3
"""
The half of the Kokoro engine (engines/kokoro.py) that runs inside the
Kokoro virtualenv. It lives in scripts/ so that lecture_format and
subtitles import normally and nothing shadows the kokoro package.

    kokoro_worker.py [cuda|cpu]          jobs on stdin, one JSON per line; one JSON answer per line

    {"check": true}
        -> {"torch": version, "device": "cuda"|"cpu", "cuda": bool, "gpu": name|null}
    {"voice": "af_sky", "speed": 1.0, "paragraphs": ["…", …], "wav": "out.wav"}
        each paragraph exactly what the engine should say, pauses as
        <break time="Ns" /> tags (the same text any engine gets)
        -> {"duration": seconds, "device": …, "starts": [[per-character start
            time of paragraph 0], [of paragraph 1], …]}  (align_from_char_starts' input)
"""

import json
import sys
import warnings

from lecture_format import BREAK_RE
from subtitles import sentences_with_offsets

warnings.filterwarnings("ignore")
RATE = 24000
PARAGRAPH_GAP = 0.45      # seconds of silence between paragraphs
SENTENCE_GAP = 0.12       # between sentences of one paragraph


def pick_device(wanted):
    import torch
    cuda = torch.cuda.is_available()
    device = wanted or ("cuda" if cuda else "cpu")
    if device == "cuda" and not cuda:
        sys.exit("cuda requested but torch.cuda.is_available() is False (references/kokoro.md, GPU)")
    return {"torch": torch.__version__, "device": device, "cuda": cuda,
            "gpu": torch.cuda.get_device_name(0) if cuda else None}


class Track:
    """Audio pieces and the running clock; per-character start times of the current paragraph."""

    def __init__(self, pipe, voice, speed):
        import numpy as np
        self.np, self.pipe, self.voice, self.speed = np, pipe, voice, speed
        self.chunks, self.t, self.starts = [], 0.0, []

    def silence(self, seconds):
        n = int(seconds * RATE)
        if n > 0:
            self.chunks.append(self.np.zeros(n, dtype=self.np.float32))
            self.t += n / RATE

    def speak(self, piece, base):
        """One sentence sitting at paragraph[base:]; fill starts for its chars."""
        for r in self.pipe(piece, voice=self.voice, speed=self.speed):
            if r.audio is None:
                continue
            cursor = 0
            for tok in r.tokens or []:
                if not tok.text or tok.start_ts is None:
                    continue
                at = piece.find(tok.text, cursor)
                if at < 0:
                    continue
                for k in range(at, at + len(tok.text)):
                    if self.starts[base + k] is None:
                        self.starts[base + k] = round(self.t + float(tok.start_ts), 3)
                cursor = at + len(tok.text)
            audio = r.audio.cpu().numpy().astype(self.np.float32)
            self.chunks.append(audio)
            self.t += len(audio) / RATE

    def say(self, seg, base):
        """A stretch with no break tags: one pipeline call per sentence, so nothing
        exceeds the model's per-call length."""
        for i, (off, s) in enumerate(sentences_with_offsets(seg)):
            if i:
                self.silence(SENTENCE_GAP)
            self.speak(s, base + off)

    def paragraph(self, para):
        """-> per-character start times for one paragraph (whitespace forward-filled)."""
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


def synthesise(job, pipes, device):
    import soundfile as sf
    from kokoro import KPipeline

    lang = "b" if job["voice"].startswith("b") else "a"
    if lang not in pipes:
        pipes[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M", device=device)
    track = Track(pipes[lang], job["voice"], float(job.get("speed", 1.0)))
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
    info = pick_device(sys.argv[1] if len(sys.argv) > 1 else None)
    pipes = {}
    for line in sys.stdin:
        job = json.loads(line)
        out = info if job.get("check") else synthesise(job, pipes, info["device"])
        print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
