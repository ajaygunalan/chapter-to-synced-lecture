# Narration craft

How to write a script the author's voice can deliver as a lecture. The
teaching decisions are in `teaching.md`; this is the writing.

## Before a word: the author profile and the glossary

Write both into `script.md`'s header.

**Author profile** — from reading the chapter: how he positions himself
(practitioner telling stories; co-builder, "let's build it"; authority), how
he motivates (a war story, a bug, history, "here's why you'd care"), how often
he steps aside and in what tone, his humour, signature phrases to reuse
sparingly, how he closes a section. Reproduce the pattern, not the sentences.

**Glossary** — a row per symbol, operator, identifier, acronym, and
typographic distinction, with its single spoken form; decided once.

```markdown
<!-- author: first-person practitioner; motivates with a real job gone wrong;
     wry, self-deprecating asides; closes with a boxed lesson -->
<!-- glossary
θ            theta
≤            at most
x̄ vs x       the mean of x / a single x
API          the letters, A-P-I — never said as a word
getUserName()   the get-user-name method
example.org/docs   example dot org, slash docs
-->
```

Acronyms: word (NASA) or letters (H-T-M-L); anything the engine could read as
an English word gets expanded. Identifiers are screen-only; the voice says
"the get-user-name method". Typography that carries meaning is said aloud.
Diagram legend once, then plain verbs. Every name the engine would
mispronounce gets a `pronounce:` entry in the header block.

## Writing for the ear

- One idea per sentence; front-load the point; contractions; "you" and "we".
- Name things before using them — a listener cannot glance up at a label.
- Signpost what the eye gets from layout: "three things to hold", "here's
  the part worth slowing down on", "that was the mechanical bit".
- Say the key idea until it lands — formally, as a picture, as a rule of
  thumb — in whatever forms the moment wants.
- Keep something happening: each paragraph follows the last by consequence
  or contrast ("so", "but"), never by mere sequence ("and then").
- Emphasis with words and CAPITALS, not markup. Pauses with full stops,
  paragraph breaks, "…", and a `pause` where the listener needs a moment to
  think.
- Whatever the voice names, mark it (`mark`, below) — an edge, a line, a
  cell, a bullet — so it lights as it is said.

## Connect the concept to the worked example

Start each major concept in the book's teaching style: a familiar problem,
story, thought experiment, or general explanation. Establish the need in
plain language, then the conceptual solution, mechanism, and payoff before
dense implementation. A concrete example can carry that explanation when
its roles are clear; there is no universal abstract-only opening. Define
the central idea plainly in the narration, matching its visible definition,
before expecting the listener to interpret diagram labels. Connect the
roles and relationships in that diagram through causal language.
A definition alone does not explain why someone would want the capability.

Then demonstrate the mechanism with the smallest toy the listener can follow.
If the book's own example is already minimal, it can serve this role;
otherwise use a labeled simplified or supplementary case before its fuller
worked example. Say how the toy's roles map into the book's names and what
the larger case adds. Keep names consistent within each example's code,
diagram, and worked state. When a step matters, walk through it and connect
the result back to the larger claim. Narration should explain the purpose
and consequence of a line, graph change, or state update, not merely pronounce
the syntax.

