# Extraction

What a PDF's text layer loses, and how `scripts/extract.py` recovers it.
The rule: **anything `inventory.md` flags is read from the page render, not
from `text.txt`.**

## What the extractor writes

```
extract/
├── text.txt        pdftotext -layout, pages separated by form feeds; prose is reliable
├── outline.txt     heading candidates, one per line — weak, see below
├── images/         every embedded raster (pdfimages): UML, photographs, plots
├── pages/          pNNN.png render of each flagged page
└── inventory.md    counts, pages grouped by flag, image table
```

`outline.txt` is a heuristic over numbered headings, and it misses whole
chapters: a book whose sections are unnumbered Title Case yields nothing at
all, and even a numbered one usually yields about half. Read the section
headings out of `text.txt` yourself and hand-correct the file before writing
the plan — the outline block in `script.md` is checked against it, so a short
outline silently weakens that check.

Pages are flagged for: raster images, numbered equations or dense maths,
lossy glyphs, tables, figure captions, code listings. The default render
is enough to read prose and equations but not always edge weights or
thin-vs-bold edges in a figure; re-render those pages at a higher dpi
(`extract.py --help`, `--pages`) into a second directory.

## Losses by content type

- **Vector figures** (graphs, trees, geometric drawings) come out as
  scattered labels with no edges. Rebuild from the text's description or
  edge list, or read the render.
- **Raster figures** (UML, screenshots, photographs) vanish from the text
  *without any marker*; `images/` has them. Some diagrams are laid out as
  text boxes and do extract — the render tells you which.
- **Maths and pseudocode** are actively misleading in the text layer: it
  silently deletes or substitutes operators (`≠` gone turns an inequality
  into an equation), primes, hats, superscripts, and bold-vs-italic, and
  leaves no lossy flag — the text reads as plausible maths that says
  something else. Transcribe every displayed equation and every piece of
  pseudocode from the render, as LaTeX for `render_math.py`; use `text.txt`
  only to find where they are.
- **Tables** extract as aligned text and are usually recoverable; check
  column alignment on the render.
- **Code listings** keep their indentation under `-layout`.
- **Furniture** — running heads, page numbers, footnotes — interleaves with
  body text. Cartoons and author photographs land in `images/` and are not
  figures.

## Figure inventory

Keep one while reading: it decides what the slides rebuild, what they
embed, and what the lecture skips.

| ref | what | extracted as | usable? |
|---|---|---|---|
| Fig 4.2 | the figure the chapter keeps pointing back to | labels only, no lines | rebuild it from the data in the caption and the prose |
| Diagram p.112 | a twenty-box block diagram | images/img-008-003.png | yes, embed the raster |
| Eq 7.1 | the definition the argument turns on | text (lossy) + pages/p112.png | transcribe from the render, never the text |

Beyond this (OCR of scans, splitting, merging): the `document-skills:pdf`
skill.
