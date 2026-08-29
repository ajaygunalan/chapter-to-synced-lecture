#!/usr/bin/env python3
"""
Mechanical checks across script.md, lecture.html, and (if built) cues/.
Nothing here judges the teaching; that is the review in SKILL.md step 4.

    lint.py script.md lecture.html [--out DIR] [--headings extract/outline.txt]

- part keys match between `## part:` headings and `data-part` panels
- beat ids are unique; beat start frames increase strictly within a part
- EVERY REFERENCE THE SCRIPT MAKES RESOLVES against the built page: no frame
  number past the end of that part's deck, and every mark id is something the
  page actually draws on that frame (page_index.py runs the page to find out)
- marks: a mark's frame is at or after its beat's frame and increases within
  the beat; a beat that covers several frames and names none of them by a
  mark is reported (the player would have to guess when to change slide)
- every display block has a spoken form; prose never contains `$` or a
  maths glyph (narration-craft.md, "Display blocks and spoken forms")
- an `<!-- ask -->` follows a prose paragraph, ends its beat, and the answer
  moves to a different frame (narration-craft.md, "Script format")
- the header's outline block maps every section to a real part or `skip`;
  with --headings, every heading in that file appears in the outline
- no two elements share an id on any drawn frame
- with cues: beat ids match the script and the last cue ends within 2 s of
  the audio file's length
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from lecture_format import (COMMENT_RE, MATH_GLYPHS, audio_path, cue_path, duration_of, marks_in,
                            parse_outline, parse_parts, walk)
from page_index import index as page_index

GLYPH_RE = re.compile("[$" + MATH_GLYPHS + "]")
PANEL_RE = re.compile(r'<\w+[^>]*\sdata-part="([^"]+)"')
# spoken pointers into the book: written under the tab, never in the voice (teaching.md, "Not doing")
CITE_RE = re.compile(r"\b(?:pages?|pp?\.)\s*(\d+)|\b(?:Figures?|Chapters?|Sections?)\s+\d", re.I)
CORRECTIONS_RE = re.compile(r"<!--\s*corrections:(.*?)-->", re.S)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("html", type=Path)
    ap.add_argument("--out", type=Path, help="lecture output dir holding audio/ and cues/ (default: script's dir)")
    ap.add_argument("--headings", type=Path, help="one section per line, e.g. extract/outline.txt")
    args = ap.parse_args()
    out = args.out or args.script.parent

    problems, notes = [], []
    header, parts = parse_parts(args.script.read_text())
    # a page the header's corrections block names may be spoken: the listener must be able to check
    corrected = set()
    for block in CORRECTIONS_RE.findall(header):
        corrected.update(re.findall(r"p\.\s*(\d+)", block))
    page = args.html.read_text()
    panels = set(PANEL_RE.findall(page))
    for k in parts.keys() - panels:
        problems.append(f"part '{k}' has no data-part panel in {args.html.name}")
    for k in panels - parts.keys():
        problems.append(f"panel '{k}' in {args.html.name} has no part in the script")
    deck = page_index(args.html)                 # what each part's frames actually offer
    for k, frames in deck.items():               # ids as the browser sees them, per drawn frame
        for i, f in enumerate(frames):
            for dup, n in Counter(f.get("ids", [])).items():
                if n > 1:
                    problems.append(f"{k}/frame {i}: id '{dup}' appears {n} times — prefix ids "
                                    f"with the part key, or an SVG marker or gradient silently "
                                    f"points at the wrong one")
    for k in parts.keys() & deck.keys():
        if not deck[k]:
            problems.append(f"part '{k}' draws no frames")

    def resolve(k, where, frame, mark):
        """Every frame number and mark id the script uses must exist on the page."""
        frames = deck.get(k) or []
        if frame is None or not frames:
            return
        if frame >= len(frames):
            problems.append(f"{k}/{where}: frame {frame}, but the part has {len(frames)} (0–{len(frames) - 1})")
            return
        if mark is None:
            return
        f = frames[frame]
        if mark in f["marks"]:
            return
        m = re.fullmatch(r"line-(\d+)", mark)               # the Nth line of a listing
        if m and int(m.group(1)) <= f["lines"]:
            return
        problems.append(f"{k}/{where}: mark '{mark}' lights nothing on frame {frame}")

    seen = set()
    for k, body in parts.items():
        ids, last_frame, n_q, n_m, prev = [], -1, 0, 0, None
        bid = "?"

        walked = walk(body)
        beat_starts = [b["frame"] for b, _ in walked if b and b["frame"] is not None]
        for beat, items in walked:
            if beat:
                if beat["id"] in seen:
                    problems.append(f"duplicate beat id '{beat['id']}'")
                seen.add(beat["id"])
                ids.append(beat["id"])
                bid = beat["id"]
                if beat["frame"] is not None:
                    if beat["frame"] <= last_frame:
                        problems.append(f"{k}/{beat['id']}: frame {beat['frame']} does not increase "
                                        f"(previous start {last_frame})")
                    last_frame = beat["frame"]
                    resolve(k, beat["id"], last_frame, None)
                asked = False
            mark_frame = last_frame
            frame_marks = 0
            for item in items:
                if item[0] == "ask":
                    if prev != "prose":
                        problems.append(f"{k}: <!-- ask --> must follow the question's prose paragraph")
                    asked = True
                    n_q += 1
                elif item[0] == "display":
                    if item[2] is None:
                        problems.append(f"{k}: this will not be spoken — it reads as a display block, not prose. "
                                    f"Give it a <!-- spoken: … --> form, or reword it to open with a word: "
                                    f"{item[1].strip()[:50]!r}")
                else:
                    if asked:
                        problems.append(f"{k}/{bid}: prose after <!-- ask --> in the same "
                                        f"beat — the answer must start a new beat")
                    for m in marks_in(item[1]):
                        n_m += 1
                        resolve(k, bid, m["frame"] if m["frame"] is not None else mark_frame, m["id"])
                        if m["frame"] is not None:
                            frame_marks += 1
                            if m["frame"] < mark_frame:
                                problems.append(f"{k}/{bid}: mark '{m['id']}' frame "
                                                f"{m['frame']} is before the current frame {mark_frame}")
                            mark_frame = max(mark_frame, m["frame"])
                    spoken = COMMENT_RE.sub("", item[1])
                    cites = list(CITE_RE.finditer(spoken))
                    if any(c.group(1) in corrected for c in cites if c.group(1)):
                        cites = []                      # correcting the book: the page, and its figure, may be said
                    for c in cites:
                        problems.append(f"{k}/{bid}: '{c.group(0)}' spoken — page and figure numbers are written "
                                        f"under the tab, not said (unless correcting the book): {spoken.strip()[:50]!r}")
                    bad = sorted(set(GLYPH_RE.findall(spoken)))
                    if bad:
                        problems.append(f"{k}: {' '.join(bad)} in prose — say it in words (glossary) or move it "
                                        f"to a display block: {item[1].strip()[:50]!r}")
                prev = item[0]
            # a beat covering several frames with no frame-mark: the player would spread them by guessing
            if beat and beat["frame"] is not None:
                nxt = next((f for f in beat_starts if f > beat["frame"]), None)   # starts increase, checked above
                if not frame_marks and nxt is not None and nxt - beat["frame"] > 1:
                    notes.append(f"{k}/{beat['id']}: covers frames {beat['frame']}–{nxt - 1} with no "
                                 f"'| frame' mark; slide changes will be spread evenly (a guess)")
                elif frame_marks and nxt is not None and mark_frame >= nxt:
                    problems.append(f"{k}/{beat['id']}: a mark names frame {mark_frame}, but the next beat "
                                    f"starts at {nxt}")
        held = None
        for i, (beat, items) in enumerate(walked):
            if beat and beat["frame"] is not None:
                held = beat["frame"]
            if not any(it[0] == "ask" for it in items):
                continue
            nxt = next((b for b, _ in walked[i + 1:] if b), None)
            answer = nxt["frame"] if nxt and nxt["frame"] is not None else held
            if answer == held and len(deck.get(k) or []) > 1:
                problems.append(f"{k}/{beat['id'] if beat else '?'}: the answer stays on frame {held}, the slide the "
                                f"question is asked on — the listener is looking at the answer while thinking")

        if not ids:
            problems.append(f"part '{k}' has no beats")
        notes.append(f"{k}: {len(ids)} beats, {n_m} mark(s), {n_q} ask(s)")

        cf = cue_path(out, k)
        if cf.exists():
            cues = json.loads(cf.read_text())
            if [b["id"] for b in cues["beats"]] != ids:
                problems.append(f"{k}: cue beat ids differ from the script — rebuild audio")
            if len(cues.get("marks", [])) != n_m:
                problems.append(f"{k}: cues hold {len(cues.get('marks', []))} marks, the script {n_m} — rebuild audio")
            af = audio_path(out, k)
            dur = duration_of(af) if af.exists() else None
            if dur is not None and abs(dur - cues["beats"][-1]["end"]) > 2.0:
                problems.append(f"{k}: last cue ends at {cues['beats'][-1]['end']:.1f}s, audio is {dur:.1f}s")

    outline = parse_outline(header)
    if not outline:
        problems.append("header has no <!-- outline --> block")
    covered = set()
    for sec, title, target in outline:
        covered.add(sec)
        if not (target.startswith("skip") or target in parts):
            problems.append(f"outline: {sec} {title} -> '{target}' is not a part or skip")
    if args.headings:
        for line in args.headings.read_text().splitlines():
            sec = line.strip().split(" ")[0]
            if line.strip() and not line.startswith("#") and sec not in covered:
                problems.append(f"heading not in outline: {line.strip()!r}")

    for n in notes:
        print(f"  {n}")
    for p in problems:
        print(f"  ! {p}", file=sys.stderr)
    print(f"{len(parts)} parts, {len(seen)} beats, {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
