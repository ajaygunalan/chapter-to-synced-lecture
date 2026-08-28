# Narration craft

How to write a script the author's voice can deliver as a lecture. The
teaching decisions are in `teaching.md`; this is the writing.

## Before a word: the author profile and the glossary

Write both into `script.md`'s header.

**Author profile** — from reading the chapter: stance (practitioner telling
stories; co-constructor "let's build it"; authority), how he motivates (a
war story, a bug, history, "here's why you'd care"), how often he steps
aside and in what register, his humour, signature phrases to reuse
sparingly, how he closes a section. Reproduce the pattern, not the
sentences.

**Glossary** — a row per symbol, operator, identifier, acronym, and
typographic distinction, with its single spoken form; decided once.

```markdown
<!-- author: first-person practitioner; motivates with a real job gone wrong;
     wry, self-deprecating asides; closes with a boxed lesson -->
<!-- glossary
∞          the point at infinity
⌋          contracted onto
𝐩 vs p     the Euclidean vector p / the conformal point p
DIP        always "dependency inversion" — the letters read as "dip"
calculatePay()   the calculate-pay method
purplecab.com/driver   purple cab dot com, slash driver
-->
```

Acronyms: word (SOLID) or letters (S-R-P); anything the engine could read as
an English word gets expanded. Identifiers are screen-only; the voice says
"the calculate-pay method". Typography that carries meaning is said aloud.
Diagram legend once, then plain verbs. Every proper noun gets a `pronounce:`
entry in the header block.

## Writing for the ear

- One idea per sentence; front-load the point; contractions; "you" and "we".
- Name things before using them — a listener cannot glance up at a label.
- Signpost what the eye gets from layout: "three things to hold", "here's
  the part worth slowing down on", "that was the mechanical bit".
- Say the key idea until it lands — formally, as a picture, as a rule of
  thumb — in whatever forms the moment wants. Some listeners are fogged out
  at any given moment.
- Keep something happening; a chapter is "therefore / but", never "and
  then".
- Emphasis with words and CAPITALS, not markup. Pauses with full stops,
  paragraph breaks, "…", and a `pause` where the listener needs a moment to
  think (Script format).
- Read every draft aloud. What you stumble on, the engine stumbles on.

Narration contains no maths and no code; anything symbolic goes through the
glossary or a spoken form. The linter rejects `$` and maths glyphs in prose.

## Style sheet

| don't | do |
|---|---|
| "The edge B–D turns green." | "Of everything touching the tree, B–D is cheapest. That's the only question I ever ask." |
| "On the board, the inner product is minus one." | "Take their inner product. Minus one." |
| "I'll give you the dates because the chapter doesn't." | "Meyer, 1988. Liskov, the year before." — the source sits in the plan |
| "The reader will note that the cut property guarantees safety." | "Here's why you can trust that edge: it crosses the cut, and nothing cheaper does." |
| "Prim adds the lightest crossing edge." (cold) | "Obvious plan: grab the cheapest edge anywhere. Feels right? Watch it strand a vertex… that's why I only look at the frontier." |
| "Next Prim picks C–E with weight 2." | "Three edges leave the tree. Which one?" — then a question block; C–E's reply: "you're thinking like the algorithm." |
| "MST cost is Σ w(e), O(E log V) via a heap." | "Add up the weights you kept. With a heap, the whole thing runs in E log V." |
| a 40-word sentence with a semicolon | two sentences, one idea each; the second starts with "So". |
| "That concludes Prim's algorithm." | "So that grows one tree. But what if you grew a forest — many little trees merging? That's Kruskal, and it's next." |
| dropping the author's aside | keeping it whole, in his voice — or cutting it whole. Never flattened into a claim. |

## Display blocks and spoken forms

The engine receives prose paragraphs only. A block is prose when it starts
with a word character; a `$$` equation, a fenced listing, a `|` table, a `>`
quotation, an image, an SVG is a **display block**. One the author refers to
gets a spoken form right after it — the paraphrase a lecturer would say, not
a transliteration; one without a spoken form is dropped from the audio and
reported.

```markdown
$$W[i,j]^k = \min\left(W[i,j]^{k-1},\; W[i,k]^{k-1} + W[k,j]^{k-1}\right)$$
<!-- spoken: the best route from i to j using only the first k stops is
     either what you already had, or the trip through k — whichever is shorter -->
```

## Fidelity

Principle 5 (`teaching.md`) applies to every sentence. Watch for: merged
caveats, the wrong proof on the wrong result, number drift, "always/every",
borrowed credit, speculative closers. Where the book is wrong (a mislabelled
diagram), show it corrected on screen and list it under
`<!-- corrections -->`.

## Script format

The one description of `script.md`; `scripts/lecture_format.py` implements
it.

```markdown
# <Chapter title>

<!-- author: … -->
<!-- pronounce: Skiena = SKEE-nuh; Dijkstra = DYKE-struh -->
<!-- glossary
…
-->
<!-- outline
6     Weighted Graph Algorithms      -> skip: title
6.1   Minimum Spanning Trees         -> prim
6.1.1 Prim's Algorithm               -> prim
6.7   Exercises                      -> skip: drill set
-->
<!-- corrections: Fig 6.5 array shown with 0 = root, as a legend -->

## part: prim

<!-- beat: prim-trouble | frame 0 -->
Say we have to wire seven towns… <!-- pause 2s --> …and that guess is three
too heavy.

<!-- beat: prim-scan | frame 1 -->
<!-- question: prim-q1 -->
Three edges leave what we own. Which one do I take?
A. A–D, weight 7 | Cheapest anywhere — but it doesn't touch the tree. I only look at the frontier.
B. B–C, weight 7 | Right. The cheapest way out of what we already own.
C. A–G, weight 12 | Three cheaper doors exist. Never that one.
<!-- end -->

Here's why that's safe…

## part: nets
<!-- beat: nets-1 -->
…
```

- `## part: <key>` is one part of the lecture — one tab, one audio file —
  and matches `data-part="<key>"` in the page.
- `<!-- beat: id | frame N -->` starts a beat at frame N; `<!-- beat: id -->`
  holds (semantics: `sync-architecture.md`, "Beats start at a frame").
- `<!-- question: id -->` … `<!-- end -->`: the prompt (spoken), then the
  options as `A. option | reply` lines — as many as there are real
  misconceptions, lettered in order; options on screen, replies recorded.
  No blank lines inside the block.
- `<!-- pause 2s -->` inside prose becomes silence (the engine's limit is
  3 s).
- `outline` maps every heading of `extract/outline.txt`, including the
  chapter-title line, to a part or `skip: <reason>`; invent ids for
  unnumbered sections (`19.2`, `6.notes`) and use the same ids in both.
- `pronounce:` respellings are substituted before synthesis; subtitles keep
  the real spelling.
