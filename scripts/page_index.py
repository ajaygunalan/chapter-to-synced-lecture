#!/usr/bin/env python3
"""
What the built page actually offers, per part and per frame:

    page_index.py lecture.html            -> JSON on stdout
    page_index.py lecture.html --text     -> readable dump of every frame (frames.txt)

The page is the authority on how many frames a part has and what ids its
drawings carry, because both are produced by the page's own code at run
time. lint.py resolves every frame number and mark id in script.md against
this; the --text dump is what the script is written from (SKILL.md step 4),
so the narration describes the run the slides actually computed.

Needs chromium (the same binary step 3 screenshots with).
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROBE = r"""
(function () {
  function go(part, f) {                       // the page listens for hashchange; drive it that way
    location.hash = '#' + part + ':' + f;
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  }
  var out = {};
  var parts = document.querySelectorAll('[data-part]');
  for (var i = 0; i < parts.length; i++) {
    var key = parts[i].getAttribute('data-part');
    var n = parts[i].querySelectorAll('.ribbon .tick').length || 1;
    var frames = [];
    for (var f = 0; f < n; f++) {
      go(key, f);
      var sec = document.querySelector('[data-part="' + key + '"]');
      var ids = {}, m = sec.querySelectorAll('[data-mark]');
      for (var j = 0; j < m.length; j++) ids[m[j].getAttribute('data-mark')] = 1;
      var label = sec.querySelector('.counter');
      var slide = sec.querySelector('.slide'), own = '';
      if (slide) {                                  // the page's drawing, without the player's furniture
        var clone = slide.cloneNode(true), junk = clone.querySelectorAll('.frame-no, .fs-btn');
        for (var q = 0; q < junk.length; q++) junk[q].remove();
        own = clone.textContent;
      } else own = sec.textContent;
      frames.push({
        marks: Object.keys(ids),
        rows: sec.querySelectorAll('.ladder > div').length,
        lines: sec.querySelectorAll('pre.code .line').length,
        label: label ? label.textContent : '',
        text: own.replace(/\s+/g, ' ').trim()
      });
    }
    out[key] = frames;
  }
  document.title = 'PAGEINDEX' + JSON.stringify(out);
})();
"""


def index(html):
    """-> {part: [{marks, rows, lines, label, text}, … one per frame]}"""
    html = Path(html).resolve()
    chromium = next((c for c in ("chromium", "chromium-browser", "google-chrome") if shutil.which(c)), None)
    if not chromium:
        sys.exit("chromium not found: lint needs it to resolve the script's frames and marks against the page")
    page = html.read_text()
    if "PAGEINDEX" not in page:
        page = page.replace("</body>", "<script>setTimeout(function(){" + PROBE + "}, 60);</script></body>")
    tmp = Path(tempfile.mkdtemp(prefix="pageindex-"))
    probe = tmp / html.name
    probe.write_text(page)
    for extra in ("cues",):                      # the probe page loads cues/cues.js relative to itself
        if (html.parent / extra).exists():
            (tmp / extra).symlink_to(html.parent / extra)
    try:
        r = subprocess.run([chromium, "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--virtual-time-budget=4000", "--dump-dom", str(probe)],
                           capture_output=True, text=True, timeout=180)
        m = re.search(r"PAGEINDEX(\{.*?\})</title>", r.stdout, re.S)
        if not m:
            sys.exit(f"could not read the page: {(r.stderr or r.stdout)[:300]}")
        return json.loads(m.group(1))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    data = index(sys.argv[1])
    if "--text" in sys.argv:
        for part, frames in data.items():
            print(f"\n===== part: {part} — {len(frames)} frames")
            for i, f in enumerate(frames):
                print(f"\n--- frame {i}  {f['label']}")
                print(f"    {f['text'][:1500]}")
                if f["marks"]:
                    print(f"    marks: {' '.join(sorted(f['marks']))}")
    else:
        print(json.dumps(data, indent=1))


if __name__ == "__main__":
    main()
