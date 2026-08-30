#!/usr/bin/env python3
"""
The half of the TADA engine (engines/tada.py) that runs inside the TADA
virtualenv (references/tada.md); protocol in worker.py. Job: {"voice":
"/path/ref.wav", "voice_text": "…transcript…", "speed": 1.0, "paragraphs", "wav"}.

Word timing comes from the model itself: each generated text token carries
the number of 20 ms frames before its acoustic anchor (GenerationOutput
.time_before, 50 frames/s). The public generate() drops the leading block as
silence, and a token's speech occupies the block after its own, so the k-th
generated token starts at sum(time_before[1..k]) / 50 — checked against the
waveform's own silences.
"""

import sys

import worker

FPS = 50                      # acoustic frames per second
LJ_TEXT = ("The examination and testimony of the experts, enabled the commission to conclude "
           "that five shots may have been fired.")


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


class Track(worker.Track):
    max_chars = 420           # one generate() call; the model paces sentences itself inside it

    def __init__(self, tts, prompt, speed):
        super().__init__()
        self.tts, self.prompt, self.speed = tts, prompt, speed

    def speak(self, piece, base):
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
        self.add(wav)


def synthesise(job, state, device):
    if "tts" not in state:
        state["tts"] = Tada(device)
    prompt = state["tts"].prompt(job["voice"], job.get("voice_text") or LJ_TEXT)
    return Track(state["tts"], prompt, float(job.get("speed", 1.0))).render(job["paragraphs"], job["wav"])


if __name__ == "__main__":
    worker.serve(worker.pick_device(sys.argv[1] if len(sys.argv) > 1 else None, "references/tada.md"), synthesise)
