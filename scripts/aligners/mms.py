#!/usr/bin/env python3
"""
MMS forced aligner: torchaudio's MMS_FA bundle (Meta's wav2vec2 trained for
alignment over 1,100+ languages, https://docs.pytorch.org/audio/stable/tutorials/ctc_forced_alignment_api_tutorial.html)
plus torchaudio.functional.forced_align. Nothing beyond the torch every
engine virtualenv already installs; the bundle's weights (~1.2 GB) download
from PyTorch on first use.

    python aligners/mms.py <wav> <text-file> [cuda|cpu]     prints the JSON list

Words are reduced to the model's vocabulary [a-z'] by normalise(): lowercase,
accents stripped, integers spelt out, everything else dropped.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # subtitles, when run as a script
from subtitles import words_with_offsets                          # noqa: E402

RATE = 16000                  # MMS_FA.sample_rate
WINDOW_S = 30                 # seconds of audio per emission pass (attention is quadratic in it)
PAD_S = 1                     # context heard on either side of a window, not scored
_loaded = {}

_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _num_words(n):
    """An integer as English words (what the voice said for the digits in the script)."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    for unit, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand"), (100, "hundred")):
        if n >= unit:
            head = _num_words(n // unit) + " " + name
            return head if n % unit == 0 else head + " " + _num_words(n % unit)
    return ""


def normalise(word):
    """A word of the script -> its letters in the MMS vocabulary, or ''."""
    w = unicodedata.normalize("NFKD", word.replace("’", "'")).encode("ascii", "ignore").decode().lower()
    w = re.sub(r"\d+", lambda m: " " + _num_words(int(m.group())) + " ", w)
    return re.sub(r"[^a-z']", "", w)


def _model(device):
    if device not in _loaded:
        import torchaudio
        bundle = torchaudio.pipelines.MMS_FA
        _loaded[device] = (bundle.get_model(with_star=False).to(device).eval(), bundle.get_dict(star=None))
    return _loaded[device]


def align(samples, rate, text, device=None):
    import torch
    import torchaudio.functional as F
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model, vocab = _model(device)
    words = words_with_offsets(text)
    per_word, targets = [], []
    for _, w in words:
        ids = [vocab[c] for c in normalise(w) if c in vocab]
        per_word.append(len(ids))
        targets += ids
    wave = torch.as_tensor(samples, dtype=torch.float32)
    if wave.ndim > 1:
        wave = wave.mean(dim=-1)
    if rate != RATE:
        wave = F.resample(wave, rate, RATE)
    wave = wave.unsqueeze(0).to(device)

    # emissions window by window, each run with PAD_S of context on either side and only its
    # own frames kept, so a word on a window edge is heard whole; frame_t[f] = seconds at frame f
    emissions, frame_t = [], []
    step, pad, total = WINDOW_S * RATE, PAD_S * RATE, wave.size(1)
    with torch.inference_mode():
        for w0 in range(0, total, step):
            lo, hi = max(0, w0 - pad), min(total, w0 + step + pad)
            piece = wave[:, lo:hi]
            if piece.size(1) < 800:                          # shorter than the model's receptive field
                continue
            em, _ = model(piece)
            per_frame = piece.size(1) / em.size(1)           # samples per frame (about 320)
            a = round((w0 - lo) / per_frame)
            b = a + round(min(step, total - w0) / per_frame)
            em = em[0, a:b]
            emissions.append(em)
            frame_t += [(lo + f * per_frame) / RATE for f in range(a, a + em.size(0))]
    if not targets or not emissions:
        return [[off, 0.0] for off, _ in words]
    emission = torch.cat(emissions).unsqueeze(0)
    t = torch.tensor([targets], dtype=torch.int32, device=device)
    try:
        aligned, scores = F.forced_align(emission, t, blank=0)
    except RuntimeError as e:                                # more tokens than frames: audio far too short
        print(f"mms: forced_align failed ({e}); spreading {len(words)} words evenly", file=sys.stderr)
        return [[off, round(frame_t[-1] * i / len(words), 3)] for i, (off, _) in enumerate(words)]
    spans = F.merge_tokens(aligned[0].cpu(), scores[0].cpu())   # one span per target token, in order
    out, k, last = [], 0, 0.0
    for (off, _), n in zip(words, per_word):
        if n:
            last = round(frame_t[spans[k].start], 3)
            k += n
        out.append([off, last])
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    import soundfile as sf
    data, rate = sf.read(sys.argv[1], dtype="float32")
    print(json.dumps(align(data, rate, Path(sys.argv[2]).read_text(), sys.argv[3] if len(sys.argv) > 3 else None)))


if __name__ == "__main__":
    main()
