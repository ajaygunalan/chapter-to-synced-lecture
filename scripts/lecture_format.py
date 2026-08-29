"""
The script.md format and the output layout, in one place. build_audio.py,
subtitles.py, lint.py and the engines import this so they cannot disagree.
The human-readable description is references/narration-craft.md, "Script
format"; the vocabulary (part, frame, beat, mark, ask) is SKILL.md's.
"""

import re
import shutil
import subprocess

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
    """Paragraph-level blocks. A block that is only a spoken comment is merged
    into the block before it, so the comment may sit after a blank line."""
    out = []
    for b in re.split(r"\n\s*\n", raw):
        if not b.strip():
            continue
        if SPOKEN_RE.fullmatch(b.strip()) and out:
            out[-1] += "\n" + b
        else:
            out.append(b)
    return out


def is_display_block(block):
    """Prose starts with a word character; anything else ($$, ```, |, >, <svg,
    ![, - list) is display-only and needs a spoken form to reach the engine."""
    return not PROSE_START_RE.match(COMMENT_RE.sub("", block))


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


try:
    from mutagen.mp3 import MP3 as _MP3
except ImportError:
    _MP3 = None
_FFPROBE = shutil.which("ffprobe")


def duration_of(path):
    """Seconds of audio in an mp3, or None."""
    if _MP3:
        try:
            return _MP3(str(path)).info.length
        except Exception:
            pass
    if _FFPROBE:
        r = subprocess.run([_FFPROBE, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True)
        try:
            return float(r.stdout.strip())
        except ValueError:
            pass
    return None