Bridge to each implementation step at the listener's level. Use existing
evidence to skip, refresh, or explain a prerequisite; if needed, a tiny
isolated check belongs before the dependent topic (`quizzing.md`, "Brief
prerequisite checks"). It should inform the explanation rather than become
a multi-feature gotcha or an unsolicited live quiz during a build.
Explain an unfamiliar symbol, type helper, or pattern by the job it does
here before asking the listener to follow it in code. A spoken name in the
glossary is pronunciation support, not an explanation. Do not jump from a
definition into a full listing and expect tracing to supply the missing idea.

Alternate levels of detail as the idea needs. An overview can introduce the
relationship, a close walkthrough can establish the mechanism, and a return
to the overview can explain the choice and cost. Learner-controlled segments
belong at meaningful subgoal boundaries, not at arbitrary line counts. Avoid
simultaneous unrelated motion while attention shifts between these views.

End each section by saying its durable takeaway and the connection to the
next section. Close the chapter by explaining how its solutions address the
opening problem and when to choose among them. Keep the lesson meaningful
after the listener forgets the values in the example.

Use question pauses when a prediction or explanation would help the lesson,
including why a choice helps or how it transfers to a changed requirement.
They are optional; do not manufacture a wrong answer or an incorrect
baseline to motivate a concept. Follow a question with an explanation of the
mechanism and tradeoff. Do not restart skills already demonstrated in the
listener's diagnostic notes; introduce an unfamiliar supporting facility by
its local purpose just before using it.

Narration contains no maths and no code; anything symbolic goes through the
glossary or a spoken form. The linter rejects `$` and maths glyphs in prose.

## Style sheet

The rows are the lesson; the words in them are throwaway, and yours come from
the chapter in front of you.

| don't | do |
|---|---|
| "On the board, the total comes to minus one." | "Take the total. Minus one." |
| "I'll give you the date because the chapter doesn't." | "Nineteen sixty-eight, in a paper nobody read for a decade." |
| "Total cost is Σ c(i), O(n log n) with a heap." | "Add up what you kept. With the right structure, the whole thing runs in n log n." |
| naming the method, then defining it | "Obvious plan: grab the smallest one anywhere. Feels right? Watch it strand you…" |
| dropping the author's aside | keeping it whole, in his voice — or cutting it whole. Never flattened into a claim. |
| "That's Figure 6.2, on page 194." | nothing — the page and figure are written under the tab. Spoken only to say where the book is wrong. |
| "We watched greedy fail back in Chapter 1." | "Four towns in a row. Nearest-first zigzags and pays the long leg home; the straight route is shorter." — shown, then, if useful, "Chapter 1 opens with it." |

## Display blocks and spoken forms

The engine receives prose paragraphs only. A block is prose when it starts
with a word character; a `$$` equation, a fenced listing, a `|` table, a `>`
quotation, an image, an SVG is a **display block**. One the author refers to
gets a spoken form right after it, in the same paragraph — the paraphrase a
lecturer would say, not a transliteration; one without a spoken form is
dropped from the audio and reported.

```markdown
$$E[X] = \sum_{i=1}^{n} x_i \, p_i$$
<!-- spoken: multiply every outcome by how likely it is, add those up, and
     that is what you should expect on average -->
```

## Honesty

Principle 5 (`teaching.md`) applies to every sentence. Watch for: merged
caveats, the wrong proof on the wrong result, number drift, "always/every",
opinions the author never voiced, borrowed credit, speculative closers. Book
errors go under `<!-- corrections -->`.

## Script format

The one description of `script.md`; `scripts/lecture_format.py` implements
it.

```markdown
# <Chapter title>

<!-- author: … -->
<!-- pronounce: Nyquist = NYE-kwist; Cholesky = ko-LES-kee -->
<!-- glossary
…
-->
<!-- outline
7     The Chapter's Title            -> skip: title
7.1   The First Idea                 -> alpha
7.1.1 A Worked Example               -> alpha
7.2   The Second Idea                -> beta
7.5   Exercises                      -> skip: drill set
-->
<!-- corrections: p. 114 states the bound the other way round; said aloud -->

## part: alpha

<!-- beat: alpha-need | frame 0 -->
A choice can restrict what remains possible. We need a reason to choose now
without losing the result we are trying to reach.

<!-- beat: alpha-idea | frame 1 -->
A safe choice preserves a way to reach the best result. Once we establish
that property, we can commit to the choice and solve the remaining problem.

<!-- beat: alpha-scan | frame 2 -->
Here is the book's small case. These values let us test that condition.
Three of them are in reach: <!-- mark: item-a -->the first, at five,
<!-- mark: item-b -->the second, at seven, <!-- mark: item-c -->the third,
at twelve. Which one do I take?
<!-- ask -->

<!-- beat: alpha-take | frame 3 -->
If you reached for the one at two, over on the far side — that's the trap:
it isn't in reach yet. <!-- mark: item-a -->The first, at five. Here is why
that is safe…

## part: beta
<!-- beat: beta-1 -->
…
```

- `## part: <key>` matches `data-part="<key>"` in the page.
- `<!-- beat: id | frame N -->` starts a beat at frame N; `<!-- beat: id -->`
  holds the frame (`sync-architecture.md`, "Beats").
- `<!-- mark: id -->` right before the words it belongs to; `<!-- mark: id |
  frame N -->` also changes the slide there. Ids are whatever the page's
  `render(frame, mark)` understands; frames named by marks increase within a
  beat.
- `<!-- ask -->` right after the question's paragraph, and it ENDS its beat:
  the answer is the next beat, and that beat moves to a different frame.
  Otherwise the audio stops with the answer already on the screen the
  question was asked on. The answer may open with the trap ("if you said…").
- `<!-- pause 2s -->` inside prose becomes silence (clamped to the limit in
  `lecture_format.py`).
- `outline` maps every heading of `extract/outline.txt`, including the
  chapter-title line, to a part or `skip: <reason>`; invent ids for
  unnumbered sections (`19.2`, `6.notes`) and use the same ids in both.
- `pronounce:` respellings are substituted before synthesis, for every
  engine; subtitles keep the real spelling.
