# Sync architecture

`audio.currentTime` is the only clock. No `setInterval`, no CSS animation on
its own schedule. Every frame and every mark is derived from the audio
position on each animation tick, which makes drift impossible and gives
scrubbing, seeking, and playback speed for free.

## Frames

A part's slides are an array of **frames** — snapshots the page can draw,
one canvas each. `player.js` treats them as opaque — it never looks inside a
frame; only the page's `render` does — and reads two optional keys:

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
on; it runs until the next beat starts:

```
<!-- beat: prim-init | frame 0 -->    starts at frame 0
<!-- beat: prim-scan | frame 1 -->    covers frames 1…5 if the next beat starts at 6
<!-- beat: prim-aside -->             no frame: holds whatever is showing
<!-- beat: prim-pick | frame 6 -->    one frame, because the next starts at 7
```

Start frames increase strictly within a part; the last beat runs to the
final frame.

## Marks: what the voice names lights up as it is named

A **mark** is a name the page understands, placed in the script right before
the words it belongs to. Its time is the first spoken word after it. It may
also change the frame:

```
F offers <!-- mark: edge-CF -->C for 4, better than the 7 through B.
<!-- mark: edge-EF -->E for 3. <!-- mark: edge-FG | frame 5 -->G for 4.
```

The player calls `render(frame, mark)` whenever either changes; `mark` is the
id of the last mark whose time has passed within the current beat, or `null`
at the start of a beat. What "lit" means is the page's business — an edge
turns violet, a table cell flashes, a code line comes into focus, a bullet
appears, a term in an equation is boxed. One mechanism for all of them;
pages that ignore the second argument still work.

Frames inside a beat: if the beat's marks name frames, frames change only on
those marks. Only a beat that covers several frames and names none of them
falls back to spreading them evenly across its duration — the linter reports
that case, because it is a guess.

Mark only what the listener would otherwise have to search for — one edge
among twelve, one line among forty. What is already obvious is not marked.

## What build_audio.py writes

`cues/<part>.json`, one per part, and `cues/cues.js`, which gathers them
into `window.LECTURE_CUES = {part: …}` (a script tag: `fetch()` of a local
file is blocked on `file://`). Regenerating audio never touches the HTML.

```json
{
  "part": "prim", "audio": "audio/prim.mp3", "duration": 214.6,
  "engine": "kokoro", "model": "Kokoro-82M", "voice": "af_sky",
  "beats": [
    { "id": "prim-init",  "frame": 0,    "t": 0.0,  "end": 7.4 },
    { "id": "prim-scan",  "frame": 1,    "t": 7.4,  "end": 21.9 },
    { "id": "prim-aside", "frame": null, "t": 21.9, "end": 30.2 },
    { "id": "prim-pick",  "frame": 6,    "t": 30.2, "end": 38.0 }
  ],
  "marks": [ { "id": "edge-CF", "t": 9.1, "frame": null }, { "id": "edge-FG", "t": 14.8, "frame": 5 } ],
  "questions": [ { "id": "prim-ask1", "t": 41.2, "prompt": "Three edges leave what we own. Which one do I take?" } ],
  "subs": [ { "t": 7.4, "end": 12.1,
              "text": "Now look at every edge leaving that first vertex.",
              "words": [[7.4, "Now"], [7.6, "look"], …] }, … ]
}
```

Every time comes from one table, `cues/<part>.align.json` — the start time
of each word, derived from the engine's alignment. Beat `t` is the time of
its first word; a mark's `t` is the time of the first word after it; an ask's
`t` is where the question ends; subtitles are sentences with their words'
times.

**Asks.** An `<!-- ask -->` in the script after the question's paragraph.
When playback crosses `t` the player pauses and shows the question in the
caption bar, where the words were; the picture stays fully visible. The
listener thinks; Play (or Space) resumes, the caption bar goes back to
captioning, and the answer is simply what the author says next. Seeking past
an ask does not trigger it.

**Captions and transcript.** Under the slide, the current sentence with
words lit as spoken and the current one marked — always on. Under that, the
transcript: every sentence of the part in a scrollable panel, the current one
lit and kept in view; click one to jump. The transcript never takes the
picture's place. In fullscreen it is hidden with the controls.

## The page

```js
createLecture({
  parts: [ { key: 'prim', name: 'Prim', frames: [...], render: fn(frame, mark) }, … ],
  tabs: document.querySelector('.tabs')     // optional; default .tabs; null for none
}) -> { players: {key: player}, activate(key, frame?), fullscreen(on) }
```

`createLecture` owns everything a page used to copy: one `<section
data-part="key">` per part (found by key; a `.slide` inside it is the
canvas the player draws the slide number — bottom left — and the fullscreen
button — bottom right — onto; a `.transport` is the mount, or one is
appended), the cue lookup, `new Audio('audio/<key>.mp3')` only when cues
exist, the tab buttons (`name` as text or `tab` as HTML), the `#part:frame`
hash on load and on `hashchange` — which is how the screenshots in step 3
open any frame headlessly — fullscreen (the button, `F`, `Esc`), and number
keys 1–9 for parts. Switching parts stops the other part's audio. A page
needs the frames and `render` and nothing else; `onBeat(beat)` is optional.

Navigation moves the position; Play decides whether sound comes out. ← →
step one slide (with audio: seek to that slide's moment, no auto-play, so
flipping through with the audio paused is silent); Space play/pause; Shift+←
→ ±10 s; the ribbon and the seek bar do the same with the mouse. In
fullscreen only the slide and the caption remain; the transport appears
while the mouse moves and fades when it stops.

Underneath, each part is one `createSyncedPlayer` (an internal of
`createLecture`). Its transport: a seek bar with a `m:ss / m:ss` clock, ◀,
−10 s, Play/Pause/Resume, +10 s, ▶, Restart, speed (0.85–1.5×), the frame
ribbon, then the caption, then the transcript. Without cues it is a manual
stepper, so the page is useful before audio exists; with one frame the
ribbon is hidden.

`highlightCode(text, lang)` (also in `player.js`) colours a listing;
how a page uses it is `slides.md`, "Code on slides".

`assets/player.css` part 1 is what the player builds — keep its class names,
restyle through the tokens. Every part's SVG lives in one document, so
prefix SVG ids (markers, gradients, clip paths) with the part key; the
linter reports duplicates.

## One audio file per part

The part is the navigation unit, so a tab switch is a natural audio
boundary, and regenerating one part's phrasing costs one file. A part over
the engine's per-request limit is split at paragraph boundaries, synthesised
in pieces, and concatenated; the split is invisible to the player.

## Engines

One module per engine in `scripts/engines/`, all with the contract in
`scripts/engines/__init__.py`; `build_audio.py` never names one. Every
engine writes the same `cues/*.align.json`, so nothing downstream knows
which one spoke. Which engine is used when is SKILL.md steps 5–6; each
engine's setup is its reference (`kokoro.md`, `elevenlabs.md`).

Audio from any other source (another engine, a human reading) can still be
used by running forced alignment (`whisperx`, `aeneas`) over the audio and
the script to produce the same `cues/*.align.json`.
