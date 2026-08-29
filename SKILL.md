---
name: chapter-to-synced-lecture
description: Turn a book or textbook chapter (PDF) into a lecture given by its author — HTML slides plus narrated audio that drives them, with questions the audio stops on, word-synced captions, and a picture that lights whatever the voice names. Use this whenever someone gives you a chapter, paper, or textbook section and asks for a lecture, a podcast, a narrated walkthrough, an animated explainer, a "deep dive," an audio version, or a visual companion — and also when they ask to "turn this into a video/animation," "make this chapter listenable," or "teach me this chapter." Works for any subject — algorithms, software design, mathematics, graphics, economics — because the lecture is built from the chapter's own argument and examples, not a template. Do NOT use for interactive quizzing or active-recall study sessions; those are different skills.
---

# Chapter to synced lecture

The author lectures on his own chapter: his voice, with a picture that moves
where he points. The listener is someone who bought the book, split out the
chapter, and wants to be taken through it for the first time.

`references/teaching.md` is the contract — the goal, the one rule, five
principles. Read it before anything else.

## The run

```
  IN:  chapter.pdf   (+ note, + voice)                      OUT:  lecture.html + audio/
        │
        ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 1  READ                                                                 │
 │    extract.py ──▶ extract/text.txt     whole chapter as text (grep-able)│
 │               ──▶ extract/outline.txt  section list, hand-corrected     │
 │               ──▶ extract/images/      the book's figures as files      │
 │               ──▶ extract/inventory.md which pages need a look          │
 │    read the text; look at the flagged pages (figures, maths)            │
 │    for each idea: the problem it answers, the failure before it,       │
 │    what will carry it (book ─▶ history ─▶ staged example)               │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 2  PLAN            plan.md   (your own notes, never shown)              │
 │    how each part opens · failure→rescue chain · where to stop · skips   │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 3  SLIDES          lecture.src.html ──build_page.py──▶ lecture.html     │
 │    frontend-design ─▶ one look for this book                            │
 │    per part: frames + render(frame, mark) ─▶ createLecture({parts})     │
 │    equations/figures transcribed from the page images                   │
 │    screenshots ─▶ shots/  ─▶ fix overflow / clipping now                │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 4  SCRIPT          script.md                                            │
 │    the author's voice, first person; beat ↔ frame; marks on what he    │
 │    names; asks where the listener can predict                           │
 │    lint.py   ─▶ mechanical: parts↔tabs, beat order, marks, spoken forms,│
 │                 outline coverage, duplicate ids               (a script)│
 │    REVIEW    ─▶ fresh agent: script COLD first, then the chapter        │
 │              ─▶ fix ─▶ lint again                            (a model)  │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 5  DRY RUN         build_audio.py ─▶ Kokoro (local, free)               │
 │    audio/<part>.mp3 · cues/<part>.json (beats, marks, asks, subtitles) │
 │    lint.py (now also vs audio lengths) ─▶ xdg-open                      │
 │    THE RUN ENDS HERE. The user listens and gives notes; steps 3–5       │
 │    repeat until the words are final.                                    │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 6  RECORD — on request, once   build_audio.py --engine elevenlabs       │
 └─────────────────────────────────────────────────────────────────────────┘

  IN THE BROWSER (lecture.html) — a blackboard with the author's voice
     audio.currentTime ─▶ cues.js ─▶ frame + mark ─▶ render(frame, mark)  · slide number, ⛶
                                 ├─▶ caption: the sentence, current word lit · transcript below it
                                 ├─▶ ask: audio stops, question in the caption bar ─▶ Play ─▶ answer
                                 └─▶ ← → slides · Space play/pause · Shift+← → ±10 s · F / ⛶ fullscreen
```

One shot from PDF to a dry-run lecture, opened in the browser. Nothing is
shown for approval on the way; the approval is the listening at the end.
Nothing is reported beyond one sentence if a piece of the chapter could not
be used. The final recording is a separate command the user gives when the
words are final; it is never part of the run.

Vocabulary: a **part** is one tab with one audio file; a **frame** is one
slide; a **beat** is one idea in the narration, starting at a frame; a
**mark** is a name in the script for the thing the voice is naming, lit at
that word; an **ask** is a stop — the audio pauses on the question, Play
brings the answer.

## Inputs

- **The chapter** (PDF) — required.
- **A note** — optional: what the listener already knows, or what to focus
  on. It steers the lecture; absent, the chapter's own emphasis decides.
- **A voice** — optional: a name from the engine's `VOICES` table
  (`scripts/engines/<engine>.py`); `build_audio.py --check` lists them.

All commands run from the skill directory
(`~/.claude/skills/chapter-to-synced-lecture`).

### 1. Read

```bash
python3 scripts/extract.py <chapter.pdf> --out <outdir>/extract
```

Read `extract/text.txt` in full and `extract/inventory.md`. Look at the
pages flagged **raster image** or **lossy glyphs**, at **figure caption**
pages when `images/` is empty, and at any page whose maths contradicts its
prose — the text layer drops symbols silently (`references/extraction.md`).
Hand-correct `extract/outline.txt`.

Then, for each idea in the chapter: what problem does it answer, as that
problem shows up in the world; what fails without it; and what will carry it
to the listener — the book's own application, story or exercise first;
history when the book's opening has none (search as the need arises, record
what is found in the plan); a staged example as the stage for either. Note
the author's voice (`narration-craft.md`, "author profile").

### 2. Plan

