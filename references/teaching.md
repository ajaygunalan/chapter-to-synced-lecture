# Teaching

What makes the lecture a lecture and not the book read aloud.

## Goal

Someone has a chapter and wants to understand it before reading it. The
lecture is the author at a blackboard, taking them through it: his voice, and
a picture that moves where he points. When it ends they can say what each
idea is for, connect its mechanism to a worked example, and tell when its
benefit justifies its cost. The lesson should remain useful after they have
forgotten the example's values or code.

## The one rule

**The book anchors the lesson: its argument, section identities, and worked
examples.** Choose code, a diagram, a graph, a story, or a combination to
make that argument understandable. Preserve the book's original examples
and names so the listener can return to the text and recognize them. A
simplified input or supplementary example may clarify a gap, but label the
adaptation and record it in the plan; do not silently replace the chapter's
examples with a new running toy problem. Explicit user choices take priority.

The five principles are ways of doing that well. They are not fences; when a
principle and the rule disagree, the rule wins.

## Principles

**1. The author teaches.** First person, on his own chapter: his argument,
his opinions, his war stories as his, his jokes, talking to a student he
likes. Build his profile from the text before writing (`narration-craft.md`,
"Author profile") and speak in that pattern. He says "I" about what is his.
What the lecture adds and he did not write — a small example, a piece of
code, a piece of history — he introduces the way a teacher at a blackboard
does: "let's take a small one", "here's what they were up against"; every
such addition is listed in the plan with where it came from. He never claims
a memory or an opinion that isn't in the chapter, and no one else's voice
narrates.

Earn additions through a need in the current explanation, not through a
desire to cover related material. Identify supplementary examples or helpers
where they appear and record their origin in the plan; distinguish them from
the book's worked examples without making the lesson about its production.

**2. Establish the need and the idea before dense implementation.** Follow
the book's way of introducing an idea: it may begin with a familiar problem,
a story, a thought experiment, or a general explanation. Make clear what
someone needs to accomplish, what constraint matters, and what capability
is missing. Explain the proposed solution, how it changes the relationship
or process, and why that helps. A familiar concrete example can establish
these roles; it does not have to wait behind a mandatory abstract opening.
A dictionary definition or an execution trace alone does not establish
the need. Preserve the author's teaching style while adding the bridges
this listener needs.

State the problem in plain language before interpreting a diagram or tracing
an example. Define the central idea on screen and in the narration: what
kind of thing it is, what it contains or does, and how that addresses the
problem. A pronunciation glossary or a labeled box is not this definition.
A diagram can make the mechanism visible once its entities and relationships
mean something; it need not be the first frame.

Use the conceptual diagram to explain roles, responsibilities, information
flow, state, or constraints, with links that show meaningful actions or
dependencies. High level means the mechanism is clear without decoding its
implementation. Concrete labels are useful when the listener can also say
which general roles they represent and why the relationship helps. The
listener should understand that before seeing a dense listing. Topic names
joined by arrows are insufficient.

Then bridge explicitly into the book's worked implementation. Map its people, data,
or code to the roles already understood, demonstrate the relevant limitation
or changed requirement, and build the implementation in meaningful steps.
Return from those steps to the original claim. Closely related minor
facilities can be introduced just in time within this chain; they do not
each need a separate opening lesson.

The need can be reusable behavior, clearer responsibilities, composition,
control of state, or avoiding work or storage. An existing solution may be
correct and appropriate. Do not stage a fake failure, require a wrong guess,
or claim a speed advantage to justify an abstraction. Show the conditions
under which its capability earns its cost. Derive this motivation from the
chapter's argument; use supplementary research only to resolve a real gap,
identify additions, and record their source in the plan.

**3. Ask where thinking will help.** Choose pauses where the listener can make a
meaningful choice or form an expectation before the reveal: the lecture
stops until the listener chooses to go on. A question can clarify a
misconception or make the learner justify a choice; it need not produce a
wrong answer. Questions are optional teaching tools, not a required opening
or a quota for every concept or helper. Check both what happens and why this design is
useful: choose an approach under a changed requirement, explain a mechanism,
or identify a cost. Output prediction belongs where it exposes a conceptual
misunderstanding; repeated tracing is not a substitute for a lesson. Present
one question at a time with A/B/C/D, and include the complete relevant code,
diagram, or data immediately above it so the listener need not hunt through
previous frames. Diagnostic evidence governs emphasis; untested is not weak.

**4. The slide shows what is true right now; the voice says what it means.**
The picture holds the current situation — the table so far, the structure so
far, the line of code in question — and the voice says why, what to expect,
what contrasts. The voice never talks about the picture, only about the
thing: not "the green edge is" but "the edge we kept is" — because whatever
he names is lit at the moment he names it, and nothing on the slide moves
that he is not talking about. This is a requirement on the page, not a
hope: every named thing has a mark, every mark has a time
(`sync-architecture.md`, "Marks"). Mark what the listener would otherwise
have to search for — one edge among twelve, one line among forty; what is
already obvious is not marked. A formal derivation can follow the example's
evidence; the plain definitions needed to understand that example come first.

**5. Honest.** What is the book's is presented as the book's; what is the
lecture's is presented as the lecture's; nothing said is false. Where the
book itself is wrong, say so and show the right thing, with the page, so the
listener is misled by neither.

