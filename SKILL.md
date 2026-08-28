---
name: chapter-to-synced-lecture
description: Turn a book or textbook chapter (PDF) into a lecture given by its author — HTML slides plus narrated audio (ElevenLabs) that drives them, with questions the audio stops on and word-synced captions. Use this whenever someone gives you a chapter, paper, or textbook section and asks for a lecture, a podcast, a narrated walkthrough, an animated explainer, a "deep dive," an audio version, or a visual companion — and also when they ask to "turn this into a video/animation," "make this chapter listenable," or "teach me this chapter." Works for any subject — algorithms, software design, mathematics, graphics, economics — because the lecture is built from the chapter's own argument and examples, not a template. Do NOT use for interactive quizzing or active-recall study sessions; those are different skills.
---

# Chapter to synced lecture

The author lectures on his own chapter: his voice, with slides that change
as he talks. The listener is someone who bought the book, split out the
chapter, and wants to be taken through it for the first time.

`references/teaching.md` is the contract — goal, five principles, and the
strategies under them. Read it before anything else.

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
 │    find the trouble behind each idea: book ─▶ history ─▶ staged example│
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 2  PLAN            plan.md   (your own notes, never shown)              │
 │    opening trouble · failure→rescue chain · where to ask · what to skip │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 3  SLIDES          lecture.src.html ──build_page.py──▶ lecture.html     │
 │    frontend-design ─▶ one look for this book                            │
 │    per part: frames + render()  ─▶ createLecture({parts})               │
 │    equations/figures transcribed from the page images                   │
 │    screenshots ─▶ shots/  ─▶ fix overflow / clipping now                │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 4  SCRIPT          script.md                                            │
 │    the author's voice, first person; beat ↔ frame; asks where it stops  │
 │    lint.py   ─▶ mechanical: parts↔tabs, beat order, spoken forms,       │
 │                 outline coverage, duplicate ids            (a script)   │
 │    REVIEW    ─▶ fresh agent, given teaching.md + chapter + plan + script:│
 │                 "first-time listener: where does this fail the goal or  │
 │                  a principle, or say what the chapter doesn't?"         │
 │              ─▶ fix ─▶ lint again                          (a model)    │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 5  AUDIO — once    build_audio.py ─▶ ElevenLabs (thomas)                │
 │    audio/<part>.mp3                              one file per part      │
 │    word timings ─▶ cues/<part>.json  (beats, asks, subtitles)           │
 │                 ─▶ cues/cues.js      what the page loads                │
 └───────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 6  OPEN            lint.py (now also vs audio lengths) ─▶ xdg-open      │
 └─────────────────────────────────────────────────────────────────────────┘

  IN THE BROWSER (lecture.html) — a slideshow with the author's voice
     audio.currentTime ─▶ cues.js ─▶ which slide ─▶ render(frame)   · slide number on the slide
                                 ├─▶ caption: the sentence, current word lit · Transcript tab
                                 ├─▶ ask: audio stops ─▶ listener thinks ─▶ Play ─▶ the answer
                                 └─▶ ← → slides · Space play/pause · Shift+← → ±10 s · F fullscreen
