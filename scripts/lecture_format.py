"""
The script.md format and the output layout, in one place; every script
imports this so they cannot disagree. The human-readable description is
references/narration-craft.md, "Script format".
"""

import re
import subprocess
from datetime import datetime

SEP = "\n\n"                                   # paragraph separator in the text sent to the engine
MATH_GLYPHS = "∞⌋⌊∧∨∑∏∫√∂∇≠≤≥≈→↦⊗⊕½¼¾²³⁻∈∀∃"   # what "maths in prose" looks like

PART_RE = re.compile(r"^##\s*part:\s*(\S+)\s*$", re.M)
BEAT_RE = re.compile(r"<!--\s*beat:\s*(\S+)((?:\s*\|[^>]*?)*)\s*-->")
MARK_RE = re.compile(r"<!--\s*mark:\s*(\S+?)\s*((?:\|[^>]*?)?)\s*-->")
FRAME_RE = re.compile(r"\|\s*frame\s+(\d+)")
SPOKEN_RE = re.compile(r"<!--\s*spoken:\s*(.*?)-->", re.S)
PRONOUNCE_RE = re.compile(r"<!--\s*pronounce:\s*(.*?)-->", re.S)
OUTLINE_RE = re.compile(r"<!--\s*outline\s*\n(.*?)-->", re.S)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
PAUSE_RE = re.compile(r"<!--\s*pause\s+([\d.]+)\s*s?\s*-->")
NON_PAUSE_COMMENT_RE = re.compile(r"<!--(?!\s*pause\b).*?-->", re.S)   # what leaves prose before it is spoken
BREAK_RE = re.compile(r'<break time="([\d.]+)s" />')                  # what a pause becomes in the engine's text
PAUSE_MAX_S = 3                                                        # longer pauses are cut to this
ASK_RE = re.compile(r"<!--\s*ask\s*-->")
PROSE_START_RE = re.compile(r"""^\s*[\w"'“‘(]""")


# ---- output layout ---------------------------------------------------------

def audio_path(out, part):
    return out / "audio" / f"{part}.mp3"


def cue_path(out, part):
    return out / "cues" / f"{part}.json"


def align_path(out, part):
    return out / "cues" / f"{part}.align.json"


def text_path(out, part):
    """Exactly what the engine was given; --recue refuses a part whose words changed."""
    return out / "audio" / f"{part}.txt"


def cues_js_path(out):
    return out / "cues" / "cues.js"


# the run's phases, in order; each is stamped when it finishes (scripts/stamp.py)
PHASES = ["read", "plan", "slides", "script", "review", "record", "open"]
NOTE = {"read": "extract, then the chapter and its figures",
        "plan": "the teaching decisions", "slides": "frames, render, screenshots",
        "script": "the words, and the lint", "review": "cold read, and the fixes",
        "record": "audio and cues", "open": ""}


def stamp(out, what, detail=""):
    """Append one line to <out>/run.log. extract.py opens the run with "started";
    each phase is stamped as it finishes; open.py closes it and prints the summary."""
    out.mkdir(parents=True, exist_ok=True)
    with (out / "run.log").open("a") as f:
        f.write(f"{datetime.now().replace(microsecond=0).isoformat()} {what}"
                + (f" | {detail}" if detail else "") + "\n")


def _mmss(seconds):
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def run_summary(out):
    """Every phase since the last "started", in order, with its duration and the
    total from the chapter going in to the page opening."""
    log = out / "run.log"
    if not log.exists():
        return "no run.log"
    rows = []
    for line in log.read_text().splitlines():
        t, _, rest = line.partition(" ")
        what, _, detail = rest.partition(" | ")
        if what:
            rows.append((datetime.fromisoformat(t), what.strip(), detail.strip()))
    starts = [i for i, r in enumerate(rows) if r[1] == "started"]
    if not starts:
        return "no 'started' stamp in run.log"
    run = rows[starts[-1]:]
    out_lines = []
    for (t0, _, _), (t1, what, detail) in zip(run, run[1:]):
        note = detail or NOTE.get(what, "")
        out_lines.append(f"  {what:<8} {_mmss((t1 - t0).total_seconds()):>6}   {note}")
    total = (run[-1][0] - run[0][0]).total_seconds()
    out_lines.append(f"  {'─' * 8} {'─' * 6}")
    out_lines.append(f"  {'total':<8} {_mmss(total):>6}   chapter in, lecture open")
    return "\n".join(out_lines)


def para_offsets(paragraphs):
    """Char offset of each paragraph in SEP.join(paragraphs)."""
    offs, pos = [], 0
    for p in paragraphs:
        offs.append(pos)
        pos += len(p) + len(SEP)
    return offs


