# Sync architecture

`audio.currentTime` is the only clock: the current frame and mark are
derived from it on every animation tick, so `render` draws state and never
animates on its own schedule.

## Frames

A part's slides are an array of **frames** — snapshots the page can draw,
one canvas each. `player.js` treats them as opaque — only the page's
`render` looks inside — and reads two optional keys:

- `label` — the name shown on the ribbon tick and counter ("Facade", "apply
  the rotor"); default "Step n"
- `tone` — `good` | `bad` | `mark` | `end`, colours the ribbon tick only;
  `render` colours the drawing itself

Produce frames by running the process in the page's own JavaScript when the
drawing can be computed from an example (an algorithm over a small graph, a
construction the algebra computes); write them by hand otherwise (add a class
box, reveal the next derivation line, fill a table row). Either way each
frame is drawable from the object alone:

```js
{ label: 'accept e3', tone: 'good', tree: [...], dist: {...} }       // computed
{ label: 'Facade', show: ['Employee', 'Facade'], highlight: ['e1'] }  // authored
{ label: 'expand', eq: 'eq-13-4', lines: 3, mark: 'term-2' }         // derivation
```

A voice-only stretch is a part with one frame. An interactive explorer
(slider, click-to-toggle) has no timeline; mount it as that one frame and
let the author set it up.

## Beats

A **beat** is one idea in the narration (syntax: `narration-craft.md`,
"Script format"). It declares the frame it starts on and runs until the
next beat starts; a beat with no frame holds whatever is showing. Start
frames increase strictly within a part; the last beat runs to the final
frame. Within a beat, if its marks name frames, frames change only on those
marks; a beat that covers several frames and names none of them falls back
to spreading them evenly across its duration — the linter reports that
case, because it is a guess.

## Marks

A **mark** names something on the slide, placed in the script right before
the words it belongs to; its time is the first spoken word after it, and it
may also change the frame. The player calls `render(frame, mark)` whenever
either changes; `mark` is the id of the last mark whose time has passed
within the current beat, or `null` at the start of a beat. What "lit" means
is the page's business; pages that ignore the second argument still work.

## Cues

`build_audio.py` writes `cues/<part>.json` per part and `cues/cues.js`,
which gathers them into `window.LECTURE_CUES = {part: …}` (a script tag,
because `fetch()` of a local file is blocked on `file://`). A cue file
holds `audio`, `duration`, `engine`, `model`, `voice`, and the timed lists
`beats` (`id, frame, t, end`), `marks` (`id, frame, t`), `questions` (`id,
t, prompt`) and `subs` (sentences with per-word times). Every time comes
from `cues/<part>.align.json`, the start time of each spoken word.

**Asks.** When playback crosses an ask's `t` the player pauses and shows the
question in the caption bar, where the words were; the picture stays fully
visible. Play (or Space) resumes, the caption bar goes back to captioning,
and the answer is simply what the author says next. Seeking past an ask
does not trigger it.

**Caption and transcript.** Under the slide, the current sentence with
words lit as spoken and the current one marked — always on. Under that, the
transcript: every sentence of the part in a scrollable panel, the current
one lit and kept in view; click one to jump. The transcript never takes the
picture's place; in fullscreen it is hidden with the controls.

## The page

```js
createLecture({
  parts: [ { key: 'prim', name: 'Prim', frames: [...], render: fn(frame, mark) }, … ]
}) -> { players: {key: player}, activate(key, frame?), fullscreen(on) }
```

The page supplies, per part, one `<section data-part="key">` holding a
`.slide` (the canvas; the player draws the slide number bottom-left and the
fullscreen button bottom-right onto it) and a `.transport` (the mount for
the controls), plus a `.tabs` element; `createLecture` does the rest — the
tab buttons, the cue lookup and audio, the `#part:frame` hash on load and on
`hashchange` (how the screenshots in step 3 open any frame headlessly),
fullscreen (the button, `F`, `Esc`), number keys 1–9 for parts. Switching
parts stops the other part's audio. Without cues a part is a manual
stepper, so the page is useful before audio exists.

Navigation moves the position; Play decides whether sound comes out. ← →
step one slide (with audio: seek to that slide's moment, no auto-play);
Space play/pause; Shift+← → ±10 s; the ribbon and the seek bar do the same
with the mouse. In fullscreen only the slide and the caption remain; the
controls appear while the mouse moves and fade when it stops.

The page is self-contained: `build_page.py` inlines the player, embeds
images, and renders `$…$`/`$$…$$` in static markup to MathML (`\lt` `\gt`
for inequalities inside maths); fonts may load from Google Fonts with real
fallbacks, nothing else is external. `assets/player.css` part 1 is what the
player builds — keep its class names, restyle through the `:root` tokens
(`--bg --panel --ink --muted --rule --shade --accent --good --bad --mark
--idle --mono --serif --sans`) so light and dark both work. Every part's
SVG lives in one document, so prefix SVG ids (markers, gradients, clip
paths) with the part key; the linter reports duplicates.
`highlightCode(text, lang)` colours a listing (`slides.md`, "Code on
slides").

## Engines

One module per voice engine in `scripts/engines/`, with the contract in
`scripts/engines/__init__.py`; every engine writes the same
`cues/*.align.json`. Which engine is used when is SKILL.md steps 5–6;
setup is `kokoro.md` and `elevenlabs.md`.
