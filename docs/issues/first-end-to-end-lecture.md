---
status: done
type: feature
---

# First end-to-end lecture with the generalized skill

The skill was rewritten on 2026-08-27 from three test-case analyses (Skiena ch6, Clean Code
ch19, GA ch13) but has never been run end to end. Pick one chapter, run the whole workflow
including the Step 3 plan gate, and record every place the skill's instructions were wrong,
vague, or missing.

**2026-08-27:** user chose to test all three in parallel agents. Each agent runs Steps 1–3 and stops at the plan gate; plans land in `<book>_Chapters/lectures/<slug>/plan.md` and are shown to the user before Step 4. Skill was streamlined the same day (shared `lecture_format.py`, start-state beats, outline block, batched extractor/KaTeX).

**2026-08-27 (later):** user reviewed the three plans and said go on all with defaults — voice George `JBFqnCBsd6RMkjVDRZzb`, `eleven_multilingual_v2`, stability 0.5. Estimated ~125k credits total (33k CC + 36k Skiena + 56k GA); balance unknown (key lacks user_read). Steps 1–3 friction from all three runs already folded into the skill.

**2026-08-27 result:** all three pages + scripts built and pass `check_lecture.py`
(Skiena 13 modules/89 beats, Clean Code 8/81, GA 15/126). Audio: Skiena 13/13 done; Clean
Code 5/8; GA 2/15 — the 40,000-credit monthly quota ran out (shared across the three parallel
builds). Real rate on this account is 0.5 credit/char on multilingual_v2 (not 1.0). Remaining
≈ 35k credits (CC 12.5k chars, GA 57.7k chars). After top-up, rerun the same build command per
chapter — finished modules are skipped. ~30 friction items from Steps 4–8 folded into the skill
(cues.js contract, resume-safe builds, SVG stroke scoping, deep links, step/toggle, etc.).

**Chapters:**
1. Clean Code ch19 (SOLID) — authored reveal steps, raster UML from `images/`, design
   evolution / dependency overlay, author-voice rules. No maths, no generated frames.
2. Skiena ch6 — generated frames, procedure modules; the original example, so mostly a
   regression check of the audio/cue pipeline.
3. GA ch13 — hardest: equation transcription from page renders, `render_math.py`,
   derivation modules, geometric canvas driven by a small GA kernel.

**Done when:** `chapter.html` + `lecture.md` + `audio/` + `cues/` exist for one chapter,
`check_lecture.py` passes, a module plays in sync in a browser, and the findings are folded
back into SKILL.md / references.

Depends on [elevenlabs-api-key-setup](elevenlabs-api-key-setup.md) for the audio half;
everything up to Step 6 can run without it.


**Closed 2026-08-27:** three v1 lectures built; findings folded in; the skill was then re-founded on teaching principles (`references/teaching.md`). Follow-up: [solid-story-v2](solid-story-v2.md).
