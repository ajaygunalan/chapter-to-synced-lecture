# ElevenLabs

The paid voice — `build_audio.py --engine elevenlabs` (SKILL.md step 5, the optional final pass).
What `scripts/engines/elevenlabs.py` assumes about the API. Endpoint
reference:
https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps

## Setup

1. Account at https://elevenlabs.io. Billing is per character of input;
   https://elevenlabs.io/pricing has the monthly quotas (the free tier does
   not cover a chapter and is non-commercial).
2. Key at https://elevenlabs.io/app/settings/api-keys with scopes **Text to
   Speech** (required), **Voices: read** and **User: read** (for `--check`).
   A key missing a scope still synthesises; the script names the missing
   scope instead of failing.
3. Store it where the script looks: `ELEVENLABS_API_KEY` in the environment,
   or — recommended, so every session finds it —
   ```bash
   mkdir -p ~/.config/elevenlabs
   printf '%s' 'KEY' > ~/.config/elevenlabs/api_key && chmod 600 ~/.config/elevenlabs/api_key
   ```
4. `build_audio.py --check --engine elevenlabs` prints tier, balance, and
   each model's live per-request limit; add `--probe` to send one short
   request that proves the Text to Speech scope works, and `--list-voices`
   for the account's voices.

## Voices

`VOICES` in `scripts/engines/elevenlabs.py` maps short names to the
account's voice ids; `--voice` takes a name from it or a raw id. To add a
voice: audition in the web app, where listening is free —
https://elevenlabs.io/app/voice-library (filter Narrative & Story /
Educational, English) — **Add to My Voices**, then **⋯ → Copy voice ID**
and add a row. Audition cheaply before committing a chapter:
`--check --probe --voice <name|id>` says one sentence, or build one short
part with `--part <key>`. Changing voice means regenerating every part you
want in that voice (`--force`), which re-bills them.

## Models

`eleven_multilingual_v2` is the default: documented as the stable choice for
long-form narration and verified to return alignment. `eleven_flash_v2_5`
is cheaper per character with a larger request limit and lower quality.
`eleven_v3` is the most expressive but its alignment support is unverified —
test one part before committing. Per-request limits are `MODEL_LIMITS` in
`scripts/engines/elevenlabs.py`; a part over the limit is split at paragraph
boundaries and stitched with `previous_text` / `next_text` /
`previous_request_ids`.

Voice settings (`--stability --similarity --style --speed`; defaults in
`--engine elevenlabs --help`): stability 0.4–0.55 is the useful band for a
teaching voice — higher is flatter and more repeatable, lower more
expressive; `--style` (0–0.4) adds emphasis on v2; `--speed` 0.9–1.1.

## Quota

Quotas are monthly and shared across everything you generate — chapters
built in parallel drain one pool. When a build hits `quota_exceeded` the
script stops with a summary of which parts exist; top up at
https://elevenlabs.io/app/subscription and rerun the identical command
(resume rules: `build_audio.py --help`).

## Errors

- `401 missing_permissions` — the key lacks a scope; the message names it.
- `401` otherwise — key missing or wrong.
- `400 max_character_limit_exceeded` — a single paragraph exceeds the model
  limit; split it in the script.
- `422` — a field the API no longer accepts; re-check the endpoint reference.
- `429` — quota or concurrency; the script retries with backoff.
