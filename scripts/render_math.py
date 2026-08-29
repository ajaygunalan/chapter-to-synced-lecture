#!/usr/bin/env python3
"""
Render $…$ and $$…$$ in an HTML file to MathML with KaTeX, at build time.

The page stays standalone: MathML is native in every current browser, so no
script, stylesheet, or font loads at runtime. Rendered expressions are cached
in <html>.math-cache.json next to the file, so rebuilding a page only costs
the new or changed expressions.

Used by build_page.py. Skips <script>, <style>, <pre>, <code>. Write `\\$` for a literal dollar. Use
\\lt and \\gt instead of < and > inside maths.
Needs node plus KaTeX: `npm i -g katex`, or npx will fetch it on first run.
"""

import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKIP_RE = re.compile(r"(<(script|style|pre|code)\b.*?</\2>)", re.S | re.I)
DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE_RE = re.compile(r"(?<!\\)\$(?!\$)([^$\n]+?)(?<!\\)\$")

NODE_BATCH = r"""
const katex = require(process.argv[1]);
let buf = '';
process.stdin.on('data', d => buf += d);
process.stdin.on('end', () => {
  const out = JSON.parse(buf).map(([tex, display]) => {
    try { return katex.renderToString(tex, {output: 'mathml', displayMode: display, throwOnError: true}); }
    catch (e) { return {error: String(e.message || e)}; }
  });
  process.stdout.write(JSON.stringify(out));
});
"""


def katex_package_dir():
    """Locate the katex package without installing anything into the repo."""
    cli = shutil.which("katex")
    if not cli and shutil.which("npx"):
        r = subprocess.run(["npx", "--yes", "-p", "katex", "sh", "-c", "command -v katex"],
                           capture_output=True, text=True)
        cli = r.stdout.strip() or None
    if not cli:
        sys.exit("need KaTeX: npm i -g katex (or node+npx on PATH)")
    return str(Path(cli).resolve().parent)  # …/node_modules/katex


def tex_of(m):
    """Unescape and trim, but keep a trailing '\\ ' (a TeX space) intact."""
    t = html.unescape(m.group(1)).strip("\n\t ")
    return t + " " if m.group(1).rstrip("\n\t ").endswith("\\") else t


def render_batch(items):
    """items: [(tex, display)] -> [mathml or {'error'}]"""
    if not items:
        return []
    r = subprocess.run(["node", "-e", NODE_BATCH, katex_package_dir()],
                       input=json.dumps(items), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"katex batch failed: {r.stderr[:300]}")
    return json.loads(r.stdout)


def ckey(tex, display):
    return f"{int(display)}|{tex}"


def render_html(src, cache_file):
    """-> (html with $…$ rendered, number of expressions, [(tex, error)])."""
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}

    # split into [prose, skipped, tag, prose, skipped, tag, …]; maths lives in prose segments
    parts = SKIP_RE.split(src)
    found = []   # (tex, display)
    for i in range(0, len(parts), 3):
        for m in DISPLAY_RE.finditer(parts[i]):
            found.append((tex_of(m), True))
        for m in INLINE_RE.finditer(DISPLAY_RE.sub("", parts[i])):
            found.append((tex_of(m), False))
    if not found:
        return src, 0, []

    todo = sorted({(t, d) for t, d in found if ckey(t, d) not in cache})
    for (tex, display), out in zip(todo, render_batch(todo)):
        cache[ckey(tex, display)] = out
    if todo:
        cache_file.write_text(json.dumps(cache, indent=0))

    errors = []

    def sub(display):
        def fn(m):
            tex = tex_of(m)
            out = cache[ckey(tex, display)]
            if isinstance(out, dict):
                errors.append((tex, out["error"]))
                return f'<span class="math-error" title="{html.escape(out["error"])}">{html.escape(tex)}</span>'
            return out
        return fn

    for i in range(0, len(parts), 3):
        parts[i] = DISPLAY_RE.sub(sub(True), parts[i])
        parts[i] = INLINE_RE.sub(sub(False), parts[i]).replace("\\$", "$")
    # parts = [prose, skipped block, tag name, prose, …]; the tag-name groups are not content
    return "".join(x for i, x in enumerate(parts) if i % 3 != 2), len(found), errors


def cache_path(html_path):
    return html_path.with_suffix(html_path.suffix + ".math-cache.json")


def report(errors):
    for tex, err in errors:
        print(f"  ! {tex[:60]!r}: {err[:120]}", file=sys.stderr)
