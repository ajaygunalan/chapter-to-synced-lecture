#!/usr/bin/env python3
"""
Mechanical checks across script.md, lecture.html, and (if built) cues/.
Nothing here judges the teaching; that is the review in SKILL.md step 4.

    lint.py script.md lecture.html [--out DIR] [--headings extract/outline.txt]

- part keys match between `## part:` headings and `data-part` panels
- beat ids are unique; beat start frames increase strictly within a part
- every display block has a spoken form; prose never contains `$` or a
  maths glyph — those are what the glossary exists to replace
- a question block has a prompt and two or more distinct options, each with
  a reply
- the header's outline block maps every section to a real part or `skip`;
  with --headings, every heading in that file appears in the outline
- no two elements in the page share an id (a duplicate SVG marker or
  gradient id makes arrowheads vanish silently)
- with cues: beat ids match the script and the last cue ends within 2 s of
  the audio file's length
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from lecture_format import (COMMENT_RE, MATH_GLYPHS, audio_path, cue_path, duration_of, parse_outline,
                            parse_parts, walk)

GLYPH_RE = re.compile("[$" + MATH_GLYPHS + "]")
PANEL_RE = re.compile(r'<\w+[^>]*\sdata-part="([^"]+)"')   # the attribute on a tag, not a JS selector string
ID_RE = re.compile(r'<\w+[^>]*\sid="([^"]+)"')


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
    page = args.html.read_text()
    panels = set(PANEL_RE.findall(page))
    for k in parts.keys() - panels:
        problems.append(f"part '{k}' has no data-part panel in {args.html.name}")
    for k in panels - parts.keys():
        problems.append(f"panel '{k}' in {args.html.name} has no part in the script")
    for i, n in Counter(ID_RE.findall(page)).items():
        if n > 1:
            problems.append(f"{args.html.name}: id '{i}' appears {n} times — prefix ids with the part key")

    seen = set()
    for k, body in parts.items():
        ids, last_frame, n_q = [], -1, 0
        for beat, items in walk(body):
            if beat:
                if beat["id"] in seen:
                    problems.append(f"duplicate beat id '{beat['id']}'")
                seen.add(beat["id"])
                ids.append(beat["id"])
                if beat["frame"] is not None:
                    if beat["frame"] <= last_frame:
                        problems.append(f"{k}/{beat['id']}: frame {beat['frame']} does not increase "
                                        f"(previous start {last_frame})")
                    last_frame = beat["frame"]
            for item in items:
                if item[0] == "question":
                    q = item[1]
                    letters = [o["letter"] for o in q["options"]]
                    if len(letters) < 2 or len(set(letters)) != len(letters):
                        problems.append(f"{k}/{q['id']}: needs two or more distinct options as 'A. text | reply'")
                    if not q["prompt"]:
                        problems.append(f"{k}/{q['id']}: no prompt text before the options")
                    n_q += 1
                elif item[0] == "display":
                    if item[2] is None:
                        problems.append(f"{k}: display block without spoken form: {item[1].strip()[:50]!r}")
                else:
                    bad = sorted(set(GLYPH_RE.findall(COMMENT_RE.sub("", item[1]))))
                    if bad:
                        problems.append(f"{k}: {' '.join(bad)} in prose — say it in words (glossary) or move it "
                                        f"to a display block: {item[1].strip()[:50]!r}")
        if not ids:
            problems.append(f"part '{k}' has no beats")
        notes.append(f"{k}: {len(ids)} beats, {n_q} question(s)")

        cf = cue_path(out, k)
        if cf.exists():
            cues = json.loads(cf.read_text())
            if [b["id"] for b in cues["beats"]] != ids:
                problems.append(f"{k}: cue beat ids differ from the script — rebuild audio")
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
