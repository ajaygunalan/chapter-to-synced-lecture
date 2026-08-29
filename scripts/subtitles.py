"""
Subtitles for a part: sentence-level captions with per-word times, written
into cues/<part>.json as "subs" and shown by player.js as a caption bar and
a scrolling transcript.

time_at() is the one lookup from a character offset (in the text the engine
got) to seconds; beat, mark, ask and subtitle times all come from it.
"""

import difflib
import re
from bisect import bisect_left, bisect_right


SENTENCE_RE = re.compile(r"(?:(?<=[.!?…])|(?<=[.!?…][\"”’)]))\s+(?=[\"“‘(]?[A-Z0-9])")


def sentences_with_offsets(text):
    """[(char offset, sentence)] in order."""
    out, cursor = [], 0
    for s in SENTENCE_RE.split(text.strip()):
        if not s.strip():
            continue
        at = text.find(s, cursor)
        if at < 0:
            at = cursor
        out.append((at, s))
        cursor = at + len(s)
    return out


def words_with_offsets(text):
    """[(char offset, word)] for the text as sent to the engine."""
    return [(m.start(), m.group()) for m in re.finditer(r"\S+", text)]


def align_from_char_starts(text, starts, t0=0.0, off0=0):
    """An engine's per-character start times for `text`, which sits at char off0 of the
    part and t0 seconds into it -> [[offset, t]] per word (what .align.json stores)."""
    out = []
    for off, _ in words_with_offsets(text):
        i = min(off, len(starts) - 1)
        out.append([off0 + off, round(t0 + (starts[i] if starts else 0.0), 3)])
    return out


def time_at(align, offset):
    """Seconds at which the word starting at or before `offset` begins.
    align: [[offset, t], …] sorted by offset (as stored in .align.json)."""
    i = bisect_right(align, [offset, float("inf")]) - 1
    return align[max(i, 0)][1] if align else 0.0


def build_subs(paragraphs, shown, offsets, align, total_end):
    """paragraphs: what the engine got; shown: the same paragraphs in the
    reader's spelling (no respellings, no break tags); offsets: para_offsets;
    align: [[offset, t], …] over SEP.join(paragraphs).
    -> [{"t", "end", "text", "words": [[t, word], …]}]"""
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
        for rel, sent in sentences_with_offsets(para):    # rel: offset within this paragraph
            lo, hi = bisect_left(word_offs, rel), bisect_right(word_offs, rel + len(sent) - 1)
            words = [[time_at(align, offsets[i] + word_offs[n]), labels[n]] for n in range(lo, hi) if labels[n]]
            if words:
                subs.append({"t": words[0][0], "text": " ".join(w for _, w in words), "words": words})
    for a, b in zip(subs, subs[1:]):
        a["end"] = max(a["t"], b["t"])
    if subs:
        subs[-1]["end"] = max(subs[-1]["t"], total_end)
    return subs

