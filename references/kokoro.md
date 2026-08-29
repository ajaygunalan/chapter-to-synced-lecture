# Kokoro

The default engine, for every dry run: open-weight, runs on the laptop,
free, unlimited, and it returns the start time of every word, which is all
the sync needs. Model: https://huggingface.co/hexgrad/Kokoro-82M
(Apache 2.0). Library: https://github.com/hexgrad/kokoro.

Code: `scripts/engines/kokoro.py` (the engine contract is
`scripts/engines/__init__.py`) keeps one `scripts/kokoro_worker.py` process
alive for the run — it lives inside Kokoro's own virtualenv because Kokoro
pulls in torch, and loads the model once per run, not per part.

## Setup (once)

```bash
uv venv ~/.local/share/kokoro-venv --python 3.12
uv pip install --python ~/.local/share/kokoro-venv/bin/python torch --index-url https://download.pytorch.org/whl/cu128   # GPU
uv pip install --python ~/.local/share/kokoro-venv/bin/python kokoro soundfile
# misaki (Kokoro's English front end) needs spaCy's small English model; match spaCy's minor version:
V=$(~/.local/share/kokoro-venv/bin/python -c "import spacy; print('.'.join(spacy.__version__.split('.')[:2]))").0
uv pip install --python ~/.local/share/kokoro-venv/bin/python \
  https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-$V/en_core_web_sm-$V-py3-none-any.whl
sudo apt-get install -y espeak-ng          # fallback for words the dictionary lacks
```

Then `python3 scripts/build_audio.py --check` prints the torch build, the
device it will use, and the voices. Set `KOKORO_PYTHON` to use a venv
elsewhere. The model weights (~330 MB) download from Hugging Face on first
use.

## GPU or CPU

The worker uses `cuda` when torch can see a GPU and `cpu` otherwise;
`--device cpu|cuda` forces one, and every run prints which it used
(`kokoro on cuda: 9292 chars -> 742.1s in 40s`). The GPU build of torch
above is ~2.5 GB (CUDA 12.8 wheels; NVIDIA driver 570+). Without a GPU
use `--index-url https://download.pytorch.org/whl/cpu` instead: CPU is
still several times faster than real time (a 45-minute chapter in ~10
minutes on a laptop). If `--check` says `cuda available: False` on a
machine with an NVIDIA GPU, the venv has the CPU build — reinstall torch
with `--reinstall` from the cu128 index.

## Voices

`VOICES` in `scripts/engines/kokoro.py` maps short names to Kokoro ids
(`sky` → `af_sky`, the default); `--check` lists them; `--voice` takes a
name or an id. All of Kokoro-82M's English voices are there, American and
British, female and male. Audition with one short part: `build_audio.py
script.md --out DIR --part <key> --voice george --force`.

## What the worker does

One pipeline call per sentence (the model truncates long inputs), a short
silence between sentences and a longer one between paragraphs, and real
silence for `<break time="Ns" />` tags, so pauses before asks are pauses.
Each token's start time from the model becomes the start time of its
characters; whitespace and separators are forward-filled. The result is one
24 kHz wav and per-character start times, the shape every engine hands to
`align_from_char_starts`, so beats, marks, asks and subtitles are derived
the same way for every engine.

## Limits

Calm narration only: no emotional range, and the voice does not change
register for a joke or a quote. Occasional small artefacts at sentence
joins. Pronunciation of rare names follows the dictionary or espeak; the
script's `pronounce:` rules apply before synthesis (narration-craft.md,
"Script format"), so fix a name once and every engine says it.
