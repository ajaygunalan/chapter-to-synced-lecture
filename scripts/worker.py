"""
What the local voice workers share — tada_worker.py, kokoro_worker.py,
chatterbox_worker.py — so the protocol, the device and the audio bookkeeping
exist once. A worker runs inside its engine's virtualenv and supplies a model
plus a Track.speak(); the engine side is engines.Worker.

    <name>_worker.py [cuda|cpu]          jobs on stdin, one JSON per line; one JSON answer per line

    {"check": true}
        -> {"torch": version, "device": "cuda"|"cpu", "cuda": bool, "gpu": name|null, …}
    {…engine's job…, "paragraphs": ["…", …], "wav": "out.wav"}
        each paragraph exactly what the engine should say, pauses as
        <break time="Ns" /> tags
        -> {"duration": seconds, "device": …, "starts": [[per-character start
            time of paragraph 0], [of paragraph 1], …]}  (align_from_char_starts' input)

Only answers may reach stdout — the libraries print (download bars, a
watermarker's greeting) — so serve() sends stdout to stderr for the life of
the process and writes answers through the original handle.
"""

import json
import sys
import warnings

from lecture_format import BREAK_RE
from subtitles import sentences_with_offsets

warnings.filterwarnings("ignore")
RATE = 24000
PARAGRAPH_GAP = 0.45          # seconds of silence between paragraphs


def pick_device(wanted, doc, **extra):
    """-> the check answer; exits if cuda was asked for and is not there."""
    import torch
    cuda = torch.cuda.is_available()
    device = wanted or ("cuda" if cuda else "cpu")
    if device == "cuda" and not cuda:
        sys.exit(f"cuda requested but torch.cuda.is_available() is False ({doc})")
    return {"torch": torch.__version__, "device": device, "cuda": cuda,
            "gpu": torch.cuda.get_device_name(0) if cuda else None, **extra}


class Track:
    """Audio pieces and the running clock; per-character start times of the current
    paragraph. A subclass supplies speak(piece, base): make the audio for one stretch
    of text sitting at paragraph[base:], hand it to add(), and stamp self.starts for
    the characters it timed (whitespace and the rest are forward-filled here)."""

    max_chars = 0             # sentences packed into one speak() up to this many chars; 0: one sentence per call
    sentence_gap = 0.0        # silence between two speak() calls inside a paragraph

    def __init__(self):
        import numpy as np
        self.np = np
        self.chunks, self.t, self.starts = [], 0.0, []

    def silence(self, seconds):
        n = int(seconds * RATE)
        if n > 0:
            self.chunks.append(self.np.zeros(n, dtype=self.np.float32))
            self.t += n / RATE

    def add(self, audio):
        """Append one piece of float32 audio at RATE."""
        self.chunks.append(audio)
        self.t += len(audio) / RATE

    def say(self, seg, base):
        """A stretch with no break tags: its sentences, packed into speak() calls."""
        pieces, size = [], 0
        for off, s in sentences_with_offsets(seg):
            if not pieces or size + len(s) > self.max_chars:
                pieces.append(off)
                size = 0
            size += len(s)
        for i, (a, b) in enumerate(zip(pieces, pieces[1:] + [len(seg)])):
            if i:
                self.silence(self.sentence_gap)
            self.speak(seg[a:b].strip(), base + a)

    def paragraph(self, para):
        """-> per-character start times for one paragraph; a break tag is stamped
        where its silence starts, and every unstamped character takes the time of
        the last stamped one before it."""
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

    def render(self, paragraphs, wav):
        """Speak the paragraphs in turn, write wav -> the synth answer (minus "device")."""
        import soundfile as sf
        all_starts = []
        for pi, para in enumerate(paragraphs):
            if pi:
                self.silence(PARAGRAPH_GAP)
            all_starts.append(self.paragraph(para))
        np = self.np
        audio = np.concatenate(self.chunks) if self.chunks else np.zeros(RATE // 10, dtype=np.float32)
        sf.write(wav, audio, RATE)
        return {"duration": round(len(audio) / RATE, 3), "starts": all_starts}


def serve(info, synthesise):
    """Answer jobs on stdin until it closes. synthesise(job, state, device) -> Track.render()'s
    answer; state is a dict the worker keeps its loaded model in."""
    answers, sys.stdout = sys.stdout, sys.stderr
    state = {}
    for line in sys.stdin:
        job = json.loads(line)
        out = info if job.get("check") else {"device": info["device"], **synthesise(job, state, info["device"])}
        print(json.dumps(out), file=answers, flush=True)
