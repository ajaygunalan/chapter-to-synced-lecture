# Sync architecture

`audio.currentTime` is the only clock. No `setInterval`, no CSS animation on
its own schedule. Every frame is derived from the audio position on each
animation tick, which makes drift impossible and gives scrubbing, seeking,
and playback speed for free.

## Frames

A part's slides are an array of **frames** — snapshots the page can draw,
one canvas each. `player.js` treats them as opaque and calls your
`render(frame)`; it reads two optional keys:

- `label` — the name shown on the ribbon tick and counter ("Facade", "apply
  the rotor"); default "Step n"
- `tone` — `good` | `bad` | `mark` | `end`, colours the ribbon tick only;
  `render` colours the drawing itself. The page maps its own vocabulary
  (accept/reject/pivot…) onto these four

Produce frames by running the process in the page's own JavaScript when the
drawing can be computed from an example (an algorithm over a small graph, a
construction the algebra computes); write them by hand otherwise (add a class
box, reveal the next derivation line, fill a table row). Either way each
frame should be drawable from the object alone:

```js
{ label: 'accept e3', tone: 'good', tree: [...], dist: {...} }       // computed
{ label: 'Facade', show: ['Employee', 'Facade'], highlight: ['e1'] }  // authored
{ label: 'expand', eq: 'eq-13-4', lines: 3, mark: 'term-2' }         // derivation
```

A voice-only stretch is a part with one frame. An interactive explorer
(slider, click-to-toggle) has no timeline; mount it as that one frame and
let the author set it up.

## Beats start at a frame

A **beat** is one idea in the narration. It declares the frame it starts
on; it runs until the next beat starts. That is the whole contract:

```
<!-- beat: prim-init | frame 0 -->    starts at frame 0
<!-- beat: prim-scan | frame 1 -->    covers frames 1…5 if the next beat starts at 6
<!-- beat: prim-aside -->             no frame: holds whatever is showing
<!-- beat: prim-pick | frame 6 -->    one frame, because the next starts at 7
```

Start frames increase strictly within a part; the last beat runs to the
final frame. A beat that covers several frames spreads them evenly across
its duration — a mechanical stretch moves quickly under one sentence — and
a beat that covers one holds while the explanation lands.

## What build_audio.py writes

`cues/<part>.json`, one per part, and `cues/cues.js`, which gathers them
into `window.LECTURE_CUES = {part: …}` (a script tag: `fetch()` of a local
file is blocked on `file://`). Regenerating audio never touches the HTML.

```json
{
  "part": "prim", "audio": "audio/prim.mp3", "duration": 214.6, "model": "…", "voice": "…",
  "beats": [
    { "id": "prim-init",  "frame": 0,    "t": 0.0,  "end": 7.4 },
    { "id": "prim-scan",  "frame": 1,    "t": 7.4,  "end": 21.9 },
    { "id": "prim-aside", "frame": null, "t": 21.9, "end": 30.2 },
    { "id": "prim-pick",  "frame": 6,    "t": 30.2, "end": 38.0 }
  ],
  "questions": [ { "id": "prim-ask1", "t": 41.2, "prompt": "Three edges leave what we own. Which one do I take?" } ],
  "subs": [ { "t": 7.4, "end": 12.1,
              "text": "Now look at every edge leaving that first vertex.",
              "words": [[7.4, "Now"], [7.6, "look"], …] }, … ]
}
```

Every time comes from one table, `cues/<part>.align.json` — the start time
of each word, derived from the provider's per-character alignment. Beat `t`
is the time of its first word; an ask's `t` is where the question ends;
subtitles are sentences with their words' times.

**Asks.** An `<!-- ask -->` in the script after the question's paragraph.
When playback crosses `t` the player pauses and shows the question on the
slide; the listener thinks; Play (or Space) resumes, and the answer is
simply what the author says next. Seeking past an ask does not trigger it.

**Captions.** Under the slide, the current sentence with words lit as
spoken and the current one marked — always on. The **Transcript** tab (the
last tab) shows every sentence of the active part; click one to jump
there; the audio keeps playing while you read.

## The page

```js
createLecture({
  parts: [ { key: 'prim', name: 'Prim', frames: [...], render: fn(frame) }, … ],
  tabs: document.querySelector('.tabs')     // optional; default .tabs; null for none
}) -> { players: {key: player}, activate(key, frame?), fullscreen(on) }
```

`createLecture` owns everything a page used to copy: one `<section
data-part="key">` per part (found by key; a `.slide` inside it is the
canvas the player draws the slide number and the ask onto; a `.transport`
is the mount, or one is appended), the cue lookup, `new
Audio('audio/<key>.mp3')` only when cues exist, the tab buttons (`name` as
text or `tab` as HTML) plus the Transcript tab, the `#part:frame` hash on
load and on `hashchange` — which is how the screenshots in step 3 open any
frame headlessly — fullscreen (`F`, `Esc`), and number keys 1–9 for parts.
Switching parts stops the other part's audio. A page needs the frames and
`render` and nothing else; `onBeat(beat)` is optional.

Navigation moves the position; Play decides whether sound comes out. ← →
step one slide (with audio: seek to that slide's moment, no auto-play, so
flipping through with the audio paused is silent); Space play/pause; Shift+←
→ ±10 s; the ribbon and the seek bar do the same with the mouse. In
fullscreen only the slide, the caption and the transport remain.

Underneath, each part is a `createSyncedPlayer({frames, beats, subs,
questions, audio, render, mount, slide?, onBeat?, ribbon?, keys?})`
returning `{goto(i), seek(seconds), step(±1), toggle(), stop(), element,
transcript}`. Its transport: a seek bar with a `m:ss / m:ss` clock, ◀,
−10 s, Play/Pause/Resume, +10 s, ▶, Restart, speed (0.85–1.5×), the frame
ribbon, then the caption. With `audio: null` it is a manual stepper, so the
page is useful before audio exists; with one frame the ribbon is hidden.

`highlightCode(text, lang)` (also in `player.js`) returns coloured HTML
for a listing — keywords, types, strings, numbers, comments — for
`cpp` (default), `java`, `python`, `js`; the page wraps lines in
`.line` spans and adds its own teaching marks (`slides.md`, "Code on
slides").

`assets/player.css` part 1 is what the player builds — keep its class names,
restyle through the tokens. Every part's SVG lives in one document, so
prefix SVG ids (markers, gradients, clip paths) with the part key; the
linter reports duplicates.

## One audio file per part

The part is the navigation unit, so a tab switch is a natural audio
boundary, and regenerating one part's phrasing costs one file. A part over
the model's per-request character limit is split at paragraph boundaries,
synthesised with request stitching, and concatenated; the split is
invisible to the player.

## Provider

ElevenLabs, because its `with-timestamps` endpoint returns per-character
alignment — without alignment there is no sync. Audio from any other source
(another engine, a human reading) can still be used by running forced
alignment (`whisperx`, `aeneas`) over the audio and the script to produce
the same `cues/*.align.json`.
