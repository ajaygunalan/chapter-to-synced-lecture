---
name: chapter-to-synced-lecture
description: Turn a book or textbook chapter (PDF) into a lecture given by its author — HTML slides plus narrated audio that drives them, with questions the audio stops on, word-synced captions, and a picture that lights whatever the voice names. Use this whenever someone gives you a chapter, paper, or textbook section and asks for a lecture, a podcast, a narrated walkthrough, an animated explainer, a "deep dive," an audio version, or a visual companion — and also when they ask to "turn this into a video/animation," "make this chapter listenable," or "teach me this chapter." Use it again on a chapter it has already built — "let's go through that lecture", "I didn't follow the third part", "re-record this bit" — to walk the parts one at a time, explain what confused the listener, then revise the words, the slides and the audio. Works for any subject — algorithms, software design, mathematics, graphics, economics — because the lecture is built from the chapter's own argument and examples, not a template. Do NOT use for interactive quizzing or active-recall study sessions; those are different skills.
---

# Chapter to synced lecture

The author lectures on his own chapter — his voice, with a picture that
moves where he points — for someone who bought the book and wants to be
taken through this chapter for the first time. `references/teaching.md` is
the contract: the goal, the one rule, five principles. Read it before
anything else.

## The run

```
 1 READ     extract.py ─▶ extract/         the text, the figures, the pages to look at
 2 PLAN     plan.md                        the teaching decisions, never shown
 3 SLIDES   lecture.src.html ─▶ lecture.html ─▶ screenshots · page_index.py --text
 4 SCRIPT   script.md ─▶ lint.py ─▶ cold-read review ─▶ fix ─▶ lint.py
 5 RECORD   build_audio.py ─▶ audio/ + cues/ ─▶ lint.py ─▶ open.py
```

One shot from PDF to a lecture opened in the browser, and `open.py` prints
where the time went. Nothing is shown for approval on the way; the approval
is the listening at the end, and what happens after it the user says
("Revising", below).
Nothing is reported beyond one sentence if a piece of the chapter could not
be used.

Each phase is stamped as it finishes (`scripts/stamp.py <outdir> <phase>`);
`extract.py`, `build_audio.py` and `open.py` stamp their own.

Vocabulary: a **part** is one tab with one audio file; a **frame** is one
slide; a **beat** is one idea in the narration, starting at a frame; a
**mark** names the thing the voice is naming, lit at that word; an **ask**
is a stop — the audio pauses on the question, Play brings the answer.

## Build, or pick up where the listening stopped

The PDF is the address of its own lecture: the output always sits at
`<pdf-dir>/lectures/<chapter-slug>/`, so one invocation covers both jobs.

- **No such directory** — build it: the five steps below.
- **It is there** — do not rebuild. Read `run.log` and `script.md`'s header,
  say what exists (the parts, when each was recorded, by which engine), and
  ask which part to work on. Then "Revising", below.

Building again from scratch means deleting that directory first. Nothing else
triggers one, so coming back to a chapter weeks later resumes it instead of
overwriting an hour of work.

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
inventory to keep while reading). Hand-correct `extract/outline.txt`, then
`stamp.py <outdir> read`.

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
Then build from it, and `stamp.py <outdir> plan`.

### 3. Slides

`references/slides.md` decides what each stretch becomes and what a frame
holds; `references/sync-architecture.md` is the page contract.

**Look first.** Load the `frontend-design` skill (Skill tool) and commit
to one look for this chapter before writing markup — one that belongs to
this book, not the previous lecture's. Restyle through the player's tokens
(`sync-architecture.md`, "The page"). `player.css` part 3 already carries the
geometry — `.board` holding a `.fig` beside a `.side`, either one `.wide` to
take the slide alone — so the effort goes into the look, not the plumbing.

Draft each part's frames and beats together — the list of beats, each with
the frame it starts on, is the plan for both — with an id for every thing
the voice will name (`slides.md`, "What a frame is"). Author
`lecture.src.html` as `sync-architecture.md` "The page" says (placeholders:
`build_page.py --help`), then

```bash
python3 scripts/build_page.py lecture.src.html -o lecture.html
```

Screenshot every part's first frame and the frames that matter, and **look
at them** — the URL must be absolute, or the browser photographs its own
error page and every shot comes out the same plausible size:

```bash
for f in <part>:0 <part>:<frame> …; do p=${f%%:*}; n=${f##*:}
  chromium --headless --window-size=1500,1100 --virtual-time-budget=3000 \
    --screenshot="$PWD/shots/$p-$n.png" "file://$PWD/lecture.html#$f" &
done; wait
```

The linter checks consistency, never legibility; this is the only step that
looks. Overflow, clipped labels, collided text, a drawing that does not read
at a glance: fixed now. Then

```bash
python3 scripts/page_index.py lecture.html --text > frames.txt
python3 scripts/stamp.py <outdir> slides
```

`frames.txt` is every frame of every part as text — its label, everything
written on it, and the mark ids it offers. **The script is written from that
file**, so the words describe the run the slides actually computed rather
than a second run in your head, and every mark you write is one that
exists.

