#!/usr/bin/env python3
"""
script.md -> <out>/audio/<part>.mp3 + <out>/cues/<part>.json + <out>/cues/cues.js

One audio file per part, and a cue for every beat, mark and ask, timed from
the engine's per-word alignment (engines: scripts/engines/).

    build_audio.py script.md --out DIR                          # kokoro (default)
    build_audio.py script.md --out DIR --engine elevenlabs
    build_audio.py script.md --out DIR --recue                  # re-time cues from the existing recording; no synthesis
    build_audio.py --check [--engine E]                         # what the engine can do right now
    --voice NAME|ID  --part KEY  --force  ; --engine E --help lists E's own options

Parts that already have audio are skipped, so an interruption resumes with
the same command; --force (or --part) rebuilds. A part recorded by an
engine marked FINAL (a paid voice) is never replaced by another engine's
run unless forced. Script format:
references/narration-craft.md; engines: references/kokoro.md,
references/elevenlabs.md.
"""

import argparse
import functools
import json
import shutil
import sys
import tempfile
from pathlib import Path

import engines
from lecture_format import (SEP, align_path, audio_path, cue_path, cues_js_path, marks_in, para_offsets,
                            parse_parts, parse_pronounce, prose_text, spoken_text, stamp, text_path, walk)
from subtitles import build_subs, time_at, words_with_offsets

print = functools.partial(print, flush=True)   # progress must reach a redirected log as it happens
CHARS_PER_MIN = 930                            # spoken narration, measured


def build_narration(body, rules, warn):
    """-> (paragraphs, shown, beats, marks, asks). beat["para"] is the paragraph
    the beat starts on; a mark is {"id", "frame", "para", "word"}; an ask is
    {"para": the paragraph AFTER the question, "prompt": the question as shown}
    — the audio pauses where that paragraph would start."""
    paragraphs, shown, beats, marks, asks = [], [], [], [], []
    for beat, items in walk(body):
        texts = []
        for item in items:
            kind = item[0]
            if kind == "ask":
                if not texts and not paragraphs:
                    warn("<!-- ask --> with nothing before it; dropped")
                    continue
                prompt = texts[-1][1] if texts else shown[-1]
                asks.append({"para": len(paragraphs) + len(texts), "prompt": prompt})
            elif kind == "display":
                if item[2] is None:
                    warn(f"dropped display block with no spoken form: {item[1].strip()[:50]!r}")
                    continue
                texts.append(spoken_text(item[2], rules))
            else:
                pair = spoken_text(prose_text(item[1]), rules)
                if not pair[0]:
                    continue
                para_index = len(paragraphs) + len(texts)
                for m in marks_in(item[1]):
                    # count the spoken words before the mark, through the paragraph's own transformations
                    prefix = spoken_text(prose_text(item[1][:m["pos"]]), rules)[0]
                    marks.append({"id": m["id"], "frame": m["frame"], "para": para_index,
                                  "word": len(words_with_offsets(prefix))})
                texts.append(pair)
        if beat is not None:
            if not texts:
                warn(f"beat '{beat['id']}' has no narration; dropped")
                continue
            beat["para"] = len(paragraphs)
            beats.append(beat)
        paragraphs.extend(t for t, _ in texts)
        shown.extend(s for _, s in texts)
    return paragraphs, shown, beats, marks, asks


# --------------------------------------------------------------------------
# alignment -> cues
# --------------------------------------------------------------------------

def timed_cues(key, narration, align, total):
    """Everything in cues/<part>.json that depends on the alignment."""
    paragraphs, shown, beats, marks, asks = narration
    offsets = para_offsets(paragraphs)

    def at_para(i):
        return time_at(align, offsets[i]) if i < len(offsets) else total

    starts = [at_para(b["para"]) for b in beats]
    ends = starts[1:] + [total]
    mark_cues = []
    for m in marks:
        words = [off for off, _ in words_with_offsets(paragraphs[m["para"]])]
        t = time_at(align, offsets[m["para"]] + words[m["word"]]) if m["word"] < len(words) else at_para(m["para"] + 1)
        mark_cues.append({"id": m["id"], "frame": m["frame"], "t": round(t, 3)})
    return {
        "beats": [{"id": b["id"], "frame": b["frame"], "t": round(s, 3), "end": round(max(e, s), 3)}
                  for b, s, e in zip(beats, starts, ends)],
        "marks": mark_cues,
        # an ask pauses the main line where the paragraph after the question would start
        "questions": [{"id": f"{key}-ask{n + 1}", "t": round(at_para(a["para"]), 3), "prompt": a["prompt"]}
                      for n, a in enumerate(asks)],
        "subs": build_subs(paragraphs, shown, offsets, align, total),
    }


def write_cues(cf, cues, key, narration, align, duration):
    cues.update(timed_cues(key, narration, align, duration))
    cf.write_text(json.dumps(cues, indent=2))
    return cues


def write_cues_js(out, keys):
    """cues/cues.js: window.LECTURE_CUES = {part: cues}, in script order, for the parts built."""
    cues = {k: json.loads(cue_path(out, k).read_text()) for k in keys if cue_path(out, k).exists()}
    cues_js_path(out).write_text("window.LECTURE_CUES = " + json.dumps(cues) + ";\n")
    return len(cues)