Write `<outdir>/plan.md` — your own notes, as long as they need: how each
part opens (the problem before the idea) and where that comes from; the
chain of failure → rescue in order, with the example that carries each and
the medium; where the listener can predict, and which wrong answer is the
lesson; what the listener can do at the end; what the chapter has that the
lecture skips, and why; every addition that is the lecture's and not the
book's, with its source; the author's voice. Then build from it.

### 3. Slides

`references/slides.md` chooses each stretch's treatment;
`references/sync-architecture.md` is the page contract (frames, beats,
marks, asks, player).

**Look first.** Load the `frontend-design` skill (Skill tool) and commit
to one look for this chapter before writing markup — one that belongs to
the book, its era, its subject, its author's temperament, not the previous
lecture's. Typography, palette, texture, and the drawing style follow from
it. What holds it together: the player's `:root` tokens (colours and fonts,
`assets/player.css`) are what you restyle, so light and dark both work; the transport, seek bar, caption, and
transcript keep their classes; the slide still carries the state
(`teaching.md`, principle 4). Fonts via Google Fonts with real fallbacks;
everything else inline. Distinctive, not decorated. The header is the
book, the chapter, the author — nothing about how the page was made
(`teaching.md`, "Not doing"); each part shows its section and page
numbers.

Draft each part's frames and beats together — the list of beats, each with
the frame it starts on, is the plan for both — and place stops wherever the
listener can predict. Decide the part's mark vocabulary while drawing
(`slides.md`, "What a frame is, and what a mark does to it"): every edge,
line, cell or bullet the voice will name has an id, and `render(frame,
mark)` lights it. Transcribe from page images any equation or figure the
slide needs; what goes on a frame and how code is shown is `slides.md`.
Author `lecture.src.html` with `{{PLAYER_CSS}}`, `{{PLAYER_JS}}`,
`{{IMG:path}}`, one literal `<section data-part="key">` per part holding a
`.slide`, and one `createLecture({parts})` call giving each part its frames
and `render` (`sync-architecture.md`, "The page"); maths as `$…$`/`$$…$$`
in static markup, `\lt` `\gt` for inequalities; then

```bash
python3 scripts/build_page.py lecture.src.html -o lecture.html
```

Screenshot every part's first frame and the frames that matter
(`chromium --headless --screenshot=shots/<part>-<frame>.png
--window-size=1400,900 lecture.html#<part>:<frame>`) and look at them.
Overflow, clipped labels, a slide that does not read at a glance are fixed
now.

### 4. Script, then review

Write `script.md` in the author's voice, against the frames
(`references/narration-craft.md`: author profile, glossary, the opening of a
part, marks, style, script format). Lint it:

```bash
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
```

Then the **review** — the one step that judges, and the only one that can
hear the lecture as a newcomer. Give a fresh agent (`general-purpose`) two
reads in a fixed order, and say why the order matters:

1. **`script.md` alone, cold** — before it has seen the chapter. It reports
   every place it could not follow; every term met before it was explained;
   every part where it did not want the idea before the idea arrived; every
   stretch where it had nothing to predict; every sentence about the picture
   instead of the thing.
2. **Then `references/teaching.md`, `extract/text.txt`, `plan.md`**, and
   the same script again — for honesty: every number, ordering, quotation
   and claim against the chapter; every addition against the plan's sources;
   anything put in the author's mouth that he did not say.

One question over both reads: *you bought this book and are hearing this
lecture for the first time — where does it fail the goal or a principle,
and where does it say something the chapter (or a source the plan cites)
does not?* Take the list it returns, whatever is on it; fix each item; lint
again. No checklist: what matters on a design chapter is not what matters
on a geometry chapter.

### 5. Dry run

```bash
python3 scripts/build_audio.py script.md --out <outdir>              # Kokoro, local, free
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
xdg-open lecture.html
```

One file per part; beats, marks, asks, subtitles and `cues/cues.js`
written alongside. The linter now also matches cue ends against audio
lengths. That is the end of the run: the user listens and says what
happens next; nothing is re-run or re-recorded without that. Kokoro
setup and voices: `references/kokoro.md`. Engines share one contract
(`scripts/engines/__init__.py`), so `--engine` is the only difference
between a dry run and the recording.

### 6. Record — on request

```bash
python3 scripts/build_audio.py script.md --out <outdir> --engine elevenlabs [--voice <name|id>]
```

Only when the user asks, and only once the words are final: the same
script, the same cues, the paid voice (skip/resume/`--force` rules are in
`build_audio.py --help`; setup, voices, quota: `references/elevenlabs.md`;
with no key, stop and say so). Marks, asks and slide changes are cues, not
speech: after editing them, `build_audio.py script.md --out <outdir>
--recue` re-times the cues from the existing recording — no re-record.

## Output

```
<outdir>/                 default: <pdf-dir>/lectures/<chapter-slug>/
├── plan.md               your notes
├── lecture.src.html      authored source
├── lecture.html          built; self-contained; works without audio
├── script.md             author profile, glossary, outline, narration, marks, asks
├── audio/                one mp3 per part, and the .txt the engine was given
├── cues/                 per-part cues + alignment + subtitles; cues.js
├── shots/                screenshots from step 3
└── extract/
```

Rebuilding a chapter that already has a lecture: delete or move the old
output first; never mix two builds' `audio/` and `cues/`.

## Delegating

A subagent running the skill runs steps 1–5. The caller re-runs `lint.py`
itself before trusting the result — agents get interrupted, and a clean
lint is the evidence.

## When to stop and ask

Only when guessing would make the work useless: no text layer or section
tree; a reference table or bare exercise set with no argument to teach;
equations that cannot be transcribed from page images; a figure the chapter
depends on that is in none of text, images, or page renders. Everything
else is a judgment call — make it.
