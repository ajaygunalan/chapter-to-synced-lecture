#!/usr/bin/env python3
"""
The half of the Kokoro engine (engines/kokoro.py) that runs inside the
Kokoro virtualenv (references/kokoro.md). It lives in scripts/ so that
lecture_format and subtitles import normally and nothing shadows the
kokoro package. One process per build_audio run: the model loads once.

    kokoro_worker.py [cuda|cpu]          jobs on stdin, one JSON per line; one JSON answer per line

    {"check": true}
        -> {"torch": version, "device": "cuda"|"cpu", "cuda": bool, "gpu": name|null}
    {"voice": "af_sky", "speed": 1.0, "paragraphs": ["…", …], "wav": "out.wav"}
        each paragraph exactly what the engine should say, pauses as
        <break time="Ns" /> tags (the same text any engine gets)
        -> {"duration": seconds, "device": …, "starts": [[per-character start
            time of paragraph 0], [of paragraph 1], …]}
           — the shape align_from_char_starts takes, so cues are built the
           same way for every engine
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


def synthesise(job, pipes, device):
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    lang = "b" if job["voice"].startswith("b") else "a"
    if lang not in pipes:
        pipes[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M", device=device)
    pipe, voice, speed = pipes[lang], job["voice"], float(job.get("speed", 1.0))
    chunks, t, all_starts = [], 0.0, []          # audio pieces and the running clock

    def silence(seconds):
        nonlocal t
        n = int(seconds * RATE)
        if n > 0:
            chunks.append(np.zeros(n, dtype=np.float32))
            t += n / RATE

    for pi, para in enumerate(job["paragraphs"]):
        starts = [None] * len(para)
        if pi:
            silence(PARAGRAPH_GAP)

        def speak(piece, base):
            """One sentence sitting at para[base:]; fill starts for its chars."""
            nonlocal t
            for r in pipe(piece, voice=voice, speed=speed):
                if r.audio is None:
                    continue
                audio = r.audio.cpu().numpy().astype(np.float32)
                cursor = 0
                for tok in r.tokens or []:
                    if not tok.text or tok.start_ts is None:
                        continue
                    at = piece.find(tok.text, cursor)
                    if at < 0:
                        continue
                    for k in range(at, at + len(tok.text)):
                        if starts[base + k] is None:
                            starts[base + k] = round(t + float(tok.start_ts), 3)
                    cursor = at + len(tok.text)
                chunks.append(audio)
                t += len(audio) / RATE

        def say(seg, base):
            """A stretch with no break tags: one pipeline call per sentence, so
            nothing exceeds the model's per-call length."""
            for i, (off, s) in enumerate(sentences_with_offsets(seg)):
                if i:
                    silence(SENTENCE_GAP)
                speak(s, base + off)

        p = 0
        for m in BREAK_RE.finditer(para):
            say(para[p:m.start()], p)
            for k in range(m.start(), m.end()):
                starts[k] = round(t, 3)
            silence(float(m.group(1)))
            p = m.end()
        say(para[p:], p)
        last = round(t, 3)                        # forward-fill whitespace and dropped punctuation
        for i in range(len(starts)):
            if starts[i] is None:
                starts[i] = last
            else:
                last = starts[i]
        all_starts.append(starts)

    audio = np.concatenate(chunks) if chunks else np.zeros(RATE // 10, dtype=np.float32)
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
