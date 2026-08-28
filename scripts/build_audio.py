#!/usr/bin/env python3
"""
script.md -> <out>/audio/<part>.mp3 + <out>/cues/<part>.json + <out>/cues/cues.js

One request per part (chunked under the model's character limit and
stitched), one audio file per part, and a cue per beat whose timestamp comes
from the character alignment ElevenLabs returns; an <!-- ask --> becomes a
stop the player pauses at. Format: references/narration-craft.md; provider: references/elevenlabs.md.

    build_audio.py --check                          key scopes and credit balance
    build_audio.py --probe [--voice NAME|ID]        one 25-char request: proves the TTS scope works
    build_audio.py --list-voices
    build_audio.py script.md --out DIR [--voice NAME|ID] [--part KEY] [--force]
    build_audio.py script.md --out DIR --subtitles   # rebuild captions from existing cues, no API

Parts that already have an mp3 and cues are skipped, so a quota interruption
resumes with the same command; --force (or --part) rebuilds. cues/cues.js is
regenerated from the script's parts on every run.
"""

import argparse
import base64
import functools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

from lecture_format import (COMMENT_RE, PAUSE_RE, SEP, align_path, audio_path, cue_path,
                            duration_of, para_offsets, parse_parts, parse_pronounce, walk)
from subtitles import align_from_char_starts, attach_subs, build_subs, time_at

print = functools.partial(print, flush=True)   # progress must reach a redirected log as it happens
CHARS_PER_MIN = 930                            # measured on multilingual_v2 (919–955)
OUTPUT_FORMAT = "mp3_44100_128"
VOICES = {                                     # the lecture voices, by name; --voice takes a name or an id
    "mark": "v3p1kjzUvro6S76qmYmH",
    "thomas": "8sGzMkj2HZn6rYwGx6G0",
}
DEFAULT_VOICE = "thomas"
MODEL_LIMITS = {"eleven_multilingual_v2": 10000, "eleven_flash_v2_5": 40000, "eleven_v3": 5000}


# --------------------------------------------------------------------------
# script -> paragraphs
# --------------------------------------------------------------------------

def spoken_text(text, rules):
    """Prose or a spoken form -> (what the engine gets, what the reader sees).
    Pauses become <break> tags for the engine and vanish for the reader;
    pronunciation respellings apply to the engine's copy only."""
    shown = " ".join(PAUSE_RE.sub(" ", text).split())
    spoken = PAUSE_RE.sub(lambda p: f' <break time="{min(float(p.group(1)), 3):g}s" /> ', text)
    spoken = " ".join(spoken.split())
    for rx, say in rules:
        spoken = rx.sub(say, spoken)
    return spoken, shown


def prose_text(block):
    s = COMMENT_RE.sub("", block)
    s = re.sub(r"[*_`]+", "", s)                       # markdown emphasis
    return re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)   # links -> text


def build_narration(body, rules, warn):
    """-> (paragraphs, shown, beats, asks). beat["para"] is the paragraph the
    beat starts on; an ask is {"para": the paragraph AFTER the question, "prompt":
    the question as shown} — the audio pauses where that paragraph would start."""
    paragraphs, shown, beats, asks = [], [], [], []
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
                if pair[0]:
                    texts.append(pair)
        if beat is not None:
            if not texts:
                warn(f"beat '{beat['id']}' has no narration; dropped")
                continue
            beat["para"] = len(paragraphs)
            beats.append(beat)
        paragraphs.extend(t for t, _ in texts)
        shown.extend(s for _, s in texts)
    return paragraphs, shown, beats, asks


def chunk_paragraphs(paragraphs, limit):
    """Greedy pack whole paragraphs -> [(first paragraph index, text)]."""
    chunks, cur, start, cur_len = [], [], 0, 0
    for i, p in enumerate(paragraphs):
        if len(p) > limit:
            sys.exit(f"one paragraph is {len(p)} chars, over the {limit} limit; split it in the script")
        if cur and cur_len + len(SEP) + len(p) > limit:
            chunks.append((start, SEP.join(cur)))
            cur, start, cur_len = [], i, 0
        cur.append(p)
        cur_len += len(p) + (len(SEP) if len(cur) > 1 else 0)
    if cur:
        chunks.append((start, SEP.join(cur)))
    return chunks


