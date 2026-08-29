---
status: in progress
type: feature
---

# ElevenLabs API key setup

**2026-08-27:** key stored at `~/.config/elevenlabs/api_key` (mode 600). Verified: a
`with-timestamps` request returns 200 with a `request-id` header and per-character alignment
whose last end time matches the MP3 duration — the whole audio pipeline works.

**2026-08-27 later:** quota exhausted (40,000/month; 325 left) after ~40k credits across three chapters. Needs top-up or next cycle. Rate observed: 0.5 credit/char.

**Remaining:** the key was created without the `voices_read` and `user_read` scopes, so
`build_audio.py --check --engine elevenlabs` reports the missing scopes (verified 2026-08-28: `user_read`, `models_read`). Either:
- edit the key at https://elevenlabs.io/app/settings/api-keys and add **Voices: read** and
  **User: read** (then `--check` shows the credit balance), or
- keep the key as is and pass a premade voice id with `--voice` (see
  `references/elevenlabs.md`, "Voices without voices_read").

Also worth doing: the key was pasted into a chat session; rotate it at the same page when
convenient.

**2026-08-28:** ElevenLabs is now the on-request final voice only; every dry run is Kokoro (`references/kokoro.md`), so the quota is spent once per chapter, when the words are final.

**Done when:** `--check --engine elevenlabs` prints tier and balance, and one full module has been synthesised.
