#!/usr/bin/env python3
"""
What the built page actually offers, per part and per frame:

    page_index.py lecture.html            -> JSON on stdout
    page_index.py lecture.html --text     -> readable dump of every frame (frames.txt)

The page is the authority on how many frames a part has and what ids its
drawings carry (sync-architecture.md, "Marks"); --text is what the script is
written from (SKILL.md step 4).

Needs chromium (the same binary step 3 screenshots with).
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROBE = r"""
(function () {
  function go(part, f) {                       // the page listens for hashchange; drive it that way
    location.hash = '#' + part + ':' + f;
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  }
  if (!window.__lecture) {            // createLecture never finished: say so, do not guess
    document.title = 'PAGEINDEXFAILED';
    return;
  }
  var out = {};
  var parts = document.querySelectorAll('[data-part]');
  for (var i = 0; i < parts.length; i++) {
    var key = parts[i].getAttribute('data-part');
    var player = window.__lecture.players[key];
    var n = player ? player.frames : 0;
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
        ids: Array.prototype.map.call(sec.querySelectorAll('[id]'), function (e) { return e.id; }),
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
    """-> {part: [{marks, ids, lines, label, text}, … one per frame]}

    The page is the authority: the frame count comes from the mounted player,
    not from counting furniture, so a page that failed to mount says so
    instead of reporting a plausible one-frame deck."""
    html = Path(html).resolve()
    chromium = next((c for c in ("chromium", "chromium-browser", "google-chrome") if shutil.which(c)), None)
    if not chromium:
        sys.exit("chromium not found: lint needs it to resolve the script's frames and marks against the page")
    page = html.read_text()
    if "PAGEINDEX" not in page:
        page = page.replace("</body>", "<script>setTimeout(function(){" + PROBE + "}, 60);</script></body>")
    probe = html.with_name("." + html.stem + "-pageindex.html")   # beside the original, so every
    probe.write_text(page)                                        # relative path still resolves
    try:
        r = subprocess.run([chromium, "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--virtual-time-budget=4000", "--dump-dom", str(probe)],
                           capture_output=True, text=True, timeout=180)
        if re.search(r"<title>PAGEINDEXFAILED</title>", r.stdout):   # the title, not the probe's own source
            sys.exit(f"{html.name} never mounted: createLecture did not finish, so the page has no "
                     f"frames at all. Open it in a browser and read the console, or run the part's "
                     f"module under node.")
        m = re.search(r"PAGEINDEX(\{.*?\})</title>", r.stdout, re.S)
        if not m:
            sys.exit(f"could not read the page: {(r.stderr or r.stdout)[:300]}")
        return json.loads(m.group(1))
    finally:
        probe.unlink(missing_ok=True)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    data = index(sys.argv[1])
    if "--text" in sys.argv:
        for part, frames in data.items():
            print(f"\n===== part: {part} — {len(frames)} frames")
            for i, f in enumerate(frames):
                print(f"\n--- frame {i}  {f['label']}")
                text, cap = f["text"], 1500
                print(f"    {text[:cap]}" + (f"  … [{len(text) - cap} more characters]" if len(text) > cap else ""))
                if f["marks"]:
                    print(f"    marks: {' '.join(sorted(f['marks']))}")
    else:
        print(json.dumps(data, indent=1))


if __name__ == "__main__":
    main()