```

One shot: PDF in, `lecture.html` with audio out, opened in the browser.
Nothing is shown for approval on the way and nothing is reported at the
end beyond one sentence if a piece of the chapter could not be used. Audio
is generated once, at the end; the care goes into the steps before it.

Vocabulary: a **part** is one tab with one audio file; a **frame** is one
slide; a **beat** is one idea in the narration, starting at a frame; an
**ask** is a stop — the audio pauses on the question, Play brings the
answer.

## Inputs

- **The chapter** (PDF) — required.
- **A note** — optional: what the listener already knows, or what to focus
  on. It steers the lecture; absent, the chapter's own emphasis decides.
- **A voice** — optional: a name from the `VOICES` table in
  `scripts/build_audio.py` (default `thomas`).

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

Then find the trouble behind each idea: the book's own applications,
stories, and exercises first; history when the book is silent — search as
the need arises, cite what is found, and when nothing is found say so and
use what the book gives (`teaching.md`, principle 2). Note the author's
voice (`narration-craft.md`, "author profile").

### 2. Plan

Write `<outdir>/plan.md` — your own notes, as long as they need: the
opening trouble and where it comes from; the chain of failure → rescue in
order, with the example that carries each and the medium; where the
lecture stops to ask and which wrong answer is the lesson; what the
listener can do at the end; what the chapter has that the lecture skips,
and why; the author's voice. Then build from it.

### 3. Slides

`references/slides.md` chooses each stretch's treatment;
`references/sync-architecture.md` is the page contract (frames, beats,
asks, player).

**Look first.** Load the `frontend-design` skill (Skill tool) and commit
to one look for this chapter before writing markup — one that belongs to
the book, its era, its subject, its author's temperament, not the previous
lecture's. Typography, palette, texture, and the drawing style follow from
it. What holds it together: the player's tokens (`--bg --panel --ink
--muted --rule --shade --accent --good --bad --mark`) are what you restyle,
so light and dark both work; the transport, seek bar, ask card, and
caption keep their classes; the slide still carries the state
(`teaching.md`, principle 4). Fonts via Google Fonts with real fallbacks;
everything else inline. Distinctive, not decorated. The header is the
book, the chapter, the author — nothing about how the page was made
(`teaching.md`, "Not doing"); each part shows its section and page
numbers.

Draft each part's frames and beats together — they are the beat sheet —
and place asks where a wrong answer teaches. Transcribe from page images
any equation or figure the slide needs. One canvas per frame; code fills
the slide when the voice is on it, coloured by `highlightCode`, staged C++
in the house style, before/after as one frame that changes (`slides.md`,
"Code on slides"). Author `lecture.src.html` with `{{PLAYER_CSS}}`,
`{{PLAYER_JS}}`, `{{IMG:path}}`, one literal `<section data-part="key">`
per part holding a `.slide`, and one `createLecture({parts})` call giving
each part its frames and `render` (`sync-architecture.md`, "The page" —
tabs, hash, fullscreen, audio wiring are its job); maths as `$…$`/`$$…$$`
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
(`references/narration-craft.md`: author profile, glossary, style, script
format). Lint it:

```bash
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
```

Then the **review** — the one step that catches what audio would make
permanent, and the one that judges. Give a fresh agent (`general-purpose`)
`references/teaching.md`, `extract/text.txt`, `plan.md`, `script.md`, and
the slides' frames if it asks, and one question: *you bought this book and
are hearing this lecture for the first time — where does it fail the goal
or one of the five principles, and where does it say something the chapter
(or a source cited in the plan) does not?* Take the list it returns,
whatever is on it; fix each item; lint again. No checklist: what matters
on a design chapter is not what matters on a geometry chapter.

### 5. Audio

```bash
python3 scripts/build_audio.py script.md --out <outdir> [--voice <name|id>]
```

One file per part; asks, subtitles and `cues/cues.js` written alongside. Finished parts are skipped on rerun, so a
quota interruption resumes with the same command; `--force` rebuilds.
Setup, voices, quota: `references/elevenlabs.md`. With no key, stop and
say so.

### 6. Open

```bash
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
xdg-open lecture.html
```

The linter now also matches cue ends against audio lengths. That is the
end of the run.

## Output

```
<outdir>/                 default: <pdf-dir>/lectures/<chapter-slug>/
├── plan.md               your notes
├── lecture.src.html      authored source
├── lecture.html          built; self-contained; works without audio
├── script.md             author profile, glossary, outline, narration, asks
├── audio/                one mp3 per part
├── cues/                 per-part cues + alignment + subtitles; cues.js
├── shots/                screenshots from step 3
└── extract/
```

Rebuilding a chapter that already has a lecture: delete or move the old
output first; never mix two builds' `audio/` and `cues/`.

## Delegating

A subagent running the skill runs all six steps. The caller re-runs
`lint.py` itself before trusting the result — agents get interrupted, and
a clean lint is the evidence.

## When to stop and ask

Only when guessing would make the work useless: no text layer or section
tree; a reference table or bare exercise set with no argument to teach;
equations that cannot be transcribed from page images; a figure the chapter
depends on that is in none of text, images, or page renders. Everything
else is a judgment call — make it.
