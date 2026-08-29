#!/usr/bin/env python3
"""
lecture.src.html -> lecture.html: inline the player assets, embed local images,
render the maths. Run again whenever the source changes.

    build_page.py lecture.src.html -o lecture.html

Placeholders in the source:
    {{PLAYER_CSS}}          contents of assets/player.css (put inside <style>)
    {{PLAYER_JS}}           contents of assets/player.js  (put inside <script>); the
                            <script src="cues/cues.js"> tag is inserted before it
    {{IMG:extract/images/img-019-000.png}}   a data: URI for src="…" (path relative to the source file)
"""

import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path

from render_math import cache_path, render_html, report

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
IMG_RE = re.compile(r"\{\{IMG:([^}]+)\}\}")
CUES_TAG = '<script src="cues/cues.js"></script>'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()

    page = args.src.read_text()
    page = re.sub(r"<script>(\s*)\{\{PLAYER_JS\}\}", CUES_TAG + r"\n<script>\1{{PLAYER_JS}}", page, count=1)
    page = page.replace("{{PLAYER_CSS}}", (ASSETS / "player.css").read_text())
    page = page.replace("{{PLAYER_JS}}", (ASSETS / "player.js").read_text())

    def embed(m):
        f = (args.src.parent / m.group(1)).resolve()
        if not f.exists():
            sys.exit(f"image not found: {f}")
        mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()

    page, n_img = IMG_RE.subn(embed, page)
    page, n_math, errors = render_html(page, cache_path(args.out))
    args.out.write_text(page)
    print(f"{args.out}: assets inlined, {n_img} image(s) embedded, {n_math} maths expression(s), {len(page):,} bytes")
    report(errors)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
