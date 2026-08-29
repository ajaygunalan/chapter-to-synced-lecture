# TADA

Hume's open-weights TADA-1B — https://github.com/HumeAI/tada — a 1B-parameter
Llama-3.2-based narrator: free, local, prosody from the sentence rather than a
fixed frame rate, and it returns the frame count before every text token, so
word timing comes from the model itself. Weights under the Llama 3.2 licence
(https://huggingface.co/HumeAI/tada-1b); the codec is `HumeAI/tada-codec`.
Engine code: `scripts/engines/tada.py` and, inside the virtualenv,
`scripts/tada_worker.py`.

## Setup (once)

```bash
uv venv ~/.local/share/tada-venv --python 3.12
uv pip install --python ~/.local/share/tada-venv/bin/python torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
uv pip install --python ~/.local/share/tada-venv/bin/python hume-tada soundfile
# hume-tada pulls a CPU torchvision that mismatches the CUDA torch; put the three back in step:
uv pip install --python ~/.local/share/tada-venv/bin/python --reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

The tokenizer is Meta's `meta-llama/Llama-3.2-1B`, a gated repo: accept the
licence once at https://huggingface.co/meta-llama/Llama-3.2-1B with the
account whose token is in `~/.cache/huggingface/token` (approval is usually
minutes). Weights (~5.8 GB) download on first use. `build_audio.py --check
--engine tada` prints the device and the voices. Set `TADA_PYTHON` for a venv
elsewhere.

## Memory

An 8 GB card is enough, in this order: the encoder (2.6 GB, fp32) builds the
voice prompt and is moved to the CPU; then the model loads (4.2 GB in bf16
with its decoder); generation peaks around 4.8 GB. Loading both at once is
6.8 GB and the waveform decode runs out. `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
helps fragmentation on long parts. Speed on an RTX 4060 laptop: about five
seconds of audio per second.

## Voices

TADA clones a voice from a reference recording plus its transcript. `lj` is
the LJSpeech sample shipped inside the package (a female audiobook narrator).
To add one: put `NAME.wav` (a clean 5–15 s of the speaker, 24 kHz mono is
ideal) and `NAME.txt` (exactly what is said) in `~/.config/tada-voices/`; it
then appears in `--check` and `--voice NAME` uses it. `--voice /path/x.wav`
with `x.txt` beside it also works. The prompt is built once per run.

## Timing

`GenerationOutput.time_before[k]` is the number of 50 Hz frames before the
k-th generated token's acoustic anchor; `generate()` trims the leading block
as silence, and a token's speech occupies the block after its own, so token k
starts at `sum(time_before[1..k]) / 50`. Tokens (`step_logs` entries whose
`n_frames_src` is not `prompted`) are matched to the paragraph's letters in
order; punctuation and special tokens carry no time. Verified against the
waveform's silences on a test sentence.

## Limits

- `speed_up_factor` (`--speed`) re-runs generation with scaled durations —
  costs a second pass.
- Text is normalised by the model (`normalize_text=True`); the script's
  words are already spoken forms, so this rarely changes anything, but a
  token the matcher cannot find in the paragraph is simply skipped and the
  next word inherits its time.
- Generation is per group of sentences (`MAX_CHARS` in the worker); prosody
  across a paragraph break is not modelled.
