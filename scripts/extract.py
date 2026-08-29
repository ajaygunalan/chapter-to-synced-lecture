#!/usr/bin/env python3
"""
chapter.pdf -> <out>/{text.txt, outline.txt, images/, pages/, inventory.md}

Pulls the three layers a text extractor alone loses (raster figures, page
renders for maths and figures, an inventory of what to read by eye). What each
output is for: references/extraction.md.

    extract.py chapter.pdf --out work/extract [--all-pages] [--dpi 110]
    extract.py chapter.pdf --out work/extract300 --pages 4,5,9-11 --dpi 300   # re-render a few pages

Needs poppler (pdftotext, pdfimages, pdftoppm); falls back to pymupdf.
"""

import argparse
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from lecture_format import stamp

LOSSY_RE = re.compile("[\ue000-\uf8ff\u2400-\u243f\u4e00-\u9fff\ufffd]")   # private-use, control pictures, CJK, U+FFFD in a Latin book
MATH_HINT_RE = re.compile(r"[=≠≈≤≥∑∏∫∞∂∇√∧∨⌋⌊⌈⌉⊂⊆∈∀∃→↦⊗⊕αβγδεθλμπρσφψω]|\b[a-zA-Z]\^")
NUMBERED_EQ_RE = re.compile(r"\((\d+\.\d+[a-z]?)\)\s*$", re.M)
FIGURE_RE = re.compile(r"^\s*(?:Figure|Fig\.)\s+(\d+(?:\.\d+)*)", re.M | re.I)
LETTERSPACED_RE = re.compile(r"\b(?:[A-Za-z] ){3,}[A-Za-z]\b")   # "F i g u r e" -> "Figure"
TABLE_RE = re.compile(r"^\s*Table\s+(\d+(?:\.\d+)*)", re.M | re.I)
CODE_LINE_RE = re.compile(r"^\s{2,}.*[;{}]\s*$|^\s*(for|while|if|return|def|class|struct|void|int)\b.*[({:;]\s*$")
HEADING_RE = re.compile(r"^[ \t]*(\d+(?:\.\d+){0,3})\s+([A-Z][^\n]{2,80}?)\s*$", re.M)   # any indent: -layout indents recto pages
CAPS_HEADING_RE = re.compile(r"^[ \t]*([A-Z][A-Z '\-:]{6,60})\s*$", re.M)


def have(tool):
    return shutil.which(tool) is not None


def unspace(text):
    """Some books set captions letter-spaced ("F i g u r e 13.1"); collapse those runs."""
    return LETTERSPACED_RE.sub(lambda m: m.group().replace(" ", ""), text)


def page_texts(pdf, doc):
    if have("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True)
        pages = r.stdout.split("\f")[:-1] or [r.stdout]
    else:
        pages = [p.get_text("text") for p in doc]
    return [unspace(t) for t in pages]


def extract_images(pdf, doc, out):
    """-> [(file, page, w, h)]"""
    out.mkdir(parents=True, exist_ok=True)
    if have("pdfimages"):
        r = subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True)
        meta = []
        for line in r.stdout.splitlines()[2:]:
            c = line.split()
            if len(c) >= 5 and c[0].isdigit():
                meta.append((int(c[0]), int(c[3]), int(c[4])))
        subprocess.run(["pdfimages", "-png", "-p", str(pdf), str(out / "img")], check=True)
        files = sorted(out.glob("img-*.png"))
        return [(f, p, w, h) for f, (p, w, h) in zip(files, meta)]
    import fitz
    result = []
    for pno, page in enumerate(doc, 1):
        for i, info in enumerate(page.get_images(full=True)):
            pix = fitz.Pixmap(doc, info[0])
            if pix.n - pix.alpha >= 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            f = out / f"img-{pno:03d}-{i:03d}.png"
            pix.save(str(f))
            result.append((f, pno, pix.width, pix.height))
    return result


def render_pages(pdf, doc, pages, out, dpi):
    out.mkdir(parents=True, exist_ok=True)
    if not pages:
        return
    if have("pdftoppm"):
        # one call per contiguous run; pdftoppm names files <root>-<page>.png
        runs, start = [], pages[0]
        for a, b in zip(pages, pages[1:] + [None]):
            if b != a + 1:
                runs.append((start, a))
                start = b
        for a, b in runs:
            subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(a), "-l", str(b), "-png",
                            str(pdf), str(out / "p")], check=True)
        for f in out.glob("p-*.png"):
            f.rename(out / f"p{int(f.stem.split('-')[1]):03d}.png")
    else:
        for p in pages:
            doc[p - 1].get_pixmap(dpi=dpi).save(str(out / f"p{p:03d}.png"))


