"""
ElevenLabs: the final voice, billed per character — `--engine elevenlabs`,
run once when the words are final. What this module assumes about the API,
setup, voices and quota: references/elevenlabs.md.
"""

import base64
import os
import shutil
import sys
import time
from pathlib import Path

from engines import Fail
from lecture_format import SEP, duration_of, ffmpeg, para_offsets
from subtitles import align_from_char_starts

FINAL = True
VOICES = {                                     # --voice takes a name here or a raw voice id
    "mark": "v3p1kjzUvro6S76qmYmH",
    "thomas": "8sGzMkj2HZn6rYwGx6G0",
}
DEFAULT = "thomas"
VOICE_ENV = "ELEVENLABS_VOICE_ID"
DEFAULT_MODEL = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
MODEL_LIMITS = {"eleven_multilingual_v2": 10000, "eleven_flash_v2_5": 40000, "eleven_v3": 5000}


def add_args(ap):
    g = ap.add_argument_group("elevenlabs")
    g.add_argument("--model", default=DEFAULT_MODEL)
    g.add_argument("--limit", type=int, help="chars per request (default: the model's limit)")
    g.add_argument("--stability", type=float, default=0.45)
    g.add_argument("--similarity", type=float, default=0.75)
    g.add_argument("--style", type=float, default=0.0)
    g.add_argument("--speed", type=float, default=1.0)
    g.add_argument("--seed", type=int)
    g.add_argument("--probe", action="store_true", help="with --check: one 25-character request to prove the text_to_speech scope")
    g.add_argument("--list-voices", action="store_true", help="with --check: the account's voices")


def settings(args):
    return {"stability": args.stability, "similarity_boost": args.similarity,
            "style": args.style, "speed": args.speed, "use_speaker_boost": True}


# ---- the API --------------------------------------------------------------

def find_key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"].strip()
    f = Path.home() / ".config" / "elevenlabs" / "api_key"
    if f.exists():
        return f.read_text().strip()
    raise Fail("No API key: set ELEVENLABS_API_KEY or write it to ~/.config/elevenlabs/api_key "
               "(references/elevenlabs.md).", stop=True)


class Api:
    base = "https://api.elevenlabs.io/v1"

    def __init__(self, key):
        import requests
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
            raise Fail(f"GET {path} -> {r.status_code}: {r.text[:300]}", stop=True)
        return r.json()

    def subscription(self):
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

    def synthesize(self, text, voice, model, voice_settings, seed=None,
                   previous_text=None, next_text=None, previous_ids=()):
        """-> (audio bytes, char start times, request id, character cost)"""
        body = {"text": text, "model_id": model, "voice_settings": voice_settings}
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
            quota = "quota" in r.text
            raise Fail(f"request failed {r.status_code}: {r.text[:400]}"
                       + ("\n  ! quota exhausted — top up, then rerun the same command; finished parts are skipped"
                          if quota else ""), stop=quota)
        data = r.json()
        starts = (data.get("alignment") or {}).get("character_start_times_seconds", [])
        if len(starts) != len(text):
            print(f"    ! alignment has {len(starts)} chars for {len(text)} sent; cues may drift",
                  file=sys.stderr)
        return (base64.b64decode(data["audio_base64"]), starts,
                r.headers.get("request-id"), r.headers.get("character-cost"))


# ---- the contract ------------------------------------------------------------

def check(args):
    api = Api(find_key())
    api.subscription()
    if args.list_voices:
        api.list_voices()
    if args.probe:
        audio, starts, rid, cost = api.synthesize("Testing the lecture pipeline.", args.voice, args.model, settings(args))
        print(f"text_to_speech OK: {len(audio)} bytes, {len(starts)} aligned chars, cost {cost}, request-id {rid}")
    else:
        print("text_to_speech scope: add --probe to verify (one 25-character request)")


def chunk_paragraphs(paragraphs, limit):
    """Greedy pack whole paragraphs -> [(first paragraph index, text)]."""
    chunks, cur, start, cur_len = [], [], 0, 0
    for i, p in enumerate(paragraphs):
        if len(p) > limit:
            raise Fail(f"one paragraph is {len(p)} chars, over the {limit} limit; split it in the script", stop=True)
        if cur and cur_len + len(SEP) + len(p) > limit:
            chunks.append((start, SEP.join(cur)))
            cur, start, cur_len = [], i, 0
        cur.append(p)
        cur_len += len(p) + (len(SEP) if len(cur) > 1 else 0)
    if cur:
        chunks.append((start, SEP.join(cur)))
    return chunks


def synth(paragraphs, args, tmp):
    api = Api(find_key())
    offsets = para_offsets(paragraphs)
    chunks = chunk_paragraphs(paragraphs, args.limit or MODEL_LIMITS.get(args.model, 5000))
    voice_settings = settings(args)
    pieces, ids, t0, align, cost_total = [], [], 0.0, [], 0
    print(f"    {len(chunks)} request(s) to ElevenLabs")
    for i, (first_para, ctext) in enumerate(chunks):
        audio, starts, rid, cost = api.synthesize(
            ctext, args.voice, args.model, voice_settings, args.seed,
            previous_text=chunks[i - 1][1][-600:] if i else None,
            next_text=chunks[i + 1][1][:600] if i + 1 < len(chunks) else None,
            previous_ids=ids)
        cost_total += int(cost or 0)
        piece = tmp / f"{i:02d}.mp3"
        piece.write_bytes(audio)
        pieces.append(piece)
        align += [[offsets[first_para] + off, t] for off, t in align_from_char_starts(ctext, starts, t0)]
        ids = (ids + [rid])[-3:] if rid else ids
        dur = duration_of(piece) or 0.0
        print(f"    chunk {i + 1}/{len(chunks)}: {len(ctext)} chars -> {dur:.1f}s" + (f", cost {cost}" if cost else ""))
        t0 += dur
    mp3 = tmp / "part.mp3"
    if len(pieces) == 1:
        shutil.move(pieces[0], mp3)
    else:
        lst = tmp / "concat.txt"
        lst.write_text("".join(f"file '{p.resolve()}'\n" for p in pieces))
        ffmpeg("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(mp3))
    return mp3, align, t0, cost_total, args.model