## The section's lesson

Begin with a brief map of the chapter's argument. Use the book's section
number and title as each tab's visible identity; keep technical part ids
internal. If a part spans related subsections, name the parent section and
show the covered subsection numbers on its pointer line.

Each section should make the following chain explicit, in forms suited to
the idea rather than as a repetitive spoken checklist:

1. **Need:** the goal, constraint, or missing capability, introduced in the
   book's style. A familiar example may carry the motivation; make its wider
   relevance explicit before implementation.
2. **Plain definition and conceptual solution:** name the idea, explain what
   changes and how it addresses the need, and show the expected benefit
   through a meaningful relationship diagram before dense implementation.
   Use abstract roles or the source's familiar example as the idea requires.
3. **Smallest concrete bridge, when needed:** isolate that mechanism with
   familiar inputs and only the machinery needed to see it work. Prefer the
   book's own small example; otherwise label the simplification or supplement.
4. **Book's worked evidence:** walk the source example, mapping any toy
   bridge's roles to the book's names and showing what the larger case adds.
   Map the conceptual roles to the example explicitly; keep names consistent
   between each example's diagram, code, and state.
   The toy is a bridge into the book, not a replacement for its argument.
5. **Choice and cost:** when to use it, what changes or stays invariant, and
   what extra storage, indirection, assumptions, or work it requires.
6. **Key takeaway:** a visible, plain-language lesson the listener could
   apply without remembering the listing. Say it in the narration too.
7. **Connection:** what this solution leaves unresolved and why the next
   book section follows. Do not fabricate a dependency when the next section
   explores a related alternative; explain that relationship honestly. A
   pointer to another chapter does not authorize teaching that chapter.

These are dependencies in the explanation, not a fixed allocation of frames.
Combine stages when the book's example is already minimal or the learner has
demonstrated the needed understanding; never skip the conceptual explanation
merely because a worked example or diagram is available.

Close with a chapter synthesis connecting the opening problem, the distinct
solutions, their costs, and the choices they enable. A list of function names
or tab names does not serve as the summary.

## What usually follows

Chosen each time, not obeyed.

- One picture grows while it is what the voice is about, and changes when
  the voice moves on. A fresh slide per sentence is a slideshow, not a
  blackboard.
- The picture is whatever carries the idea; decide per stretch
  (`slides.md`).
- Conceptual diagrams and detailed walkthroughs support each other. Focus
  on the relationship, then the code or worked state that realizes it, then
  return to the takeaway. Show the relevant pairing clearly instead of
  permanently squeezing every view into a dense frame.
- A part ends on the next trouble: "you can now… — but what if…". The whole
  closes by returning to the opening trouble with the tools in hand.
- A part is as long as its ideas take. Nothing is padded or cut to a length.

## Not doing

**The lecture never talks about itself.** Not in the header — no note on how
the drawings were made, what is staged, how the audio is synced; the header
is the book, the chapter, the author. Not in the voice — no "in this
lecture", "this part", "on the slide", "the chapter doesn't say"; the sources
live in the plan, the voice just says the thing. The one pointer outward is
to the book — page and figure numbers — and it is **written** on each part's
pointer line, never spoken: "that's Figure 6.2 on page 194" is a librarian
interrupting a teacher. The single exception is a correction: when the
lecture says the book is wrong, the voice gives the page, so the listener can
check who is right (principle 5).

**The lecture depends on nothing but itself.** It never says "as we saw in
Chapter 1" and moves on: if an idea needs the earlier chapter's example, it
shows that example, right there, in a few sentences — then it may add where
the fuller telling lives. A reference is a pointer the listener may follow
afterwards; it is never a prerequisite they were supposed to bring. The
listener bought the book; they did not necessarily read it in order.

Use learner evidence to choose the bridge into the implementation. Skip
mastered prerequisites, briefly refresh forgotten ones, and teach unknown
ones just before they are needed. If an uncertain prerequisite would change
the explanation, use a tiny check before the dependent topic. Test that
prerequisite alone, using ordinary syntax and complete local context; do not
combine several unfamiliar features into a gotcha. An explicitly forgotten
construct merits a refresher before a check, not a test of whether the learner
remembers having forgotten it. Untested is not weak. The bounded method and
its distinction from a full chapter quiz are in `quizzing.md`.

During an authorized build, put the relevant refresher and optional check in
the lesson; do not start a live quiz or wait for a chat answer unless the
listener requested that interaction. A skipped check leads to the smallest
self-contained bridge needed for the next step, not a claim of mastery.

Stage the implementation around the concept and its current example. Before an
unfamiliar symbol, type helper, or programming pattern does work in a
listing, explain its local purpose and the behavior it enables. Reveal a
meaningful step, connect it to the visual, then build on it. A definition
followed by the complete listing skips this teaching, even if the listing is
correct; the complete version can consolidate steps already understood.

Treat named library facilities as tools serving the concept, not a checklist
to reteach. Refresh an unfamiliar helper at its first necessary use with its
job, the behavior that matters, and any relevant cost or contract. Preserve
the larger lesson while supplying that bridge.

**No numbers as rules.** "In one sentence", "within the first minute" — the
principle is the constraint; the only numbers in the skill are real limits of
the tools.