### 4. Script, then review

Write `script.md` in the author's voice, from `frames.txt`
(`references/narration-craft.md`). Then, in this order:

```bash
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
python3 scripts/stamp.py <outdir> script
```

**Verify what you asserted** — the two kinds of claim a reader cannot check
for you, and a linter cannot either:

- *what the slides compute* — every number the voice says about a run
  (which edge was taken, what a cell became, what the total is) against
  `frames.txt`. Where the frames come from code, re-run that code and read
  the answer off it; do not re-derive it in your head, which is how the
  voice ends up narrating a different run than the screen draws.
- *what the book says* — every page number, quotation, figure number and
  attribution, by `grep` against `extract/text.txt`.

Then the **review**, the one step that can hear the lecture as a newcomer,
and the only thing here you cannot do yourself: you wrote the script, so
you cannot notice that a term arrived unexplained or that a stretch gave
the listener nothing to predict. Give a fresh agent (`general-purpose`)
**`script.md` and nothing else** — no chapter, no plan, no slides, so the
read stays a listener's read and stays fast — and one question:

> You are hearing this lecture for the first time, having bought the book
> but not read this chapter. Where does it lose you? Name every place you
> could not follow, every term used before it meant anything, every part
> where you did not want the idea before it arrived, every stretch with
> nothing to predict, and every sentence that talks about the picture
> instead of the thing.
>
> Then: anything that contradicts something said earlier, or argues for a
> different rule than the one being taught.

Take the list it returns, whatever is on it; fix each item; lint again;
`stamp.py <outdir> review`.

### 5. Record

```bash
python3 scripts/build_audio.py script.md --out <outdir>
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
python3 scripts/open.py lecture.html
```

Kokoro on the GPU: about a minute for a chapter, free, local, unlimited —
this is how audio is made, every time. `open.py` prints the phase timings
and opens the page. **That is the end of the run: the user listens.**

Afterwards, on their notes: change the words and rerun the same command —
each part is re-recorded only if its words changed, so this costs a few
seconds; change only marks, asks or slides and `build_audio.py … --recue`
re-times the cues from the existing recording without synthesising
anything.

Only when the user explicitly asks for the paid voice, and only once the
words are final:

```bash
python3 scripts/build_audio.py script.md --out <outdir> --engine elevenlabs [--voice <name|id>]
```

Nothing is rebuilt but the audio — same script, same cues, same page — and a
paid recording is never overwritten by a later free one (`build_audio.py
--help`).
Setup and voices: `references/elevenlabs.md`; with no key, stop and say so. If `build_audio.py --check` fails, `references/kokoro.md`.

## Revising

The listening is the review, and it comes back one tab at a time. A part is
self-contained — one stretch of `script.md`, one `audio/<part>.mp3`, one
`cues/<part>.json` — so working on it needs the script's header, that one
part, and that part's frames. Not the whole lecture: ten parts sit
comfortably in ten separate sessions.

**Teach before editing.** When the note is "I didn't follow this", explain it
in the chat and let the listener say when it lands. Only then is it clear
which sentence was at fault. Edit first and you are guessing at what confused
them.

| what changed | command | cost |
|---|---|---|
| a part's words | `build_audio.py script.md --out <outdir>` | that part alone re-records, in seconds |
| only marks, asks or slides | `build_audio.py … --recue` | no synthesis at all |
| only the page | `build_page.py lecture.src.html -o lecture.html` | instant |

Each part is compared against `audio/<part>.txt`, the exact words it was
given, so an unchanged part is never re-recorded and a changed one is never
missed. `lint.py` after every edit.

**Emphasis is written, not asked for.** Kokoro is level by design
(`kokoro.md`) and will not lean on a word because the script wants it to.
Move the word to the front, put it in CAPITALS, end the sentence sooner, or
leave a `<!-- pause 2s -->` in front of it.

Kokoro records every revision. ElevenLabs only when the listener asks for it
by name, and only once the words have stopped moving.

## Output

```
<outdir>/                 use <pdf-dir>/lectures/<chapter-slug>/
├── plan.md               your notes
├── lecture.src.html      authored source; lecture.html is built from it
├── script.md             author profile, glossary, outline, narration
├── audio/  cues/         what build_audio.py writes
├── shots/                screenshots from step 3
├── frames.txt            every frame as text — what the script is written from
├── run.log               one line per phase; open.py prints the timings
└── extract/
```

A lecture that already exists is revised, never rebuilt (above). A true
rebuild means deleting the directory first — two builds must never share an
`audio/` and `cues/`.

## Delegating

A subagent running the skill runs all five steps. The caller re-runs `lint.py`
itself before trusting the result — agents get interrupted, and a clean
lint is the evidence.

## When to stop and ask

Only when guessing would make the work useless: no text layer or section
tree; a reference table or bare exercise set with no argument to teach;
equations that cannot be transcribed from page images; a figure the chapter
depends on that is in none of text, images, or page renders. Everything
else is a judgment call — make it.
