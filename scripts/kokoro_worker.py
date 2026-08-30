#!/usr/bin/env python3
"""
The half of the Kokoro engine (engines/kokoro.py) that runs inside the
Kokoro virtualenv (references/kokoro.md); protocol in worker.py. Job:
{"voice": "af_sky", "speed": 1.0, "paragraphs", "wav"}. It lives in scripts/
so that lecture_format and subtitles import normally and nothing shadows the
kokoro package.
"""

import sys

import worker


class Track(worker.Track):
    sentence_gap = 0.12       # one pipeline call per sentence, so nothing exceeds the model's per-call length

    def __init__(self, pipe, voice, speed):
        super().__init__()
        self.pipe, self.voice, self.speed = pipe, voice, speed

    def speak(self, piece, base):
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
            self.add(r.audio.cpu().numpy().astype(self.np.float32))


def synthesise(job, pipes, device):
    from kokoro import KPipeline
    lang = "b" if job["voice"].startswith("b") else "a"
    if lang not in pipes:
        pipes[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M", device=device)
    return Track(pipes[lang], job["voice"], float(job.get("speed", 1.0))).render(job["paragraphs"], job["wav"])


if __name__ == "__main__":
    worker.serve(worker.pick_device(sys.argv[1] if len(sys.argv) > 1 else None, "references/kokoro.md, GPU"),
                 synthesise)