def analyse(text, n_images):
    lines = text.splitlines()
    flags = []
    if n_images:
        flags.append("raster image")
    if NUMBERED_EQ_RE.search(text):
        flags.append("numbered equation")
    elif sum(1 for l in lines if MATH_HINT_RE.search(l)) >= 3:
        flags.append("maths")
    if LOSSY_RE.search(text):
        flags.append("lossy glyphs")
    if TABLE_RE.search(text):
        flags.append("table")
    if FIGURE_RE.search(text):
        flags.append("figure caption")
    if sum(1 for l in lines if CODE_LINE_RE.match(l)) >= 6:
        flags.append("code listing")
    return flags


def headings(full):
    seen, out = set(), []
    for m in HEADING_RE.finditer(full):
        num, title = m.group(1), m.group(2).strip()
        if (num, title) in seen or len(title.split()) > 12 or title.endswith((".", ",")):
            continue
        if title.startswith(("Chapter ", "CHAPTER ")) or "." not in num and int(num) > 99:   # running heads
            continue
        seen.add((num, title))
        out.append(f"{num} {title}")
    for m in CAPS_HEADING_RE.finditer(full):
        t = m.group(1).strip()
        if t not in seen and len(t.split()) <= 8:
            seen.add(t)
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, default=Path("extract"))
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--all-pages", action="store_true", help="render every page, not just flagged ones")
    ap.add_argument("--pages", help="render ONLY these pages into --out/pages and do nothing else, "
                                    "e.g. --pages 4,5,9-11 --dpi 300 --out extract-hi")
    args = ap.parse_args()
    pdf, out = args.pdf, args.out
    if not pdf.exists():
        sys.exit(f"no such file: {pdf}")
    out.mkdir(parents=True, exist_ok=True)
    if not args.pages:
        stamp(out.parent, "started")           # the run's clock: <outdir>/run.log

    doc = None
    if not (have("pdftotext") and have("pdfimages") and have("pdftoppm")):
        import fitz
        doc = fitz.open(str(pdf))

    if args.pages:
        wanted = set()
        for part in args.pages.split(","):
            a, _, b = part.partition("-")
            wanted.update(range(int(a), int(b or a) + 1))
        render_pages(pdf, doc, sorted(wanted), out / "pages", args.dpi)
        print(f"rendered pages {sorted(wanted)} at {args.dpi} dpi into {out / 'pages'}")
        return

    pages = page_texts(pdf, doc)
    full = "\n\f\n".join(pages)
    (out / "text.txt").write_text(full)
    heads = headings(full)
    (out / "outline.txt").write_text("\n".join(heads) + "\n")

    images = extract_images(pdf, doc, out / "images")
    per_page = defaultdict(int)
    for _, p, w, h in images:
        if w >= 80 and h >= 80:
            per_page[p] += 1

    flags = {p: analyse(t, per_page[p]) for p, t in enumerate(pages, 1)}
    to_render = [p for p in flags if args.all_pages or flags[p]]
    render_pages(pdf, doc, to_render, out / "pages", args.dpi)

    by_flag = defaultdict(list)
    for p, fl in flags.items():
        for f in fl:
            by_flag[f].append(p)
    fig_refs = sorted(set(FIGURE_RE.findall(full)), key=lambda s: [int(x) for x in s.split(".")])
    tab_refs = sorted(set(TABLE_RE.findall(full)), key=lambda s: [int(x) for x in s.split(".")])
    n_eq = len(NUMBERED_EQ_RE.findall(full))

    inv = [f"# Extraction inventory — {pdf.name}", "",
           f"- pages: {len(pages)}; renders in `pages/`: {len(to_render)}",
           f"- heading candidates in `outline.txt`: {len(heads)} — heuristic; unnumbered or indented headings are often missed, so confirm and hand-correct before writing plan.md",
           f"- raster images in `images/`: {len(images)}",
           f"- numbered equations in text: {n_eq} (transcribe from renders, not text)",
           f"- figure captions: {', '.join(fig_refs) or 'none'}",
           f"- table captions: {', '.join(tab_refs) or 'none'}",
           "", "## Pages by flag", ""]
    inv += [f"- **{k}**: {v}" for k, v in sorted(by_flag.items())] or ["- (nothing flagged)"]
    inv += ["", "## Heading candidates (heuristic; also in outline.txt)", ""]
    inv += [f"- {h}" for h in heads] or ["- (none matched; read text.txt for the section tree)"]
    if images:
        inv += ["", "## Images (sizes only — small or wide-and-short ones are often cartoons/decoration)", "",
                "| file | page | size |", "|---|---|---|"]
        inv += [f"| images/{f.name} | {p} | {w}×{h} |" for f, p, w, h in images]
    (out / "inventory.md").write_text("\n".join(inv) + "\n")
    stamp(out.parent, "extracted")

    print(f"{pdf.name}: {len(pages)} pages, {len(images)} images, {len(to_render)} renders, "
          f"{n_eq} numbered eqs, {len(heads)} heading candidates"
          + (f"; LOSSY GLYPHS on pages {by_flag['lossy glyphs']}" if by_flag.get("lossy glyphs") else ""))


if __name__ == "__main__":
    main()
