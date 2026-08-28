---
status: done
type: feature
---

# Skill: intuitive names, diagram in SKILL.md, principle-driven review (2026-08-28)

- Files: story.md→plan.md, lecture.md→script.md, chapter.*.html→lecture.*.html,
  check_lecture.py→lint.py, extract_chapter.py→extract.py, module-taxonomy.md→slides.md.
- Vocabulary in code and format: module→part (`## part:`, `data-part`, `createLecture({parts})`),
  state→frame (`| frame N`, cues `frame`, player `frames`).
- SKILL.md opens with the ASCII diagram of the run; steps Read · Plan · Slides · Script+review ·
  Audio · Open. The review asks one question against the goal and five principles, no checklist.
- SOLID v3 and GA ch13 outputs migrated, rebuilt, lint 0/0, headless smoke passed.

**v2.0.0 (2026-08-28):** slideshow player — asks instead of option clips, slide number on the slide, arrows step slides, fullscreen, captions always on with a Transcript tab; code on slides in the house C++ style with highlightCode(); one-canvas frames. SOLID and GA lectures rebuilt on it (lint 0/0); SOLID slides still on the split layout, re-authoring pending.
