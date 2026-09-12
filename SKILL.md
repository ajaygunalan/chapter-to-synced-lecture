---
name: chapter-to-synced-lecture
description: "Turn a chapter PDF, paper, or textbook section into a concept-first lesson with narrated HTML slides, question pauses, word-synced captions, and synchronized conceptual diagrams. Use for requests to teach a chapter, make a lecture, podcast, narrated walkthrough, animated explainer, audio version, or visual companion. Follow the book's section names, argument, and worked examples; explain each problem, solution, tradeoff, durable takeaway, and connection. Also use to discuss, revise, or re-record an existing lecture. Chapter quizzing during a lecture revision is in scope; a standalone quiz with no lecture behind it is not."
---

# Chapter to synced lecture

The author lectures on his own chapter — his voice, with a picture that
moves where he points — for someone who bought the book and wants to be
taken through this chapter for the first time. `references/teaching.md` is
the contract: the goal, the one rule, five principles. Read it before
anything else.

## The run

```
                    ┌─ nothing at <book-dir>/lectures/<slug>/ ──▶ BUILD it
   <chapter.pdf> ───┤
                    └─ it is already there ───────────────────▶ REVISE it

BUILD   1 READ    extract.py ─▶ extract/    the text, the figures, the pages to look at
        2 PLAN    plan.md                   the teaching decisions, never shown
        3 SLIDES  lecture.src.html ─▶ lecture.html ─▶ screenshots · page_index.py --text
        4 SCRIPT  script.md ─▶ lint.py ─▶ cold-read review ─▶ fix ─▶ lint.py
        5 RECORD  build_audio.py ─▶ audio/ + cues/ ─▶ lint.py ─▶ open.py
                  ─▶ the user listens

REVISE    read    the script's header, the one part, that part's frames
          teach   the doubt, in the chat, until the listener says it lands
          edit    script.md for words, lecture.src.html for a slide
          build   only what changed — that part's audio, or --recue, or the page
```

A build is one shot from PDF to a lecture open in the browser, and `open.py`
prints where the time went. Nothing is shown for approval on the way; the
approval is the listening at the end. Nothing is reported beyond one sentence
if a piece of the chapter could not be used.

A listening discussion does not authorize edits by itself. When the listener
explicitly requests changes, revise the requested scope and rebuild what
changed; "revise it", "fix that", or "do that" after concrete feedback is
authorization. There is no required magic word or additional approval round.

Each phase is stamped as it finishes (`scripts/stamp.py <outdir> <phase>`);
`extract.py`, `build_audio.py` and `open.py` stamp their own.

Vocabulary: a **part** is one tab with one audio file; a **frame** is one
slide; a **beat** is one idea in the narration, starting at a frame; a
**mark** names the thing the voice is naming, lit at that word; an **ask**
is a stop — the audio pauses on the question, Play brings the answer.

## Build, or pick up where the listening stopped

### Output location — resolve before creating files

**In the reference vault, use one shared `lectures/` folder per book:**
`<book-dir>/lectures/<chapter-slug>/`. This is `<outdir>` for every build,
recording, check, and revision. Keep the complete lecture bundle there; task
`outputs/` folders may link to it. The chapter PDFs stay in their chapter folders.

When each chapter has its own folder, the book directory is the common parent
of those chapter folders; do not put another `lectures/` inside each chapter.
When chapter PDFs sit directly in the book folder, that folder is already
`<book-dir>`. For a standalone PDF outside a book layout, use its containing
folder. An explicit user-specified location takes precedence.

For example, a PDF at
`functional_programming_in_cpp/03_function_objects/03_function_objects.pdf`
produces `functional_programming_in_cpp/lectures/03-function-objects/lecture.html`.
The other chapters' lectures are siblings of `03-function-objects/` in that same
`lectures/` folder.

Inspect sibling lectures to resolve the layout instead of asking the user to
choose a convention already demonstrated there. Reuse an existing chapter slug,
and check both the book-level folder and legacy per-chapter folders before
concluding that no lecture exists. For an existing lecture in a
legacy per-chapter location, move the complete bundle to the book-level folder
when the user requests organization; preserve its audio, cues, notes, and source,
and update local links. Relocating a bundle is not a rebuild. If a destination
already exists, inspect both bundles before making changes; never overwrite one
blindly.

The resolved output address is used for both building and resuming.

### Build or resume

- **No such directory** — build it: the five steps below.
- **It is there** — do not rebuild, and do not re-read the chapter. Read
  `run.log` and `script.md`'s header, then say in a line that the lecture is
  built and you are ready for questions — the listener has been listening
  and arrives with a doubt, not a menu choice. Never put up a pick-a-part
  prompt: work out which part the question is about from the outline in the
  script's header, read that part, and answer. **Do not touch the lecture**
  — not `script.md`, not `lecture.src.html`, not the audio — merely because
  the listener asked a question. When the request already asks for revision,
  proceed directly to "Revising", below. Re-read the affected book sections
  when restoring source examples, section structure, or factual fidelity.

