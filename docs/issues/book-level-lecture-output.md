---
status: done
type: bug
---

Chapter PDFs in individual folders previously led to nested per-chapter lecture
directories. The reference-vault convention groups every chapter's lecture under
the book's shared `lectures/` directory.

The skill now defines `<book-dir>/lectures/<chapter-slug>/` before any files are
created, explains how to identify the book directory, and shows the Function
objects PDF-to-lecture mapping. All build and revision commands use that output
directory. Task output folders may link to the canonical bundle. Existing slugs
and legacy locations are checked before treating a lecture as absent. The README
links to the same rule.

Verified the live skill symlink resolves to this file and reviewed the scripts:
they accept output paths rather than deriving the book location themselves.

Validation: the skill format validator and whitespace checks pass. The existing
frontmatter description was condensed from 1,182 to 982 characters while
preserving its invocation scope and lecture-quizzing guidance.
