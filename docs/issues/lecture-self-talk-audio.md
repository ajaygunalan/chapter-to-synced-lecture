---
status: open
type: bug
---

# Recorded audio still narrates the slide ("On the board: …")

Found 2026-08-28 after the one-shot runs. The skill now forbids it (`teaching.md` principle 4,
"Not doing"; style-sheet rows) and both page headers were cleaned, but the audio was left as is:
- SOLID v3: `bricks` ("because the chapter mostly doesn't"), `ocp`, `dip` ("… on the board") — ≈8k credits to re-record.
- GA ch13: "On the board" opens ~12 paragraphs across most parts — ≈25–30k credits.

**Done when:** the user decides to re-record (edit script.md, `build_audio.py … --part <key> --force`
per part) or closes this as accepted.
