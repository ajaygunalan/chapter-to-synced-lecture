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
`build_audio.py --list-voices` and `--check` return 401. Either:
- edit the key at https://elevenlabs.io/app/settings/api-keys and add **Voices: read** and
  **User: read** (then `--check` shows the credit balance), or
- keep the key as is and pass a premade voice id with `--voice` (see
  `references/elevenlabs.md`, "Voices without voices_read").

Also worth doing: the key was pasted into a chat session; rotate it at the same page when
convenient.

**Done when:** `--check` prints tier and balance, and one full module has been synthesised.
