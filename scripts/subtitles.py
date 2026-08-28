"""
Subtitles for a part: sentence-level captions with per-word times, written
into cues/<part>.json as "subs" and shown by player.js as a caption bar and
a scrolling transcript.

Timing comes from cues/<part>.align.json — the per-word start times that
build_audio.py derives from the provider's character alignment. time_at() is
the one lookup from a character offset to seconds; beat cues, question cues,
and subtitles all use it.
"""

import difflib
import json
import re
from bisect import bisect_left, bisect_right

from lecture_format import align_path, cue_path, para_offsets

SENTENCE_RE = re.compile(r"(?:(?<=[.!?…])|(?<=[.!?…][\"”’)]))\s+(?=[\"“‘(]?[A-Z0-9])")


def split_sentences(paragraph):
    return [s for s in SENTENCE_RE.split(paragraph.strip()) if s]


def words_with_offsets(text):
    """[(char offset, word)] for the text as sent to the engine."""
    return [(m.start(), m.group()) for m in re.finditer(r"\S+", text)]


def align_from_char_starts(text, starts, t0=0.0):
    """Provider char start times -> [[offset, t]] per word (what .align.json stores)."""
    out = []
    for off, _ in words_with_offsets(text):
        i = min(off, len(starts) - 1)
        out.append([off, round(t0 + (starts[i] if starts else 0.0), 3)])
    return out


def time_at(align, offset):
    """Seconds at which the word starting at or before `offset` begins.
    align: [[offset, t], …] sorted by offset (as stored in .align.json)."""
    i = bisect_right(align, [offset, float("inf")]) - 1
    return align[max(i, 0)][1] if align else 0.0


def build_subs(paragraphs, shown, align, total_end):
    """paragraphs: what the engine got; shown: the same paragraphs in the
    reader's spelling (no respellings, no break tags); align: [[offset, t], …]
    over SEP.join(paragraphs). -> [{"t", "end", "text", "words": [[t, word], …]}]"""
    offsets = para_offsets(paragraphs)
    subs = []
    for i, para in enumerate(paragraphs):
        spoken = words_with_offsets(para)
        word_offs = [off for off, _ in spoken]
        labels = [w for _, w in spoken]
        if shown[i] != para:
            b = [w for _, w in words_with_offsets(shown[i])]
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, labels, b, autojunk=False).get_opcodes():
                if tag != "equal" and i2 > i1:
                    labels[i1] = " ".join(b[j1:j2])       # whole replacement on the first spoken word
                    for n in range(i1 + 1, i2):
                        labels[n] = ""                    # absorbed (or a break tag: dropped)
        cursor = 0                                        # offset within this paragraph
        for sent in split_sentences(para):
            rel = para.find(sent, cursor)
            if rel < 0:
                rel = cursor
            lo, hi = bisect_left(word_offs, rel), bisect_right(word_offs, rel + len(sent) - 1)
            words = [[time_at(align, offsets[i] + word_offs[n]), labels[n]] for n in range(lo, hi) if labels[n]]
            if words:
                subs.append({"t": words[0][0], "text": " ".join(w for _, w in words), "words": words})
            cursor = rel + len(sent)
    for a, b in zip(subs, subs[1:]):
        a["end"] = max(a["t"], b["t"])
    if subs:
        subs[-1]["end"] = max(subs[-1]["t"], total_end)
    return subs


def attach_subs(out, key, paragraphs, shown):
    """Rebuild "subs" in an existing cues/<part>.json from its .align.json; -> count."""
    cf, af = cue_path(out, key), align_path(out, key)
    if not cf.exists() or not af.exists():
        return 0
    cues = json.loads(cf.read_text())
    align = json.loads(af.read_text())["words"]
    cues["subs"] = build_subs(paragraphs, shown, align, cues["duration"])
    cf.write_text(json.dumps(cues, indent=2))
    return len(cues["subs"])