# ---- parsing ----------------------------------------------------------------

def parse_parts(text):
    """-> (header, {part key: body}) in document order."""
    marks = [(m.group(1), m.start(), m.end()) for m in PART_RE.finditer(text)]
    if not marks:
        raise SystemExit("No '## part: <key>' headings found in the script.")
    header = text[:marks[0][1]]
    parts = {}
    for i, (key, _, end) in enumerate(marks):
        stop = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        parts[key] = text[end:stop]
    return header, parts


def _frame(opts):
    """The '| frame N' option of a beat or mark comment, or None."""
    fr = FRAME_RE.search(opts or "")
    return int(fr.group(1)) if fr else None


def parse_beats(body):
    """-> [(beat, raw text that follows it)]; the first entry's beat may be None.
    beat = {"id", "frame": int|None}."""
    pieces, pending, cursor = [], None, 0
    for m in BEAT_RE.finditer(body):
        pieces.append((pending, body[cursor:m.start()]))
        pending = {"id": m.group(1), "frame": _frame(m.group(2))}
        cursor = m.end()
    pieces.append((pending, body[cursor:]))
    return pieces


def marks_in(block):
    """Marks inside a prose block, in order: [{"id", "frame": int|None, "pos": char
    index in the raw block where the mark's comment starts}]. The mark belongs to
    the first word after it."""
    return [{"id": m.group(1), "frame": _frame(m.group(2)), "pos": m.start()} for m in MARK_RE.finditer(block)]


def blocks(raw):
    """Paragraph-level blocks (a spoken form sits inside its display block's paragraph)."""
    return [b for b in re.split(r"\n\s*\n", raw) if b.strip()]


def is_display_block(block):
    """narration-craft.md, "Display blocks and spoken forms"."""
    return not PROSE_START_RE.match(COMMENT_RE.sub("", block))


# ---- prose -> what the engine says ----------------------------------------

def prose_text(block):
    """A prose block without its comments (pauses stay), markdown emphasis or link syntax."""
    s = NON_PAUSE_COMMENT_RE.sub("", block)
    s = re.sub(r"[*_`]+", "", s)
    return re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)


def spoken_text(text, rules):
    """Prose or a spoken form -> (what the engine gets, what the reader sees).
    Pauses become <break> tags for the engine and vanish for the reader;
    pronunciation respellings apply to the engine's copy only."""
    shown = " ".join(PAUSE_RE.sub(" ", text).split())
    spoken = PAUSE_RE.sub(lambda p: f' <break time="{min(float(p.group(1)), PAUSE_MAX_S):g}s" /> ', text)
    spoken = " ".join(spoken.split())
    for rx, say in rules:
        spoken = rx.sub(say, spoken)
    return spoken, shown


def walk(body):
    """The one reading of a part's body, shared by the builder and the linter:
    -> [(beat, items)] where each item is
         ("ask",)                       the audio stops after the block before it
         ("display", block, spoken)     spoken is the <!-- spoken --> text or None
         ("prose", block)               marks, pauses and other comments still inside"""
    out = []
    for beat, raw in parse_beats(body):
        items = []
        for b in blocks(raw):
            if ASK_RE.search(b):
                b = ASK_RE.sub("", b)
                if b.strip():                      # marker on the prompt's own block
                    items.append(("prose", b))
                items.append(("ask",))
                continue
            sm = SPOKEN_RE.search(b)
            if sm:
                items.append(("display", b, " ".join(sm.group(1).split())))   # an explicit spoken form wins
            elif is_display_block(b):
                items.append(("display", b, None))
            else:
                items.append(("prose", b))
        out.append((beat, items))
    return out


def parse_pronounce(header):
    """-> [(word regex, respelling)]"""
    rules = []
    for m in PRONOUNCE_RE.finditer(header):
        for item in re.split(r"[;\n]", m.group(1)):
            if "=" in item:
                word, say = (s.strip() for s in item.split("=", 1))
                if word and say:
                    rules.append((re.compile(r"\b" + re.escape(word) + r"\b"), say))
    return rules


def parse_outline(header):
    """-> [(section id, title, target)] where target is a part key or
    'skip[: reason]'."""
    out = []
    for m in OUTLINE_RE.finditer(header):
        for line in m.group(1).splitlines():
            if "->" not in line:
                continue
            left, target = (s.strip() for s in line.rsplit("->", 1))
            sec, _, title = left.partition(" ")
            out.append((sec, title.strip(), target))
    return out


# ---- audio tools ------------------------------------------------------------

def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def duration_of(path):
    """Seconds of audio in an mp3, or None."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None
