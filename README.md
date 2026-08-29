# chapter-to-synced-lecture

A [Claude Code](https://claude.com/claude-code) skill that turns a book chapter
(PDF) into a lecture given by its author.

You get one self-contained HTML page: slides the narration drives, questions the
audio stops on so you can think, word-synced captions, and a picture that lights
whatever the voice is naming at that moment.

The voice runs locally on **[Kokoro](https://huggingface.co/hexgrad/Kokoro-82M)**
— free, unlimited, about a minute of GPU time for an hour of narration. ElevenLabs
is optional, for a final take once the words are settled.

## What it does

Five steps, from a PDF to a page open in your browser:

| | |
|---|---|
| **Read** | pull out the text, the figures, and page renders of anything the text layer mangles |
| **Plan** | decide what each part is for: the trouble it opens on, the example that carries it |
| **Slides** | build the deck — where an algorithm or construction is involved, frames are *computed by running it*, not drawn by hand |
| **Script** | write the narration from what the slides actually computed, then a fresh reader checks where it loses a newcomer |
| **Record** | synthesise the audio and time every cue to the spoken word |

It is not a template. The lecture is built from the chapter's own argument,
examples and figures, so it works on algorithms, software design, mathematics,
economics — whatever the chapter is.

## Requirements

- Claude Code
- `poppler-utils` (`pdftotext`, `pdfimages`, `pdftoppm`), `ffmpeg`, `chromium`
- Kokoro in a virtualenv — see [`references/kokoro.md`](references/kokoro.md).
  An NVIDIA GPU makes it fast; CPU still beats real time.
- Optional: an ElevenLabs API key, for the paid final voice
  ([`references/elevenlabs.md`](references/elevenlabs.md))

## Install

```bash
git clone https://github.com/ajaygunalan/chapter-to-synced-lecture
ln -s "$PWD/chapter-to-synced-lecture" ~/.claude/skills/chapter-to-synced-lecture
```

Then, in Claude Code:

```
/chapter-to-synced-lecture @Ch06_Weighted_Graph_Algorithms.pdf
```

Optionally add a note about what you already know, or what to focus on.

## What's inside

```
SKILL.md      the recipe: five steps, in order
references/   the how-to: teaching principles, slide treatments, writing for
              the ear, the page/audio contract, PDF extraction, the two engines
scripts/      the tools: extract, build the page, lint, synthesise, time the run
assets/       player.js + player.css, copied into every lecture it builds
```

`references/teaching.md` is the contract everything else serves: put the
listener inside the problem before naming the idea, ask before telling, let the
slide show what is true right now while the voice says what it means.

## Licence

MIT. See [LICENSE](LICENSE).
