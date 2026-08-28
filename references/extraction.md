# Extraction

What a PDF's text layer loses, and how `scripts/extract.py` recovers
it. The rule: **anything `inventory.md` flags is read from the page render,
not from `text.txt`.**

## What the extractor writes

```
extract/
├── text.txt        pdftotext -layout, pages separated by form feeds; prose is reliable
├── outline.txt     heading candidates, one per line (heuristic — confirm against renders)
├── images/         every embedded raster (pdfimages): UML, photographs, plots
├── pages/          pNNN.png render of each flagged page (~110 dpi)
└── inventory.md    counts, pages grouped by flag, image table
```

Pages are flagged for: raster images, numbered equations or dense maths,
lossy glyphs, tables, figure captions, code listings. `--all-pages` renders
everything. 110 dpi is enough to read prose and equations but not always
edge weights or thin-vs-bold edges in a figure; re-render those pages with
`--pages 4,5,9-11 --dpi 300` into a second directory.

## Losses by content type

- **Vector figures** (graphs, trees, geometric drawings) come out as
  scattered labels with no edges. Rebuild from the text's description or edge
  list, or read the render.
- **Raster figures** (UML, screenshots, photographs) vanish from the text
  *without any marker*. A design chapter can lose ten of thirteen figures and
  read as if it had none; `images/` has them. Some diagrams are laid out as
  text boxes and do extract — the render tells you which.
- **Maths and pseudocode** are actively misleading in the text layer.
  Verified on a geometric-algebra chapter and an algorithms chapter: the
  contraction operator `⌋` deleted at every occurrence; `≠` deleted (so
  `−∞·p ≠ 0` reads `−∞·p = 0`, and pseudocode `if (a ≠ b)` reads `if (a =
  b)`); primes dropped; hats and tildes dropped; `½p²` → `12 p2`; `★` →
  `夹`, `φ` → `␾`; superscript `-1` floating to the next line; **bold vs
  italic lost**, so a Euclidean vector and a conformal point become the same
  letter. Deletions leave no trace and no lossy flag — the text reads as
  plausible maths that says something else. Transcribe every displayed equation from the render, as LaTeX for
  `render_math.py`; use `text.txt` only to find where equations are.
- **Tables** extract as aligned text and are usually recoverable; check
  column alignment on the render.
- **Code listings** keep their indentation under `-layout`; pseudocode with
  relational glyphs does not (see above) and is transcribed from the render.
- **Furniture** — running heads, page numbers, footnotes — interleaves with
  body text. Cartoons and author photographs land in `images/` and are not
  figures.

## Figure inventory

Keep one while reading; it decides what the slides rebuild, what they embed,
what plan.md lists under "what the chapter has that the lecture skips", and
it drives the "stop and ask" rule:

| ref | what | extracted as | usable? |
|---|---|---|---|
| Fig 6.3 | example graph with two spanning trees | labels only | rebuild from the edge list |
| UML p.349 | 20-box class diagram | images/img-008-003.png | yes |
| Eq 13.2 | point representation | text (lossy) + pages/p360.png | transcribed from render |

## Tools

poppler (`pdftotext`, `pdfimages`, `pdftoppm`) with `pymupdf` as fallback,
all installed. The `document-skills:pdf` skill covers anything beyond this
(OCR of scans, splitting, merging).
