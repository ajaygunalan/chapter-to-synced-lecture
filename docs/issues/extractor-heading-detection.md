---
status: draft
type: bug
---

# Extractor heading detection is weak on unnumbered chapters

`extract_chapter.py`'s heading heuristic found 0 candidates for Clean Code ch19 (Title-Case
unnumbered headings) and only ~11 of ~20 for Skiena ch6. The inventory is marked heuristic
and the workflow reads `text.txt` in full anyway, so this is not blocking — but a better
heuristic (font-size from pymupdf `get_text("dict")` spans, or PDF outline/bookmarks via
`pdftotext`/`fitz` TOC) would make `inventory.md` a usable outline and let
`check_lecture.py --outline` be generated instead of hand-written.