def counts(narration, text):
    _, _, beats, marks, asks = narration
    return f"{len(beats)} beats, {len(marks)} mark(s), {len(asks)} ask(s), {len(text):,} chars"


# --------------------------------------------------------------------------

def main():
    pre = argparse.ArgumentParser(add_help=False)          # --engine first: it decides the other options
    pre.add_argument("--engine", choices=engines.ENGINES, default=engines.DEFAULT)
    engine = engines.load(pre.parse_known_args()[0].engine)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[pre])
    ap.add_argument("script", type=Path, nargs="?")
    ap.add_argument("--out", type=Path, default=Path("."), help="lecture output directory")
    ap.add_argument("--voice", help="a name from the engine's VOICES table, or a raw voice id")
    ap.add_argument("--part", help="only (re)build this one")
    ap.add_argument("--force", action="store_true", help="rebuild parts that already have audio")
    ap.add_argument("--recue", action="store_true",
                    help="rebuild beats, marks, asks and subtitles from the existing alignment; no synthesis. "
                         "Refuses a part whose words changed since it was recorded")
    ap.add_argument("--check", action="store_true", help="what the engine can do right now; no synthesis")
    engine.add_args(ap)
    args = ap.parse_args()
    args.voice = engines.resolve_voice(args, engine)

    if args.check:
        try:
            engine.check(args)
        except engines.Fail as e:
            sys.exit(f"! {e}")
        print(f"voices: {', '.join(engine.VOICES)} (default {engine.DEFAULT}); --voice takes a name or an id")
        return
    if not args.script:
        ap.error("script is required unless --check")

    header, parts = parse_parts(args.script.read_text())
    rules = parse_pronounce(header)
    all_keys = list(parts)
    if args.part:
        if args.part not in parts:
            sys.exit(f"No part '{args.part}'. Found: {', '.join(parts)}")
        parts = {args.part: parts[args.part]}
    rebuild = args.force or bool(args.part)
    (args.out / "audio").mkdir(parents=True, exist_ok=True)
    (args.out / "cues").mkdir(parents=True, exist_ok=True)

    ok, total_chars, problems, spent = True, 0, [], 0
    for key, body in parts.items():
        warn = lambda msg, key=key: problems.append(f"{key}: {msg}")
        narration = build_narration(body, rules, warn)
        paragraphs, beats = narration[0], narration[2]
        text = SEP.join(paragraphs)
        total_chars += len(text)
        cf, af, tf = cue_path(args.out, key), align_path(args.out, key), text_path(args.out, key)
        recorded = audio_path(args.out, key).exists() and cf.exists() and af.exists() and tf.exists()

        if args.recue:
            if not recorded:
                print(f"{key}: not recorded yet; nothing to recue")
                continue
            if text != tf.read_text():
                ok = False
                print(f"  ! {key}: the words changed since it was recorded — re-synthesise it", file=sys.stderr)
                continue
            cues = json.loads(cf.read_text())
            write_cues(cf, cues, key, narration, json.loads(af.read_text())["words"], cues["duration"])
            print(f"{key}: {counts(narration, text)} recued from the {cues['engine']} recording")
            continue

        print(f"{key}: {counts(narration, text)}, ~{len(text) / CHARS_PER_MIN:.1f} min")
        if not beats:
            warn("no beats; skipped")
            ok = False
            continue
        if recorded and not rebuild:
            old = json.loads(cf.read_text()).get("engine", engines.LEGACY)
            if old == args.engine or engines.load(old).FINAL:
                print(f"    already built by {old}; skipping (--force to redo)")
                continue
            print(f"    built by {old}; rebuilding with {args.engine}")

        tmp = Path(tempfile.mkdtemp(prefix=f"tts-{key}-"))
        try:
            mp3, align, duration, cost, model = engine.synth(paragraphs, args, tmp)
            spent += cost
            tf.write_text(text)
            shutil.move(mp3, audio_path(args.out, key))
        except engines.Fail as e:
            print(f"  ! {key}: {e}", file=sys.stderr)
            ok = False
            if e.stop:
                break
            continue
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        af.write_text(json.dumps({"words": align}))
        cues = write_cues(cf, {"part": key, "audio": f"audio/{key}.mp3", "duration": round(duration, 3),
                               "engine": args.engine, "model": model, "voice": args.voice},
                          key, narration, align, duration)
        print(f"  -> audio/{key}.mp3 ({duration:.1f}s), cues/{key}.json, {len(cues['subs'])} subtitle sentences")

    for p in problems:
        print(f"  ! {p}", file=sys.stderr)
    n = write_cues_js(args.out, all_keys)
    missing = [k for k in all_keys if not audio_path(args.out, k).exists()]
    print(f"cues/cues.js: {n} part(s); missing audio: {missing or 'none'}; engine {args.engine}"
          + (f"; spent {spent:,} credits this run" if spent else ""))
    if not args.recue:
        print(f"total: {total_chars:,} chars, ~{total_chars / CHARS_PER_MIN:.0f} min of audio")
    if not args.recue:
        stamp(args.out, "record", f"{n} part(s), {total_chars / CHARS_PER_MIN:.0f} min of audio, {args.engine}"
                                  + (f", {spent:,} credits" if spent else ""))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
