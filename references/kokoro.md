# Kokoro

The fallback voice (`--engine kokoro`): small, a minute a chapter, level.
The default is Chatterbox (`chatterbox.md`); TADA (`tada.md`) is the other
alternative. Open-weight, runs on the laptop, free,
unlimited, and it returns the start time of every word, which is all the
sync needs. Model:
https://huggingface.co/hexgrad/Kokoro-82M (Apache 2.0). Library:
https://github.com/hexgrad/kokoro. Engine code: `scripts/engines/kokoro.py`
and, inside the virtualenv, `scripts/kokoro_worker.py`.

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
`--device cpu|cuda` forces one, and every run prints which it used. The GPU
build of torch above needs an NVIDIA driver that supports CUDA 12.8.
Without a GPU use `--index-url https://download.pytorch.org/whl/cpu`
instead; the CPU is still several times faster than real time. If `--check`
says `cuda available: False` on a machine with an NVIDIA GPU, the venv has
the CPU build — reinstall torch with `--reinstall` from the cu128 index.

## Voices

`--check` lists them; `--voice` takes a short name or a Kokoro id
(`sky` → `af_sky`, the default). All of Kokoro-82M's English voices are in
`VOICES` in `scripts/engines/kokoro.py`, American and British, female and
male. Audition with one short part: `build_audio.py script.md --out DIR
--part <key> --voice george --force`.

## Limits

Calm narration only: no emotional range, and the voice does not change
register for a joke or a quote. Occasional small artefacts at sentence
joins. Pronunciation of rare names follows the dictionary or espeak; fix
one with a `pronounce:` line in the script.
