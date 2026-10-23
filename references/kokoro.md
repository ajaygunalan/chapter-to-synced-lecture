# Kokoro

The default voice (`--engine kokoro`, or nothing): hexgrad's Kokoro-82M,
https://huggingface.co/hexgrad/Kokoro-82M (Apache 2.0; library
https://github.com/hexgrad/kokoro). Open-weight, runs on the laptop, free,
unlimited, deterministic (the same words give the same audio, so a slip is
fixed once), a set of named voices, and it returns the start of every word
itself, so no forced aligner runs for it. Chatterbox (`chatterbox.md`) is
the expressive alternative, TADA (`tada.md`) the other. Engine code:
`scripts/engines/kokoro.py` and, inside the virtualenv,
`scripts/kokoro_worker.py`.

## Setup (once)

```bash
uv venv ~/.local/share/kokoro-venv --python 3.12
uv pip install --python ~/.local/share/kokoro-venv/bin/python torch --index-url https://download.pytorch.org/whl/cu128   # GPU
uv pip install --python ~/.local/share/kokoro-venv/bin/python kokoro soundfile faster-whisper
# misaki (Kokoro's English front end) needs spaCy's small English model; match spaCy's minor version:
V=$(~/.local/share/kokoro-venv/bin/python -c "import spacy; print('.'.join(spacy.__version__.split('.')[:2]))").0
uv pip install --python ~/.local/share/kokoro-venv/bin/python \
  https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-$V/en_core_web_sm-$V-py3-none-any.whl
# espeak-ng (the fallback for words the dictionary lacks) ships with the venv as espeakng_loader, but the loader
# looks for its data beside the interpreter's lib/, ignoring the path it is given; link it there:
V=~/.local/share/kokoro-venv; ln -s $V/lib/python3.12/site-packages/espeakng_loader/espeak-ng-data/* $V/lib/
```

Then `python3 scripts/build_audio.py --check` prints the torch build, the
device it will use, the lexicon and the voices. Set `KOKORO_PYTHON` to use
a venv elsewhere. The model weights (~330 MB) download from Hugging Face on
first use; so does Whisper's `small.en` (~500 MB) the first time
`verify_words.py` runs.

## GPU or CPU

The worker uses `cuda` when torch can see a GPU and `cpu` otherwise;
`--device cpu|cuda` forces one, and every run prints which it used. On an
RTX 4060 a minute of narration takes about ten seconds (the first call adds
a few seconds of model load); the CPU is still several times faster than
real time. If `--check` says `cuda available: False` on a machine with an
NVIDIA GPU, the venv has the CPU build — reinstall torch with `--reinstall`
from the cu128 index.

## Voices

`--check` lists them; `--voice` takes a short name or a Kokoro id
(`michael` → `am_michael`, the default). All of Kokoro-82M's English voices
are in `VOICES` in `scripts/engines/kokoro.py`: `am_`/`af_` American,
`bm_`/`bf_` British, male and female. A British voice runs the British
front end (different vowels in the dictionary; the lexicon serves both).
The voice is written into `cues/<part>.json` with the engine, and a part
recorded with another voice is re-recorded by the next run, so a deck's
voice is one decision kept in its cues (Robothesis rotates three voices
deck by deck: `robothesis-audio`'s `scripts/voice.py`). Audition with one
short part: `build_audio.py script.md --out DIR --part <key> --voice george
--force`.

## Pronunciation

Two levers, both free of the recording's text (the subtitles keep the
printed spelling either way):

- **The lexicon**, `references/kokoro-lexicon.json`: `{"Iglberger":
  "ˈɪɡəlbɜɹɡəɹ"}`, word → IPA in misaki's alphabet (stress marks `ˈ ˌ`;
  `A O W I Q` are the diphthongs eɪ oʊ aʊ aɪ ɔɪ; `ᵊ` a dropped schwa). Keys
  match case-insensitively; a deck adds its own with `--lexicon file.json`
  (repeatable). Try an entry before adding it:
  `~/.local/share/kokoro-venv/bin/python -c "from kokoro import KPipeline; p=KPipeline(lang_code='a', model=False); print(p.g2p('Iglberger')[0])"`
  prints what misaki would say now.
- **`pronounce:` respellings** in the script header, as for every engine
  (`narration-craft.md`), rewritten for misaki: a run of two or more
  capitals is an acronym to it (`IGG` → I-G-G), so the engine lower-cases
  those syllables (`IGG-el-bear-ger` → `igg-el-bear-ger`) and leaves
  single letters as letters (`S-R-P`). A respelling of a word the lexicon
  knows is dropped: the IPA is the better fix. Respellings go through
  espeak's letter rules, so a syllable like `ger` comes out "jer": when a
  respelling still sounds wrong, move the word to the lexicon.

Inline IPA also works in the text itself, `[Iglberger](/ˈɪɡəlbɜɹɡəɹ/)`,
but the script's words should stay prose; the lexicon is the place.

## Checking a recording

`scripts/verify_words.py <outdir> [<part> ...]` transcribes each part with
faster-whisper (`small.en`; `--model medium.en` hears names better) and
prints every word the transcript does not have, with its time; a part
passes with at most 2 % slips and no run of three. `scripts/verify_timing.py`
is the independent check of the word times against the MMS aligner
(Chatterbox's venv): a Kokoro part sits within 0.1 s at the 95th
percentile.

## Limits

Calm narration only: no emotional range, and the voice does not change
register for a joke or a quote; punctuation is the only lean (an ellipsis
or a full stop for a pause, `<!-- pause 2s -->` for a longer one). About
a third slower than Chatterbox's reading, with real sentence pauses. A
piece over 510 phonemes is split by the pipeline at punctuation; a
sentence with none that long gets cut mid-flow, so keep sentences
sentence-length. Occasional small artefacts at sentence joins.
