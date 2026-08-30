# chapter-to-synced-lecture

A [Claude Code](https://claude.com/claude-code) skill that turns a book chapter
(PDF) into a **video lecture**: narration plus slides that animate along with
it, given in the voice of the book's own author.

It comes out as one self-contained web page you open in a browser — not an MP4,
but it plays like one, and you can pause, scrub, jump to any slide, or read the
transcript.

**No API key needed.** The voice runs on your own machine with
[Chatterbox](https://github.com/resemble-ai/chatterbox), Resemble AI's open
500M model (MIT): free, unlimited, a natural reader with an emotion knob and a
pacing knob — about half an hour of GPU time for an hour of narration on a
laptop card, because a forced aligner
([torchaudio's MMS](https://docs.pytorch.org/audio/stable/tutorials/ctc_forced_alignment_api_tutorial.html),
no extra install) times every word after it is spoken.
[TADA-1B](https://github.com/HumeAI/tada), Hume's open-weights narrator, is
the alternative — word timing straight from the model, a quarter of an hour
per hour of narration. [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M)
is the small fast fallback (a minute an hour, flatter). ElevenLabs is
optional, if you want a paid voice for a final take.

## What you get

- **Slides that animate with the voice.** When the narration says "A to B, for
  five," that edge lights up at that word.
- **Questions it stops on.** The audio pauses on a question and waits. Press
  play when you have an answer.
- **Captions in sync**, word by word, plus a full transcript you can click to
  jump anywhere.
- **Slides that show real runs.** If the chapter has an algorithm, the page
  contains a working copy of it and *runs* it to make the slides. So the picture
  can never disagree with the algorithm, and the narration is written from what
  the slides actually produced.

## Then you revise it with the same command

Point it at the same PDF and it finds the lecture already there, reads it, and
gets ready to teach. Go through a tab, say what lost you, and it explains that
bit in the chat first — then edits the script or the slide once you're happy,
and re-records just that part. A few seconds, because each tab is its own audio
file. Nothing else is touched.

## How it works

Five steps, from PDF to a lecture open in your browser:

| | |
|---|---|
| **Read** | pull out the text and figures, and render any page the text layer mangles |
| **Plan** | work out what each part is for: the problem it opens on, the example that carries it |
| **Slides** | build the deck |
| **Script** | write the narration, then have a fresh reader find where it loses a newcomer |
| **Record** | make the audio and time every cue to the spoken word |

It is not a template. Each lecture is built from that chapter's own argument,
examples and figures — so it works on algorithms, software design, mathematics,
economics, whatever the chapter happens to be.

## Requirements

- Claude Code
- `poppler-utils`, `ffmpeg`, `chromium`
- Chatterbox in a virtualenv — [`references/chatterbox.md`](references/chatterbox.md):
  an NVIDIA GPU with 8 GB; nothing to sign, the weights are open.
- Optional alternatives: TADA — [`references/tada.md`](references/tada.md)
  (a one-time click on Meta's Llama 3.2 licence for its tokenizer); Kokoro —
  [`references/kokoro.md`](references/kokoro.md), a CPU still beats real time.
- Optional: an ElevenLabs key for the paid voice
  ([`references/elevenlabs.md`](references/elevenlabs.md))

## Install

```bash
git clone https://github.com/ajaygunalan/chapter-to-synced-lecture
ln -s "$PWD/chapter-to-synced-lecture" ~/.claude/skills/chapter-to-synced-lecture
```

Then in Claude Code:

```
/chapter-to-synced-lecture @Ch06_Weighted_Graph_Algorithms.pdf
```

You can add a note about what you already know, or what to focus on.

## What's inside

```
SKILL.md      the recipe: five steps, in order
references/   how to teach, what a slide should show, how to write for the ear,
              how the page and audio stay in step, what PDFs lose, the voices
scripts/      the tools: extract, build, check, synthesise
assets/       the player copied into every lecture it builds
```

[`references/teaching.md`](references/teaching.md) is the rule everything else
serves: put the listener inside the problem before naming the idea, ask before
telling, and let the slide show what is true right now while the voice says what
it means.

## Licence

MIT. See [LICENSE](LICENSE).
