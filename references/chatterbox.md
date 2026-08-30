# Chatterbox

The default voice. Resemble AI's open Chatterbox — https://github.com/resemble-ai/chatterbox —
the original 500M-parameter English model (MIT; weights at
https://huggingface.co/ResembleAI/chatterbox, nothing to sign): a Llama-style
token model over a speech codec, with two knobs no other local voice has —
how much feeling (`--exaggeration`) and how it paces (`--cfg`). It returns
a waveform and nothing about time, so the engine runs a forced aligner over
every chunk it makes (`sync-architecture.md`, "Aligners"). Engine code:
`scripts/engines/chatterbox.py` and, inside the virtualenv,
`scripts/chatterbox_worker.py`; aligner: `scripts/aligners/mms.py`.

## Setup (once)

```bash
uv venv ~/.local/share/chatterbox-venv --python 3.12
uv pip install --python ~/.local/share/chatterbox-venv/bin/python torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
uv pip install --python ~/.local/share/chatterbox-venv/bin/python chatterbox-tts soundfile
# chatterbox-tts pins torch 2.6 from PyPI, which drags the CUDA 12.4 libraries in; put the three back in step:
uv pip install --python ~/.local/share/chatterbox-venv/bin/python --reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

Its own virtualenv, because `chatterbox-tts` pins `transformers` (and pulls
`gradio`) — 7.4 GB with torch. The model (~3.3 GB) downloads from Hugging
Face on first use, ungated; the aligner's weights (1.2 GB) from PyTorch.
`build_audio.py --check` prints the device, the voices and the knobs. Set
`CHATTERBOX_PYTHON` for a venv elsewhere. The model runs with torch 2.11
despite its pin; if a future release does not, pin `chatterbox-tts==0.1.7`.

## Memory and speed

Measured on an RTX 4060 laptop (8 GB): about 6 GB resident through a long
part, with the aligner beside the model, so both stay on the GPU. About 2×
real time — Prim's eleven minutes in five and a half, a chapter in
thirty-five.

## The two knobs

Both apply to the whole run (`build_audio.py … --exaggeration 0.7 --cfg 0.3`)
and are recorded nowhere but the command line, so note them in `plan.md`
if they are not the defaults.

- `--exaggeration` (default 0.5): emotional intensity. 0.5 is a neutral
  reader; 0.7 leans in, above 1 shouts and becomes unstable. Higher values
  also speed the speech up.
- `--cfg` (default 0.5): classifier-free guidance weight — how closely the
  output follows the reference voice's pacing. Lower is faster and freer;
  Resemble's advice is `--cfg 0.3` for a fast-talking reference clip, or
  to pair a high exaggeration with a lower cfg to slow it back down. 0
  turns guidance off entirely.
- `--temperature` (0.8) and `--seed` (0): the seed is re-applied before
  every chunk, so the same words give the same audio on the same machine —
  a re-recorded part sounds like the one it replaces.

## Voices

`default` is the voice that ships with the model (`conds.pt`): a clear,
mid-register male reader. To add one, put `NAME.wav` in
`~/.config/chatterbox-voices/` — six to fifteen seconds of one speaker,
clean, no transcript needed (Chatterbox does not take one) — and `--voice
NAME` uses it; `--voice /path/x.wav` also works. The clip's conditionals
are built once per run so every chunk is the same voice. Audition with one
short part: `build_audio.py script.md --out DIR --part <key> --voice NAME
--force`.

## Chunking and the 40 s cap

`generate()` stops at 1,000 speech tokens — about forty seconds — and text
past that is silently dropped (https://github.com/resemble-ai/chatterbox/issues/76).
Over a long call the voice can also speed up or slur the end. So the
worker packs whole sentences into calls of at most 300 characters
(`max_chars`, about twenty seconds) — a sentence is never cut — and joins
the pieces with 0.12 s inside a paragraph and 0.45 s between paragraphs.
The model leaves a variable stretch of silence at the end of every call;
the worker trims it to 0.25 s so the pacing does not wander. Prosody is per
call: a sentence group is read as one breath, but nothing carries across
the join.

## Timing

Every chunk goes to the aligner (`aligners/mms.py`) with the text it was
made from; the word starts come back in the chunk's own clock and are
shifted by the running total. Checked on a probe paragraph against the
waveform's silences: every word after a pause starts within 30 ms of where
the silence ends. `verify_timing.py <outdir> <part>` re-runs the aligner
over the finished mp3 (`--device cpu` while a recording holds the card — a
minute for a ten-minute part).

## Watermark

Every output carries Resemble's inaudible Perth watermark; the library
prints `loaded PerthNet (Implicit)` when it starts, which is normal. It
stays on.

## Limits

- A word the model has never seen — an acronym, a name — may come out
  wrong. Pronunciation and emphasis: `narration-craft.md`.
- English only. Resemble's later models in the same package (Multilingual,
  Turbo) are the fallback if this one stops installing: the same worker,
  a different class.