# --------------------------------------------------------------------------
# ElevenLabs
# --------------------------------------------------------------------------

def find_key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"].strip()
    f = Path.home() / ".config" / "elevenlabs" / "api_key"
    if f.exists():
        return f.read_text().strip()
    sys.exit("No API key: set ELEVENLABS_API_KEY or write it to ~/.config/elevenlabs/api_key "
             "(references/elevenlabs.md).")


class ApiError(Exception):
    def __init__(self, status, detail):
        super().__init__(f"{status}: {detail}")
        self.status, self.detail = status, detail


class ElevenLabs:
    base = "https://api.elevenlabs.io/v1"

    def __init__(self, key):
        self.s = requests.Session()
        self.s.headers.update({"xi-api-key": key})

    def _req(self, method, path, timeout=(10, 30), **kw):
        for attempt in range(4):
            r = self.s.request(method, f"{self.base}{path}", timeout=timeout, **kw)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = 2 ** attempt * 5
                print(f"    {r.status_code}; retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            return r

    def _get(self, path):
        r = self._req("GET", path)
        if r.status_code == 401 and "missing_permissions" in r.text:
            scope = r.json().get("detail", {}).get("message", "").split("permission ")[-1].split()[0]
            print(f"  key lacks the '{scope}' scope for {path}; add it at "
                  f"https://elevenlabs.io/app/settings/api-keys", file=sys.stderr)
            return None
        if r.status_code >= 400:
            sys.exit(f"GET {path} -> {r.status_code}: {r.text[:300]}")
        return r.json()

    def check(self):
        s = self._get("/user/subscription")
        if s:
            used, limit = s.get("character_count", 0), s.get("character_limit", 0)
            reset = s.get("next_character_count_reset_unix")
            when = time.strftime("%Y-%m-%d", time.localtime(reset)) if reset else "?"
            print(f"tier: {s.get('tier')}   characters: {used:,} / {limit:,} used "
                  f"({limit - used:,} left, resets {when})")
        for m in self._get("/models") or []:
            if m.get("can_do_text_to_speech"):
                print(f"  {m['model_id']:<28} max {m.get('maximum_text_length_per_request', '?'):>6} chars/request")

    def list_voices(self):
        for v in (self._get("/voices") or {}).get("voices", []):
            labels = ", ".join(f"{k}={x}" for k, x in (v.get("labels") or {}).items())
            print(f"{v['voice_id']}  {v['name']:<22} {v.get('category', ''):<10} {labels}")

    def synthesize(self, text, voice, model, settings, seed=None,
                   previous_text=None, next_text=None, previous_ids=()):
        """-> (audio bytes, char start times, request id, character cost)"""
        body = {"text": text, "model_id": model, "voice_settings": settings}
        if previous_text:
            body["previous_text"] = previous_text
        if next_text:
            body["next_text"] = next_text
        if previous_ids:
            body["previous_request_ids"] = list(previous_ids)
        if seed is not None:
            body["seed"] = seed
        r = self._req("POST", f"/text-to-speech/{voice}/with-timestamps", timeout=(10, 600),
                      params={"output_format": OUTPUT_FORMAT}, json=body)
        if r.status_code >= 400:
            raise ApiError(r.status_code, r.text[:400])
        data = r.json()
        starts = (data.get("alignment") or {}).get("character_start_times_seconds", [])
        if len(starts) != len(text):
            print(f"    ! alignment has {len(starts)} chars for {len(text)} sent; cues may drift",
                  file=sys.stderr)
        return (base64.b64decode(data["audio_base64"]), starts,
                r.headers.get("request-id"), r.headers.get("character-cost"))


# --------------------------------------------------------------------------
# outputs
# --------------------------------------------------------------------------

def write_cues_js(out, keys):
    """cues/cues.js: window.LECTURE_CUES = {part: cues}, in script order, for the parts built."""
    cues = {k: json.loads(cue_path(out, k).read_text()) for k in keys if cue_path(out, k).exists()}
    (out / "cues" / "cues.js").write_text("window.LECTURE_CUES = " + json.dumps(cues) + ";\n")
    return len(cues)


def concat_mp3(pieces, out):
    if len(pieces) == 1:
        shutil.copyfile(pieces[0], out)
    elif shutil.which("ffmpeg"):
        lst = out.with_suffix(".concat.txt")
        lst.write_text("".join(f"file '{p.resolve()}'\n" for p in pieces))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-c", "copy", str(out)], check=True)
        lst.unlink()
    else:
        out.write_bytes(b"".join(p.read_bytes() for p in pieces))


def beat_cues(beats, offsets, align, total):
    starts = [time_at(align, offsets[b["para"]]) for b in beats]
    ends = starts[1:] + [total]
    return [{"id": b["id"], "frame": b["frame"], "t": round(s, 3), "end": round(max(e, s), 3)}
            for b, s, e in zip(beats, starts, ends)]


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path, nargs="?")
    ap.add_argument("--out", type=Path, default=Path("."), help="lecture output directory")
    ap.add_argument("--voice", default=os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE),
                    help=f"voice name ({', '.join(VOICES)}) or ElevenLabs voice id; default {DEFAULT_VOICE}")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--part", help="only (re)build this one")
    ap.add_argument("--force", action="store_true", help="rebuild parts that already have audio")
    ap.add_argument("--limit", type=int, help="chars per request (default: the model's limit)")
    ap.add_argument("--stability", type=float, default=0.45)
    ap.add_argument("--similarity", type=float, default=0.75)
    ap.add_argument("--style", type=float, default=0.0)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--subtitles", action="store_true",
                    help="only rebuild subtitles for parts that already have cues; no API calls")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--probe", action="store_true", help="send one tiny request to verify the text_to_speech scope")
    ap.add_argument("--list-voices", action="store_true")
    args = ap.parse_args()
    args.voice = VOICES.get(args.voice.lower(), args.voice)
    settings = {"stability": args.stability, "similarity_boost": args.similarity,
                "style": args.style, "speed": args.speed, "use_speaker_boost": True}

    if args.check or args.list_voices or args.probe:
        api = ElevenLabs(find_key())
        if args.check:
            api.check()
            print("text_to_speech scope: run --probe to verify (one 25-character request)")
        if args.list_voices:
            api.list_voices()
        if args.probe:
            audio, starts, rid, cost = api.synthesize("Testing the lecture pipeline.", args.voice, args.model, settings)
            print(f"text_to_speech OK: {len(audio)} bytes, {len(starts)} aligned chars, cost {cost}, request-id {rid}")
        return
    if not args.script:
        ap.error("script is required unless --check/--probe/--list-voices")

    header, parts = parse_parts(args.script.read_text())
    rules = parse_pronounce(header)
    all_keys = list(parts)
    if args.part:
        if args.part not in parts:
            sys.exit(f"No part '{args.part}'. Found: {', '.join(parts)}")
        parts = {args.part: parts[args.part]}
    rebuild = args.force or bool(args.part)

    if args.subtitles:
        for key, body in parts.items():
            paragraphs, shown, _, _ = build_narration(body, rules, lambda m: None)
            print(f"{key}: {attach_subs(args.out, key, paragraphs, shown)} subtitle sentences")
        print(f"cues/cues.js: {write_cues_js(args.out, all_keys)} part(s)")
        return

    api = ElevenLabs(find_key())
    limit = args.limit or MODEL_LIMITS.get(args.model, 5000)
    (args.out / "audio").mkdir(parents=True, exist_ok=True)
    (args.out / "cues").mkdir(parents=True, exist_ok=True)

    ok, total_chars, problems, spent, rate = True, 0, [], 0, None
    for key, body in parts.items():
        warn = lambda msg, key=key: problems.append(f"{key}: {msg}")
        paragraphs, shown, beats, asks = build_narration(body, rules, warn)
        text = SEP.join(paragraphs)
        offsets = para_offsets(paragraphs)
        chunks = chunk_paragraphs(paragraphs, limit)
        total_chars += len(text)
        print(f"{key}: {len(beats)} beats, {len(asks)} ask(s), {len(text):,} chars in {len(chunks)} request(s), "
              f"~{len(text) / CHARS_PER_MIN:.1f} min")
        if not beats:
            warn("no beats; skipped")
            ok = False
            continue
        if audio_path(args.out, key).exists() and cue_path(args.out, key).exists() and not rebuild:
            print("    already built; skipping (--force to redo)")
            continue

        tmp = Path(tempfile.mkdtemp(prefix=f"tts-{key}-"))
        pieces, ids, t0, align = [], [], 0.0, []
        for i, (first_para, ctext) in enumerate(chunks):
            try:
                audio, starts, rid, cost = api.synthesize(
                    ctext, args.voice, args.model, settings, args.seed,
                    previous_text=chunks[i - 1][1][-600:] if i else None,
                    next_text=chunks[i + 1][1][:600] if i + 1 < len(chunks) else None,
                    previous_ids=ids)
            except ApiError as e:
                shutil.rmtree(tmp, ignore_errors=True)
                print(f"  ! {key}: request failed {e}", file=sys.stderr)
                if "quota" in e.detail:
                    print("  ! quota exhausted — top up, then rerun the same command; finished parts are skipped",
                          file=sys.stderr)
                ok = False
                break
            if cost:
                spent += int(cost)
                if rate is None:
                    rate = int(cost) / len(ctext)
                    print(f"    this account is charged {rate:.2f} credits/char on {args.model}")
            piece = tmp / f"{i:02d}.mp3"
            piece.write_bytes(audio)
            pieces.append(piece)
            align += [[offsets[first_para] + off, t] for off, t in align_from_char_starts(ctext, starts, t0)]
            ids = (ids + [rid])[-3:] if rid else ids
            dur = duration_of(piece) or 0.0
            print(f"    chunk {i + 1}/{len(chunks)}: {len(ctext)} chars -> {dur:.1f}s"
                  + (f", cost {cost}" if cost else ""))
            t0 += dur
        if len(pieces) < len(chunks):
            break   # a request failed; stop here so the summary below is accurate
        (args.out / "audio" / f"{key}.txt").write_text(text)   # exactly what the engine got

        concat_mp3(pieces, audio_path(args.out, key))
        shutil.rmtree(tmp, ignore_errors=True)
        # an ask pauses the main line where the paragraph after the question would start
        qcues = [{"id": f"{key}-ask{n + 1}", "t": round(time_at(align, offsets[a["para"]]) if a["para"] < len(offsets) else t0, 3),
                  "prompt": a["prompt"]} for n, a in enumerate(asks)]
        subs = build_subs(paragraphs, shown, align, t0)
        align_path(args.out, key).write_text(json.dumps({"words": align}))
        cue_path(args.out, key).write_text(json.dumps({
            "part": key, "audio": f"audio/{key}.mp3", "duration": round(t0, 3),
            "model": args.model, "voice": args.voice,
            "beats": beat_cues(beats, offsets, align, t0), "questions": qcues, "subs": subs}, indent=2))
        print(f"  -> audio/{key}.mp3 ({t0:.1f}s), cues/{key}.json, {len(subs)} subtitle sentences")

    for p in problems:
        print(f"  ! {p}", file=sys.stderr)
    n = write_cues_js(args.out, all_keys)
    missing = [k for k in all_keys if not audio_path(args.out, k).exists()]
    print(f"cues/cues.js: {n} part(s); missing audio: {missing or 'none'}; spent {spent:,} credits this run"
          f" ({rate:.2f}/char)" if rate else
          f"cues/cues.js: {n} part(s); missing audio: {missing or 'none'}; nothing spent")
    print(f"total: {total_chars:,} chars, ~{total_chars / CHARS_PER_MIN:.0f} min of audio")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
