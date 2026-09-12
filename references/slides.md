# Slides: what each section gets

Read a section, decide what *kind* of thing it is doing, and the slide
treatment follows. Never start from a list of slide types you want to build.
And never let the book's medium decide: a section of prose may want code, a
section of code may want a diagram, a proof may want a toy example. Whatever
carries the idea (`teaching.md`, the one rule).

Keep the book's section number and title visible in the tab, not an invented
verb such as "reuse" or "compose". A compact alias may remain the internal
part id. Frame titles can state the current problem or lesson; the part's
pointer line preserves the chapter and subsection identity.

## Classifying a section

| The section… | usually wants |
|---|---|
| explains responsibility, reuse, or a relationship | a conceptual diagram linked to the book's worked example |
| walks through steps that change data | frames computed by running it, not drawn by hand |
| builds or modifies a structure | one drawing that grows, rather than a new one each step |
| argues that something must be true | the claim and its support built up in order |
| rewrites an expression line by line | the lines revealed in order, the changed term marked |
| passes one thing through several versions | one canvas, versions as frames, the difference lit |
| sets things against each other | a table that fills in, or side-by-side builds |
| poses a problem for the reader | an ask: the audio stops on the question |
| drills mechanics (many short items) | skip it, or keep one as a question |

The right column is what usually works, not what to do. A section that wants
a photograph, a joke, or nothing at all on screen should get that instead.

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
other: focus can move from a conceptual diagram to the corresponding code
and worked state while preserving the labels that connect them. Show the
relevant pairing together where readable; use a nearby label or inset when
the fuller view is temporarily absent. Do not permanently squeeze a concept
diagram, full listing, and complete state trace into three dense panes. A
listing that does not fit at readable size is split across frames, never
shrunk.

`render(frame, mark)` receives the frame and the id of the thing the voice
is naming right now, or `null` (`sync-architecture.md`, "Marks"). Give the
part a small, stable vocabulary of ids — `edge-AB`, `line-27`, `cell-1-4`,
`bullet-3`, `next` (advance the reveal by one) — and decide what lit means
for each kind of thing the page draws. The frames give the state; the marks
give the eye its place in it.

## Conceptual diagrams and concrete walkthroughs

Follow the explanation's dependencies (`teaching.md`, "The section's
lesson"), not a diagram-first template. Put the high-level problem and a
plain definition of the central idea where the learner can read them as well
as hear them. Follow the book's style when choosing the opening: a familiar
problem or story, a thought experiment, or a general explanation. Concrete
entities and inputs are welcome when they make the conceptual roles clear;
do not impose an abstract-only opening. Explain the need, proposed solution,
and payoff before dense implementation; a code-free title followed
immediately by a listing does not satisfy this.
Then show the mechanism through relationships, flow, state,
ownership, or responsibilities. Explain what nodes and connections mean
before asking the learner to trace them; an unexplained picture is another
example to decode, not a conceptual explanation.

Once the conceptual solution makes sense, bridge explicitly into the book's
worked implementation. Use its minimal case where possible; add a simplified toy only when
needed to reach the fuller code, graph, or data. Preserve semantic roles when
moving from toy to source example, and explicitly map any changed names. Within each example, the same
names and semantic colors must mean the same things in every view. Move from
the relationship to the step that realizes it and back to the resulting
lesson. Neither an abstract overview alone nor an unexplained execution trace
is sufficient.

For [D2](https://d2lang.com/) diagrams, read the shared `d2-diagram` skill
(`~/.agents/skills/d2-diagram/SKILL.md`, also discoverable from the other
assistant's skill directory). Save actual source and rendered output beside
the lecture as `<outdir>/d2/<concept>.d2` and `<outdir>/d2/<concept>.svg`.
Render the source, inspect the resulting image for readability, and integrate
that rendered asset into the page; handwritten replacement boxes do not
count as using the diagram source. Keep source and rendered files together
when relocating or packaging the lecture.

Give named conceptual elements stable mark targets. Map each target to the
related code line or block and the worked state or graph element. A narrated
claim can then emphasize the concept and its concrete realization together,
without animating unrelated details. Keep transitions at causal or subgoal
boundaries; the listener should be able to pause before the next change.
When using an SVG, preserve or add explicit element-to-mark mappings in the
page instead of lighting the entire image for every distinct claim. Check
these mappings in the rendered page and in the narration cues.

This pairing is a design application of evidence for integrating concrete
and abstract representations, worked examples, and explanatory questions
([IES practice guide](https://ies.ed.gov/ncee/wwc/practiceguide/1)). Stable
signals and synchronized nearby representations apply the contiguity and
signaling principles summarized by
[Mayer and Fiorella](https://doi.org/10.1017/CBO9781139547369.015).
These findings motivate deliberate pairing, not a universally superior
multi-pane layout: omit decorative material and adapt detail to the listener.

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
`render`, so a listing can sit on screen while the voice explains a relevant
step and its connection to the conceptual diagram. Walk the steps that carry
the lesson; do not recite every line by default. Reveal a meaningful block
only after its purpose and unfamiliar notation have been introduced. Keep
the earlier diagram available through stable labels or an inset so each
block has a recognizable job. A full listing is a useful recap after this
walkthrough, not a substitute for it.

Preserve the book's example, names, and algorithmic structure. The house
style (`code-style.md`) keeps supporting code readable; modernization is
useful only when it helps this listener without changing the lesson. Cite
the source listing by page and identify meaningful adaptations. A conceptual
frame need not carry a whole algorithm or `main`. A code-dependent question
must show all the relevant code and input immediately above its A/B/C/D
choices. Code the lecture writes to stage a failure is as small as still
shows it.

Either way it is code on a slide, not code in a file — read at a glance, from
across a room, once. So:

- **readable before compact.** Keep useful grouping, indentation, and braces;
  use whitespace between the phases the voice will name. Split the frame
  before compressing syntax or dropping explanations the learner needs.
- **names short enough to say out loud**, and the same throughout, so "the
  backtrack helper" sends the eye straight to it.
- **comments explain what this learner cannot yet read.** Explain an
  unfamiliar construct's role, a type transformation, an invariant, or its
  connection to the diagram. Omit paraphrases of already-understood syntax;
  do not remove necessary teaching comments merely to shorten the listing.


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

Every section ends with a visible key takeaway and a connection to what
follows. The final summary connects problems, solutions, and costs; it is
not only a vocabulary list. Those lessons should be readable even when the
listener has paused the narration. In review, hide the worked example and
check whether the opening still explains a need, a mechanism, and a useful
change. Then hide the overview and check whether the walkthrough points back
to that claim; neither test is passed by topic labels alone.