Reading a part means reading its words and its slides *as text*: that part of
`script.md`, and that part in `frames.txt`. The audio and the page are for
the listener, not for you — `audio/<part>.txt` is the record of what was
actually spoken, and `plan.md` says why the part was shaped that way if the
conversation needs it.

Returning to an existing chapter resumes it; a discussion alone never
triggers a rebuild. An explicit comprehensive revision or rebuild request
authorizes replacing the requested content. Preserve or back up the previous
bundle first, stage the replacement with its matching audio and cues in a
separate directory, and replace the active bundle only after verification.

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

Then, for each idea in the chapter, identify the general need, the capability
it provides, and how that supports the chapter's argument (principle 2).
Locate the book's example that will make it concrete after the conceptual
explanation; supplementary research is for a real explanatory gap, not a
requirement to invent a failure story. Note the author's voice (principle 1).

### 2. Plan

Write `<outdir>/plan.md` — your own notes, as long as they need: what
principles 1–3 need written down (each part's opening need and its source;
the conceptual solution and payoff, followed by the example that makes them
concrete; useful pauses or questions, if any; the author's voice); every
addition that is the lecture's and not the book's,
with its source; what the chapter has that the lecture skips, and why.
Map parts to the book's section numbers and titles. For each section record
the general problem, plain definition, conceptual mechanism and payoff,
source-book worked example, useful conditions and costs, and takeaway. The
opening follows the book's teaching style: use its familiar problem, story,
thought experiment, or general explanation to establish the need and
solution before dense implementation. Do not impose a universal ban on
concrete examples or require every concept to start abstractly. Record why
the opening fits the source and how its conceptual roles map into the
book's example; use the book's minimal case or
a labeled toy bridge where needed. Define central terms in visible text and
narration before tracing code or interpreting unfamiliar diagram labels.
Start with the chapter's argument and finish with a synthesis of its lessons.

Use learner evidence to plan prerequisite bridges before dense notation:
skip demonstrated skills, refresh forgotten ones, and use a tiny isolated
check before a dependent topic when uncertainty matters. Untested is not
weak; known algorithms do not need another full walkthrough just because
they appear in the chapter. Refresh supporting facilities at their first
necessary use. `references/quizzing.md`, "Brief prerequisite checks", distinguishes
these from a full quiz; an authorized build does not wait for unsolicited
live assessment. Plan the explanation before choosing its visual treatment
(`references/teaching.md`); a problem diagram followed by a completed listing
does not establish the bridge. Stage meaningful implementation steps and
connect each to its already-explained conceptual role.
Then build from it, and `stamp.py <outdir> plan`.

### 3. Slides

`references/slides.md` decides what each stretch becomes and what a frame
holds, including conceptual diagrams with source and rendered assets in
`<outdir>/d2/`; `references/code-style.md` is how supporting code looks on a
slide; `references/sync-architecture.md` is the
page contract.

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
you can miss that a term arrived unexplained or that a stretch never
established why its concept matters. Give a fresh agent (`general-purpose`)
**`script.md` first** — no chapter, plan, or slides, so the initial read stays
a listener's read — with this prompt:

> You are hearing this lecture for the first time, having bought the book
> but not read this chapter. Where does it lose you? Name every place you
> could not follow, every term used before it meant anything, every part
> where you did not want the idea before it arrived, every stretch with
> nothing meaningful to decide or explain, and every sentence that talks about the picture
> instead of the thing.
> For each major concept, identify where the general need, conceptual
> solution, and payoff are explained before any worked example. Flag an
> opening that starts with code, example entities, an execution trace, or
> only a definition. Do not request a forced failure or a wrong prediction.
> Locate abrupt jumps from an intuitive explanation to a completed
> implementation. Flag unfamiliar symbols, type helpers, or patterns that
> pile up before their roles are explained. Name the missing bridge; do not
> prescribe a quiz for every new item or reteach a skill the script establishes.
> For each central term, locate its plain definition before its first worked
> use. Can you say what kind of thing it is and what problem it solves without
> inferring that from code? Check that the first worked case exposes the
> mechanism before extra detail, and that any changed names are mapped. The
> book's own minimal example can serve directly; do not require an added toy.
> Flag a toy that silently requires the very prerequisite being refreshed,
> or a diagnostic that combines unfamiliar features before they are taught.
>
> For each part, state the lesson you could still use after forgetting its
> example: what problem it solves, how it works, when its cost is justified,
> and why the next part follows. Flag any part that only teaches tracing
> code, any missing transition, and a final summary that fails to connect
> the chapter's lessons.
>
> Then: anything that contradicts something said earlier, or argues for a
> different rule than the one being taught.

Then give the same reviewer `frames.txt` and the relevant rendered frames,
still without the plan. Ask whether the general need, conceptual solution,
and payoff are readable and explained before any example or code; whether
the central definition is visible as well as spoken; whether diagram entities
and relationships have meaning before they are traced; and whether any toy
bridge and source example visibly realize the same mechanism. Check needed syntax
before its first dependent block and prerequisite checks before the dependent
topic. Flag abstract labels mistaken for definitions, an unexplained opening
picture, or a toy-to-full-listing jump even when each frame is correct alone.

Take the list it returns, whatever is on it; fix each item; lint again;
`stamp.py <outdir> review`.

### 5. Record

```bash
python3 scripts/build_audio.py script.md --out <outdir>
python3 scripts/lint.py script.md lecture.html --out <outdir> --headings extract/outline.txt
python3 scripts/open.py lecture.html
```

Chatterbox on the GPU (`references/chatterbox.md`): Resemble's open 500M
model, free, local, unlimited, the most natural of the local voices —
about half an hour for a chapter — this is how audio is made, every time.
TADA (`--engine tada`, `references/tada.md`) is the alternative narrator: a
quarter of an hour a chapter. Kokoro (`--engine kokoro`,
`references/kokoro.md`) is the small fast fallback: a minute a chapter,
flat. `open.py` prints the phase timings and opens the page. **That is the
end of the run: the user listens.**

What comes back from that listening is "Revising", below.

Only when the user explicitly asks for the paid voice, and only once the
words are final:

```bash
python3 scripts/build_audio.py script.md --out <outdir> --engine elevenlabs [--voice <name|id>]
```

Nothing is rebuilt but the audio — same script, same cues, same page — and a
paid recording is never overwritten by a later free one (`build_audio.py
--help`).
Setup and voices: `references/elevenlabs.md`; with no key, stop and say so. If `build_audio.py --check` fails, `references/chatterbox.md`.

## Revising

Nothing is regenerated unless the conversation changed it.

The listening is the review, and it comes back one tab at a time. A part is
self-contained — one stretch of `script.md`, one `audio/<part>.mp3`, one
`cues/<part>.json` — so working on it needs the script's header, that one
part, and that part's frames. Not the whole lecture: ten parts sit
comfortably in ten separate sessions.

**Distinguish discussion from a request to revise.**
The listener goes through the lecture tab by tab and brings each doubt to
the chat. Teach it there — explain, let them say when it lands, work out
together which sentence was at fault. While that runs, nothing in the
lecture directory changes: not a word of `script.md`, not a slide, not a
second of audio. Keep the running list of what should change in
`<outdir>/notes.md` — the doubt, what landed, the sentence or slide to fix —
so nothing is lost across a long session or a summarised context.
An explicit instruction to revise, rebuild, fix, or implement the feedback
ends that discussion boundary for the requested changes; "do that" is enough
when its scope is clear. Complete the authorized changes without asking the
listener to repeat permission or say the literal word "edit".

**Quizzing.** When the listener asks to be quizzed, `references/quizzing.md`
is the method: a concept checklist drawn from the chapter, one
decision-framed question per message in plain chat, each carrying its own
diagram or data, adapted from every answer — escalate, decompose, re-queue,
retire. The quiz is not a grade; its misses join `notes.md` as the work
list, so the next revision of the lecture fixes what the listener actually
got wrong. Concepts the listener has already demonstrated in conversation
are retired unasked. The
edits happen only when the listener explicitly says to make them, normally
at the very end of the session, and only within the scope they approved.
Unrequested mid-discussion changes risk re-recording a part they are still
listening to; an explicit request to make changes now authorizes that work.

Stay within the requested explanation or chapter. A closing pointer to a
related section or the next chapter is a connection, not an instruction to
start teaching or building that additional topic.

| what changed | command | cost |
|---|---|---|
| a part's words | `build_audio.py script.md --out <outdir>` | that part alone re-records, a minute or two |
| a part sounds wrong somewhere | `verify_timing.py <outdir> <part>` | no synthesis; names the words the voice slipped on — one is noise, a run is the place; then `--part <key>` |
| only marks, asks or slides | `build_audio.py … --recue` | no synthesis at all |
| only the page | `build_page.py lecture.src.html -o lecture.html` | instant |

Each part is compared against `audio/<part>.txt`, the exact words it was
given, so an unchanged part is never re-recorded and a changed one is never
missed. `lint.py` after every edit.

**Emphasis is written, not asked for.** Chatterbox and TADA read the
sentence and lean where a reader would; Kokoro is level by design
(`kokoro.md`). No engine follows a stage direction on one word (Chatterbox's
knobs set the whole run). Move the word to the front, put it in CAPITALS,
end the sentence sooner, or leave a `<!-- pause 2s -->` in front of it.

Chatterbox records every revision. ElevenLabs only when the listener asks
for it by name, and only once the words have stopped moving.

## Output

```
<outdir>/                 use <book-dir>/lectures/<chapter-slug>/
├── plan.md               your notes
├── lecture.src.html      authored source; lecture.html is built from it
├── script.md             author profile, glossary, outline, narration
├── audio/  cues/         what build_audio.py writes
├── d2/                   conceptual .d2 sources and rendered .svg assets
├── shots/                screenshots from step 3
├── frames.txt            every frame as text — what the script is written from
├── run.log               one line per phase; open.py prints the timings
└── extract/
```

Revise an existing lecture in the authorized scope. For a comprehensive
revision or rebuild, preserve or back up the previous bundle and stage the
replacement separately: each version needs its own matching `audio/` and
`cues/`. Verify the replacement before switching the active bundle; do not
delete prior work merely to start a rebuild.

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
