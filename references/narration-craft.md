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

<!-- beat: alpha-trouble | frame 0 -->
Say you have to do this by hand, a hundred times over…
<!-- pause 2s --> …and that guess is three too many.

<!-- beat: alpha-scan | frame 1 -->
Three of them are in reach: <!-- mark: item-a -->the first, at five,
<!-- mark: item-b -->the second, at seven, <!-- mark: item-c -->the third,
at twelve. Which one do I take?
<!-- ask -->

<!-- beat: alpha-take | frame 2 -->
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
