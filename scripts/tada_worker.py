#!/usr/bin/env python3
"""
The half of the TADA engine (engines/tada.py) that runs inside the TADA
virtualenv (references/tada.md). Same protocol as kokoro_worker.py:

    tada_worker.py [cuda|cpu]            jobs on stdin, one JSON per line; one JSON answer per line

    {"check": true}
        -> {"torch": version, "device": "cuda"|"cpu", "cuda": bool, "gpu": name|null}
    {"voice": "/path/ref.wav", "voice_text": "…transcript…", "speed": 1.0,
     "paragraphs": ["…", …], "wav": "out.wav"}
        -> {"duration": seconds, "device": …, "starts": [[per-character start
            time of paragraph 0], …]}   (align_from_char_starts' input)

Word timing comes from the model itself: each generated text token carries
the number of 20 ms frames before its acoustic anchor (GenerationOutput
.time_before, 50 frames/s). The public generate() drops the leading block as
silence, and a token's speech occupies the block after its own, so the k-th
generated token starts at sum(time_before[1..k]) / 50 — checked against the
waveform's own silences.
"""

import json
import re
import sys
import warnings

from lecture_format import BREAK_RE
from subtitles import sentences_with_offsets

warnings.filterwarnings("ignore")
RATE = 24000
FPS = 50                      # acoustic frames per second
PARAGRAPH_GAP = 0.45
SENTENCE_GAP = 0.0            # the model paces sentences itself inside one call
MAX_CHARS = 420               # one generate() call; a paragraph longer than this is split at sentence ends
LJ_TEXT = ("The examination and testimony of the experts, enabled the commission to conclude "
           "that five shots may have been fired.")


def pick_device(wanted):
    import torch
    cuda = torch.cuda.is_available()
    device = wanted or ("cuda" if cuda else "cpu")
    if device == "cuda" and not cuda:
        sys.exit("cuda requested but torch.cuda.is_available() is False (references/tada.md)")
    return {"torch": torch.__version__, "device": device, "cuda": cuda,
            "gpu": torch.cuda.get_device_name(0) if cuda else None}


class Tada:
    def __init__(self, device):
        import torch
        from tada.modules.tada import TadaForCausalLM
        self.torch, self.device = torch, device
        self.model = TadaForCausalLM.from_pretrained("HumeAI/tada-1b", dtype=torch.bfloat16).to(device)
        self.prompts = {}

    def prompt(self, voice, voice_text):
        """The voice prompt for one reference recording, built once per run. The encoder is
        2.6 GB and only needed here, so it visits the GPU and leaves."""
        key = (voice, voice_text)
        if key not in self.prompts:
            import soundfile as sf
            from tada.modules.encoder import Encoder
            torch = self.torch
            encoder = Encoder.from_pretrained("HumeAI/tada-codec", subfolder="encoder").to(self.device)
            data, sr = sf.read(voice, dtype="float32", always_2d=True)
            audio = torch.from_numpy(data.T).to(self.device)
            with torch.no_grad():
                self.prompts[key] = encoder(audio, text=[voice_text], sample_rate=sr)
            encoder.to("cpu")
            del encoder, audio
            if self.device == "cuda":
                torch.cuda.empty_cache()
        return self.prompts[key]

    def speak(self, text, prompt, speed):
        """-> (float32 numpy audio, [(token text, start seconds)])"""
        from tada.modules.tada import InferenceOptions
        torch = self.torch
        opts = InferenceOptions(speed_up_factor=None if abs(speed - 1.0) < 1e-3 else speed)
        torch.manual_seed(0)
        out = self.model.generate(prompt=prompt, text=text, inference_options=opts)
        wav = out.audio[0].float().cpu().numpy()
        steps = [s for s in out.step_logs if s["n_frames_src"] != "prompted"]
        blocks = out.time_before[0].tolist()
        words, t = [], 0
        for k, s in enumerate(steps):
            if k >= len(blocks):
                break
            if k > 0:
                t += blocks[k]
            tok = s["token"]
            if k > 0 and not tok.startswith("<|"):
                words.append((tok.replace("Ġ", " ").replace("Ċ", "\n"), t / FPS))
        return wav, words


def key_chars(s):
    """Lowercase letters and digits of s with their positions — what token text is matched on."""
    return [(i, c.lower()) for i, c in enumerate(s) if c.isalnum()]


class Track:
    """Audio pieces and the running clock; per-character start times of the current paragraph."""

    def __init__(self, tts, prompt, speed):
        import numpy as np
        self.np, self.tts, self.prompt, self.speed = np, tts, prompt, speed
        self.chunks, self.t, self.starts = [], 0.0, []

    def silence(self, seconds):
        n = int(seconds * RATE)
        if n > 0:
            self.chunks.append(self.np.zeros(n, dtype=self.np.float32))
            self.t += n / RATE

    def speak(self, piece, base):
        """One stretch of text at paragraph[base:]; fill starts for its characters."""
        wav, words = self.tts.speak(piece, self.prompt, self.speed)
        keys = key_chars(piece)
        cursor = 0
        for tok, at in words:
            tk = [c.lower() for c in tok if c.isalnum()]
            if not tk:
                continue
            # find the token's letters in the piece, in order, from the cursor
            for j in range(cursor, len(keys) - len(tk) + 1):
                if [c for _, c in keys[j:j + len(tk)]] == tk:
                    first = keys[j][0]
                    for k in range(first, keys[j + len(tk) - 1][0] + 1):
                        if self.starts[base + k] is None:
                            self.starts[base + k] = round(self.t + at, 3)
                    cursor = j + len(tk)
                    break
        self.chunks.append(wav)
        self.t += len(wav) / RATE

    def say(self, seg, base):
        """A stretch with no break tags: sentences packed into calls of at most MAX_CHARS."""
        group, goff = [], None
        for off, s in sentences_with_offsets(seg):
            if group and sum(len(x) for x in group) + len(s) > MAX_CHARS:
                self.speak(seg[goff:off].strip(), base + goff)
                group, goff = [], None
            if goff is None:
                goff = off
            group.append(s)
        if group:
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
        state["tts"] = Tada(device)
    tts = state["tts"]
    prompt = tts.prompt(job["voice"], job.get("voice_text") or LJ_TEXT)
    track = Track(tts, prompt, float(job.get("speed", 1.0)))
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
    state = {}
    for line in sys.stdin:
        job = json.loads(line)
        out = info if job.get("check") else synthesise(job, state, info["device"])
        print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
