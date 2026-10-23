#!/usr/bin/env python3
"""
Did the voice say the words? A listener that cannot be fooled by timing:
Whisper transcribes the recording and the transcript is compared with the
text the engine was given.

    verify_words.py <outdir> [<part> ...] [--model small.en] [--device cuda|cpu] [--tolerance 0.02]

For each part (every recorded one by default): audio/<part>.mp3 is
transcribed by faster-whisper (no prompt, so a name it cannot hear is a
name the voice did not say clearly), both texts are normalised (lower
case, digits spelt out, punctuation and hyphens gone, so a respelling and
the printed word compare as letters) and aligned word by word. A word pair
that differs in a letter or two is a hearing difference and passes; a word
replaced by something else, dropped or added is a slip, printed with the
time the cues give it, the words around it, and what Whisper heard.
Summary per part: words, slips, the longest run of them. Exit status 1
when a part's slips exceed --tolerance of its words or a run of 3 or more
(a skipped or garbled stretch). Kokoro is deterministic: a slip there is
fixed with a lexicon entry or a pronounce: line (references/kokoro.md),
not a new seed; Chatterbox parts re-record with another --seed.

Needs torch and faster-whisper, so it runs itself under the Kokoro
virtualenv's python (WHISPER_PYTHON overrides). The model (small.en by
default, ~500 MB) downloads from Hugging Face on first use.
"""

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lecture_format import BREAK_RE, align_path, audio_path, cue_path, parse_parts, text_path   # noqa: E402
from subtitles import words_with_offsets                                                        # noqa: E402

PYTHON = Path(os.environ.get("WHISPER_PYTHON") or os.environ.get("KOKORO_PYTHON")
              or Path.home() / ".local/share/kokoro-venv/bin/python")
_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
LINK_RE = re.compile(r"\[([^\]]+)\]\(/[^)]*/\)")        # [word](/ipa/) -> word


def num_words(n):
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + num_words(n % 100))
    if 1100 <= n <= 2099 and n % 100:                       # a year, or "twenty twenty"
        return num_words(n // 100) + " " + num_words(n % 100)
    if n < 10000:
        return _ONES[n // 1000] + " thousand" + ("" if n % 1000 == 0 else " " + num_words(n % 1000))
    return " ".join(_ONES[int(d)] for d in str(n))


def normalise(word):
    """One printed or transcribed word -> its tokens for comparison ('' tokens dropped)."""
    w = LINK_RE.sub(r"\1", word).lower()
    w = w.replace("c++", "c plus plus").replace("++", " plus plus ").replace("&", " and ")
    w = re.sub(r"\d+", lambda m: " " + num_words(int(m.group())) + " ", w)
    w = re.sub(r"[^a-z' ]+", "", w.replace("-", "").replace("’", "'"))
    return [t.strip("'") for t in w.split() if t.strip("'")]


def ref_tokens(text):
    """[(token, word index)] for the text the engine got, break tags dropped."""
    tags = [(m.start(), m.end()) for m in BREAK_RE.finditer(text)]
    out = []
    for i, (off, word) in enumerate(words_with_offsets(text)):
        if any(a <= off < b for a, b in tags):
            continue
        out += [(t, i) for t in normalise(word)]
    return out


def transcribe(model, mp3):
    import soundfile as sf
    with tempfile.TemporaryDirectory(prefix="verify-words-") as tmp:
        wav = Path(tmp) / "part.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", "16000", str(wav)], check=True)
        data, _ = sf.read(wav, dtype="float32")
    segs, _ = model.transcribe(data, beam_size=5, language="en", vad_filter=False, condition_on_previous_text=False)
    return " ".join(s.text.strip() for s in segs)


def soft(a, b):
    """Two runs of tokens that are the same word heard a little differently."""
    return difflib.SequenceMatcher(None, "".join(a), "".join(b), autojunk=False).ratio() >= 0.75


def compare(ref, hyp, align, text):
    """-> [(time, kind, ref words, heard words)] slips; ref: [(token, word index)], hyp: [token]."""
    r = [t for t, _ in ref]
    slips = []
    words = [w for _, w in words_with_offsets(text)]
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, r, hyp, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace" and soft(r[i1:i2], hyp[j1:j2]):
            continue
        if tag == "insert" and (j2 - j1) == 1 and len(hyp[j1]) <= 2:       # "a", "uh": not a word the voice owed
            continue
        wi = ref[i1][1] if i1 < len(ref) else ref[-1][1]
        said = " ".join(dict.fromkeys(words[ref[k][1]] for k in range(i1, max(i2, i1 + 1)) if k < len(ref)))
        slips.append((align[wi][1] if wi < len(align) else 0.0, tag, said, " ".join(hyp[j1:j2])))
    return slips


def main():
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        if Path(sys.executable).resolve() == PYTHON.resolve() or not PYTHON.exists():
            sys.exit(f"faster-whisper is not installed in {PYTHON} (references/kokoro.md: Setup); WHISPER_PYTHON overrides")
        os.execv(str(PYTHON), [str(PYTHON), __file__] + sys.argv[1:])

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", type=Path)
    ap.add_argument("parts", nargs="*", help="default: every recorded part, in script order")
    ap.add_argument("--model", default="small.en", help="a faster-whisper model name (small.en, medium.en, large-v3)")
    ap.add_argument("--device", choices=["cuda", "cpu"])
    ap.add_argument("--tolerance", type=float, default=0.02, help="slips allowed, as a share of the part's words")
    args = ap.parse_args()

    import torch                     # loads the CUDA libraries ctranslate2 wants before it looks for them
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device=device, compute_type="float16" if device == "cuda" else "int8")

    script = args.out / "script.md"
    keys = args.parts or (list(parse_parts(script.read_text())[1]) if script.exists()
                          else sorted(p.stem for p in (args.out / "audio").glob("*.mp3")))
    bad = False
    for key in keys:
        mp3, txt, alf = audio_path(args.out, key), text_path(args.out, key), align_path(args.out, key)
        if not mp3.exists() or not txt.exists():
            print(f"{key}: not recorded")
            continue
        text = txt.read_text()
        align = json.loads(alf.read_text())["words"] if alf.exists() else []
        ref = ref_tokens(text)
        hyp = [t for w in transcribe(model, mp3).split() for t in normalise(w)]
        slips = compare(ref, hyp, align, text)
        run = best = 0
        last = None
        for t, *_ in slips:
            run = run + 1 if last is not None and t - last < 2.5 else 1
            best, last = max(best, run), t
        voice = json.loads(cue_path(args.out, key).read_text()).get("voice", "?") if cue_path(args.out, key).exists() else "?"
        verdict = "ok" if len(slips) <= args.tolerance * len(ref) and best < 3 else "SLIPS"
        print(f"{key}: {len(ref)} words, {len(slips)} slip(s)" + (f", longest run {best}" if slips else "")
              + f" — {verdict} ({voice}, whisper {args.model})")
        for t, tag, said, heard in slips:
            m, s = divmod(t, 60)
            print(f"  {int(m):2d}:{s:05.2f}  {tag:8} {said!r:36} heard {heard!r}")
        bad = bad or verdict != "ok"
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
