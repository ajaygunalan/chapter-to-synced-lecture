---
status: done
type: feature
---

# Skill: no hard rules, one shot, simplified code (2026-08-27)

- Docs re-founded as goal → 5 principles → strategies → tactics; every numeric cap and "must"
  about teaching removed; vocabulary "slide"/"part".
- Run is one shot (no story gate, no dry run, no report); `frontend-design` loaded for the page
  look; content check by a fresh agent before the single audio pass.
- Code: `lecture_format.walk()` shared by builder and checker; one `time_at()` over the
  alignment table for beats, questions, subtitles; cue JSON written once with subs; no-alignment
  fallback removed; `createLecture()` in player.js owns tabs/hash/audio wiring; checker purely
  mechanical (+ duplicate-id check); `--dry-run`, `MODEL_CREDITS`, George, `no-question` gone;
  `render_math` in-process; requests.Session.
- Bug fixed: subtitle sentence offsets mixed absolute/relative → some sentences timed before
  their predecessor. Captions now mark the current word distinctly.
- Verified: checker 0/0 on SOLID and Skiena, stubbed end-to-end audio build, headless caption
  and createLecture tests.
