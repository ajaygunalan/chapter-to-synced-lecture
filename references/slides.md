# Slides: what each section gets

Read a section, decide what *kind* of thing it is doing, and the slide
treatment follows. Never start from a list of slide types you want to build.
And never let the book's medium decide: a section of prose may want code, a
section of code may want a diagram, a proof may want a toy example. Whatever
carries the idea (`teaching.md`, the one rule).

## Classifying a section

| The section… | Kind | Treatment |
|---|---|---|
| walks through steps that change data | **procedure** | step player over the data structure, frames computed by running it |
| shows a structure being built or modified | **structure** | a diagram that grows frame by frame |
| proves or argues that something must be true | **argument** | progressive build of the claim and its support |
| rewrites an expression line by line | **derivation** | equation lines revealed in order, the changed term marked |
| passes one design through several versions | **design evolution** | one canvas, versions as labelled frames, changed pieces highlighted |
| relates parts of a system | **architecture** | component diagram revealed in dependency order |
| shows two relationships on one diagram (control flow vs source dependency) | **dependency overlay** | same diagram, second arrow system toggled or coloured |
| presents one object in several forms | **representation** | table or figure that morphs between views |
| sets two or more things against each other | **comparison** | table that fills in, or side-by-side builds |
| makes a claim about magnitude, growth, or cost | **quantity** | chart that builds a series at a time |
| constructs something geometrically | **geometric construction** | canvas driven by the actual maths, not hand-placed coordinates |
| improves a piece of code | **transformation** | before/after (or N versions) with highlighted diff |
| shows maths implemented as code | **equation → code** | equation and listing side by side, corresponding parts marked together |
| introduces vocabulary or a formal object | **definition** | the problem it answers first, then a static labelled figure, or an annotated formula when the definition is an equation |
| tells a story about a real problem being solved | **case study** | annotated scene; usually voice-only |
| poses a problem for the reader | **exercise** | an ask: the audio stops on the question, the answer follows |
| drills notation or mechanics (many short items) | **drill set** | skip, or one representative drill as a question |

A section can be two kinds; prefer the one that carries its *argument*. A
proof that also defines terms is an argument. A story whose payoff is a
diagram gaining an edge is design evolution, not a case study. A section that
is genuinely three kinds (a procedure, then a code diff, then an exercise)
is still one part: frames are opaque, so a part may mix a computed run,
authored diff frames, and a question in sequence.

If your classification comes out uniform across a varied chapter, you are
pattern-matching to the subject.

## What a frame is

A frame is one canvas (`.slide`): whatever that moment needs — a diagram,
a listing, both, a table — composed on it and sized to be read from across
a room. No permanent sidebar; no caption of the page's own under the slide
(the words being spoken are already there). Code is a drawing like any
other: when the voice is on the code, the code fills the slide and the
diagram shrinks or leaves. A listing that does not fit at readable size is
split across frames, never shrunk.

`render(frame, mark)` receives the frame and the id of the thing the voice
is naming right now, or `null` (`sync-architecture.md`, "Marks"). Give the
part a small, stable vocabulary of ids — `edge-AB`, `line-27`, `cell-1-4`,
`bullet-3`, `next` (advance the reveal by one) — and decide what lit means
for each kind of thing the page draws. The frames give the state; the marks
give the eye its place in it.

## Code on slides

Before/after is one frame that changes, the way the diagrams already do:
the same listing, the changed lines lit (`.line.hl`), the wrong ones
`.line.bad`, the fix `.line.good`, the rest `.line.dim` when the eye
should skip it — not two blocks the listener has to diff. Colouring comes
from `highlightCode(text, lang)` in `player.js`, and the teaching marks sit
on top of it:

```js
pre.className = 'code';
pre.innerHTML = lines.map(function (l, i) {
  return '<span class="line' + (mark[i] ? ' ' + mark[i] : '') + '">' + highlightCode(l, 'cpp') + '</span>';
}).join('');            // .line is display:block — no newline between them
```

Build the listing once; a mark on a line (`line-27`) toggles `.line.lit` in
`render`, so a listing can sit on screen whole while the voice walks it.

The book's own code stays exactly as the book prints it. Code the lecture
writes is as small as still shows the failure, in the house style of
`code-style.md`.

## Which sections earn a part

Give a stretch of the plan its own part when the slide shows something prose
cannot say compactly (a change over time, a spatial relationship, a shape in
data, a diagram that differs from its previous version), when it is
load-bearing for the chapter's argument, or when the author gave it a
figure, table, listing, or worked example of its own.

Leave a section **voice-only with a static visual** when it is motivational,
discursive, historical, a list of rules with no process behind them, or a
story whose value is the narrative. Animating a story about people usually
produces a worse result than a single good still.

When several sibling subsections annotate the same diagram or formula, build
**one** part spanning them and map each section to it in the outline.

A part gets as many beats as it has distinct ideas — not as many as it has
frames.
