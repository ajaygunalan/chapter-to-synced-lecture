---
name: chapter-to-synced-lecture
description: Turn a book or textbook chapter (PDF) into a lecture given by its author — HTML slides plus narrated audio that drives them, with questions the audio stops on, word-synced captions, and a picture that lights whatever the voice names. Use this whenever someone gives you a chapter, paper, or textbook section and asks for a lecture, a podcast, a narrated walkthrough, an animated explainer, a "deep dive," an audio version, or a visual companion — and also when they ask to "turn this into a video/animation," "make this chapter listenable," or "teach me this chapter." Works for any subject — algorithms, software design, mathematics, graphics, economics — because the lecture is built from the chapter's own argument and examples, not a template. Do NOT use for interactive quizzing or active-recall study sessions; those are different skills.
---

# Chapter to synced lecture

The author lectures on his own chapter — his voice, with a picture that
moves where he points — for someone who bought the book and wants to be
taken through this chapter for the first time. `references/teaching.md` is
the contract: the goal, the one rule, five principles. Read it before
anything else.

## The run

```
 1 READ      extract.py ─▶ extract/            read the text; look at the flagged pages
 2 PLAN      plan.md                           your notes, never shown
 3 SLIDES    lecture.src.html ─build_page.py─▶ lecture.html ─▶ screenshots
 4 SCRIPT    script.md ─▶ lint.py ─▶ cold-read review ─▶ fix ─▶ lint.py
 5 DRY RUN   build_audio.py (Kokoro) ─▶ lint.py ─▶ open.py        THE RUN ENDS HERE
 6 RECORD    build_audio.py --engine elevenlabs                   on request, once
```

One shot from PDF to a dry-run lecture opened in the browser. Nothing is
shown for approval on the way; the approval is the listening at the end,
and what happens after it — notes, another dry run, the recording — the
user says. Nothing is reported beyond one sentence if a piece of the
chapter could not be used.

Vocabulary: a **part** is one tab with one audio file; a **frame** is one
slide; a **beat** is one idea in the narration, starting at a frame; a
**mark** names the thing the voice is naming, lit at that word; an **ask**
is a stop — the audio pauses on the question, Play brings the answer.

## Inputs

- **The chapter** (PDF) — required.
- **A note** — optional: what the listener already knows, or what to focus
  on. It steers the lecture; absent, the chapter's own emphasis decides.
- **A voice** — optional; `build_audio.py --check` lists them.

All commands run from the skill directory
(`~/.claude/skills/chapter-to-synced-lecture`).

### 1. Read

```bash
python3 scripts/extract.py <chapter.pdf> --out <outdir>/extract
```

Read `extract/text.txt` in full and `extract/inventory.md`. Anything the
inventory flags is read from the page render, not the text
(`references/extraction.md`: what the text layer loses, and the figure
inventory to keep while reading). Hand-correct `extract/outline.txt`.

Then, for each idea in the chapter, answer what principle 2 asks: the
trouble it exists for, and where the lecture will take that from — the
book first, history where the book's opening has none (search as the need
arises), a staged example as the stage. Note the author's voice
(principle 1).

### 2. Plan

Write `<outdir>/plan.md` — your own notes, as long as they need: what
principles 1–3 need written down (each part's opening trouble and its
source; the chain of failure → rescue in order, with the example that
carries each; where to stop, and which wrong answer is the lesson; the
author's voice); every addition that is the lecture's and not the book's,
with its source; what the chapter has that the lecture skips, and why.
Then build from it.

### 3. Slides

`references/slides.md` decides what each stretch becomes and what a frame
holds; `references/sync-architecture.md` is the page contract.

**Look first.** Load the `frontend-design` skill (Skill tool) and commit
to one look for this chapter before writing markup — one that belongs to
this book, not the previous lecture's. Restyle through the player's tokens
(`sync-architecture.md`, "The page").

Draft each part's frames and beats together — the list of beats, each with
the frame it starts on, is the plan for both — with an id for every thing
the voice will name (`slides.md`, "What a frame is"). Author
`lecture.src.html` as `sync-architecture.md` "The page" says (placeholders:
`build_page.py --help`), then

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
(`references/narration-craft.md`). Lint it:

```bash
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
```

Then the **review** — the only step that can hear the lecture as a
newcomer. Give a fresh agent (`general-purpose`) two reads in this order,
and say why the order matters:

1. **`script.md` alone, cold** — before it has seen the chapter. As a
   listener: where could it not follow, where did it not want the idea
   before the idea arrived, where was there nothing to predict?
2. **Then `references/teaching.md`, `extract/text.txt`, `plan.md`**, and
   the script again: where does it fail the goal or a principle, and where
   does it say something the chapter (or a source the plan cites) does not?

Take the list it returns, whatever is on it; fix each item; lint again.

### 5. Dry run

```bash
python3 scripts/build_audio.py script.md --out <outdir>
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
python3 scripts/open.py lecture.html
```

Each script's `--help` says what it writes. `open.py` prints how long the
run took (from `run.log`) and opens the page. That is the end of the run.
If `build_audio.py --check` fails, `references/kokoro.md` has the setup.

### 6. Record — on request

```bash
python3 scripts/build_audio.py script.md --out <outdir> --engine elevenlabs [--voice <name|id>]
```

Only when the user asks, and only once the words are final: the same
script, the same cues, the paid voice (`references/elevenlabs.md`; with no
key, stop and say so). Marks, asks and slide changes are cues, not speech:
after editing them, `build_audio.py … --recue` re-times the cues from the
existing recording instead of recording again.

## Output

```
<outdir>/                 use <pdf-dir>/lectures/<chapter-slug>/
├── plan.md               your notes
├── lecture.src.html      authored source; lecture.html is built from it
├── script.md             author profile, glossary, outline, narration
├── audio/  cues/         what build_audio.py writes
├── shots/                screenshots from step 3
├── run.log               the run's clock
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
