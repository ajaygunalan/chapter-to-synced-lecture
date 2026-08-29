# ElevenLabs

The final voice — `build_audio.py --engine elevenlabs`, run once when the words
are final (SKILL.md step 6). What `scripts/engines/elevenlabs.py` assumes
about the API, verified against the docs and a live request on 2026-08-27. Endpoint reference:
https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps

## Setup

1. Account at https://elevenlabs.io. Billing is per character of input
   (`build_audio.py` prints each part's character count and each request's
   cost); https://elevenlabs.io/pricing has the
   current monthly quotas (the free tier has historically not covered one
   chapter and is non-commercial).
2. Key at https://elevenlabs.io/app/settings/api-keys with scopes **Text to
   Speech** (required), **Voices: read** (`--check --list-voices`), **User:
   read** (`--check`). A key missing a scope still synthesises; the script names
   the missing scope instead of failing.
3. Store it where the script looks: `ELEVENLABS_API_KEY` in the environment,
   or — recommended, so every session finds it —
   ```bash
   mkdir -p ~/.config/elevenlabs
   printf '%s' 'KEY' > ~/.config/elevenlabs/api_key && chmod 600 ~/.config/elevenlabs/api_key
   ```
4. `build_audio.py --check --engine elevenlabs` prints tier, balance, and
   each model's live per-request limit; add `--probe` to send one
   25-character request that proves the Text to Speech scope works, and
   `--list-voices` for the account's voices.

Every request authenticates with one header, `xi-api-key`.

## Voices

The lecture voices are the `VOICES` table in `scripts/engines/elevenlabs.py`
(name → id, with `DEFAULT`). `--voice` takes a name from the table or a raw
ElevenLabs id; `ELEVENLABS_VOICE_ID` overrides the default.
`--check --list-voices` prints the account's voices.

To add a voice: audition in the web app, where listening is free —
https://elevenlabs.io/app/voice-library (filter Narrative & Story /
Educational, English) — **Add to My Voices**, then **⋯ → Copy voice ID**
and add a row to `VOICES`. Audition cheaply before committing a chapter:
`--check --probe --voice <name|id>` says one sentence (≈15 credits), or
build one short part with `--part <key>`. Changing voice means regenerating every
part you want in that voice (`--force`), which re-bills them.

## What the script sends and reads

`POST /v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128`
with `text`, `model_id`, `voice_settings`, and for chunked parts
`previous_text` / `next_text` / `previous_request_ids` (request stitching;
the id comes from the `request-id` response header). `seed` is passed when
`--seed` is given, for best-effort reproducibility.

The response carries `audio_base64` and `alignment.character_start_times_seconds`,
indexed by character of the text sent — the cue offsets are computed against
that same text. (`normalized_alignment` indexes the text after number
expansion and is not used.) The `character-cost` header is printed per chunk.

## Models

`eleven_multilingual_v2` is the default: documented as the stable choice for
long-form narration and verified to return alignment. `eleven_flash_v2_5`
is cheaper per character with a larger request limit and lower quality.
`eleven_v3` is the most expressive but its alignment support is unverified —
test one part before committing. Per-request limits are in
`MODEL_LIMITS` in `scripts/engines/elevenlabs.py` (fallback) and live from
`--check`. The rate
per character is whatever the plan charges; the script prints it from the
first response.

Voice settings (`--stability --similarity --style --speed`; defaults in
`--engine elevenlabs --help`): stability 0.4–0.55 is the useful band for a teaching voice —
higher is flatter and more repeatable, lower more expressive; `--style`
(0–0.4) adds emphasis on v2; `--speed` 0.9–1.1.

## Pronunciation

`pronounce:` lines in the script are substituted before synthesis
(narration-craft.md, "Script format"), for every engine. Pronunciation dictionaries
(https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/pronunciation-dictionaries)
are only worth it for a voice reused across many chapters; phoneme rules need
`eleven_flash_v2` or `eleven_v3`.

## Quota

Quotas are monthly and shared across everything you generate — chapters
built in parallel drain one pool (`--check` shows the balance if the key has
User: read). When a build hits `quota_exceeded` the script stops with a
summary of which parts exist; top up at
https://elevenlabs.io/app/subscription and rerun the identical command
(SKILL.md step 6).

## Errors

- `401 missing_permissions` — the key lacks a scope; the message names it.
- `401` otherwise — key missing or wrong.
- `400 max_character_limit_exceeded` — a single paragraph exceeds the model
  limit; split it in the script.
- `422` — a field the API no longer accepts; re-check the endpoint reference.
- `429` — quota or concurrency; the script retries with backoff.
