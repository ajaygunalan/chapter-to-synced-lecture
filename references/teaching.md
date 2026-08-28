# Teaching

What makes the lecture a lecture and not the book read aloud.

## Goal

Someone has a chapter and wants to understand it before reading it. The
lecture is the author taking them through it — his voice, with slides that
change as he talks. Everything below serves that and nothing else.

Three layers. **Principles** never change. **Strategies** are what usually
follows from them — chosen each time, not obeyed. **Tactics** are decided
per chapter, per moment, from the material; the only numbers in this skill
are real limits of the tools.

## Principles

**1. The author teaches.** First person, lecturing on his own chapter the
way Feynman lectured on his own physics: his argument, his opinions, his
war stories as his, his jokes, his pauses, talking to a student he likes.
Build his profile from the text before writing (`narration-craft.md`,
"Author profile") and speak in that pattern. He says "I" about what is
his; what the lecture stages that he did not write (a small example, a
piece of history) he introduces the way a teacher at a blackboard does:
"let's take a small one", "here's what Borůvka was up against". No
narrator, no attribution notes, no invented biography.

**2. Failure before idea.** Every idea in a textbook was invented because
something failed without it. Put the listener inside that failure first —
try the obvious thing on a real example, watch it break, feel why — and
only then hand over the idea as the way out. The rhythm: get them into
trouble → let them guess the way out → show the way out and why it holds →
say what they can now do → the next trouble. Not boxes; one rhythm applied
as the material wants. Where the trouble comes from, in order: the book's
own applications, war stories, exercises, and other chapters; then history
— the problem the idea was made for and the story around it (Borůvka
electrifying Moravia; Bellman naming dynamic programming to hide
mathematics from a defense secretary), searched for as the need arises and
recorded in the plan; only then a staged example — a tiny graph, a before/after in C++, a
robot pose — as the stage for the real trouble, never as the trouble
itself. Nothing from thin air.

**3. Ask before telling.** Where the listener would guess wrong and learn
from it, stop and ask. The voice asks; the audio stops; the question stays
on the slide; the listener thinks as long as they like; Play brings the
answer — which opens with the trap when the trap is the lesson: "if you
reached for the cheapest edge anywhere, here's why not". A lecture cannot
listen, but an author can anticipate. Where there is no such spot, there
is no question — some parts have several, some none.

**4. The slide carries the state; the voice carries the meaning.** The
picture shows what is — the distance table, the parent array, the inner
product — and changes in view. The voice says why, what to predict, what
contrasts; it talks about the thing, never about the drawing of it. It does
not name the slide, the board, the page, or the screen — not "on the
board, the inner product is minus one" but "take their inner product:
minus one" — because whatever he names lights up as he names it, and
nothing moves that he is not talking about. The formal statement appears
after it has been earned.

**5. Faithful to the chapter.** Every claim traces to the chapter or to a
source recorded in the plan. The lecture may stage examples, code, and
history; it may not add a result, a number, an attribution, or a general
claim the author did not make. Say what is known, never what the chapter
lacks; where the book is wrong, show it corrected on the slide.

## Strategies

- One drawing grows while it is what the voice is talking about — edges
  turn green one by one, a table fills in — instead of a fresh slide per
  sentence. When the material moves to something else, the drawing changes.
- The medium follows the material: a diagram for structure, a before/after
  code pair for design, a moving geometric picture for geometry.
- Staged code in C++, as small as still shows the failure.
- A part ends on a gap: "you can now… — but what if…". The chapter opens
  with its trouble, gives the cast (objects and notation) before the first
  mechanism, and closes by returning to the opening trouble with the tool
  in hand.
- The caption under the slide — the sentence being said, word by word — is
  always there; the full transcript lives behind its own tab so it never
  competes with the slide.
- Audio is generated once per part. Length is whatever the part takes;
  nothing is rewritten or re-recorded to change it.

## Not doing

**The lecture never talks about itself.** Not in the header — no note on
how the drawings were made, what is staged, how the audio is synced, how
many parts there are; the header is the book, the chapter, the author. Not
in the voice — no "in this lecture", "this part", "on the slide", "the
chapter doesn't say"; the sources live in the plan, the voice just says
the thing. The one pointer outward is to the book: page and figure numbers
on each part, because that is where the listener goes next.

Also not: learning-style matching (no evidence); avatars and talking heads;
decorative motion; level-check quizzes before play (the listener bought the
book; the optional note is where they say what they already know).

## Sources

Mayer, *Multimedia Learning* (modality, coherence, signaling, redundancy);
Sweller et al. 2019 (cognitive load, worked examples); Hundhausen, Douglas &
Stasko 2002 and Naps et al. 2002 (engagement, not visuals, predicts learning
from algorithm visualization); Szpunar et al. 2013 (questions between segments
halve mind-wandering); Muller et al. 2008 (misconception first); Chi & Wylie
2014 (ICAP); Willingham (memory is the residue of thought); Sanderson, Azad,
Victor, Case, Lockhart, Gowers, Tao, Winston, Glass, NPR Training, Metz,
Erickson, Dorst and Todd on the craft.
