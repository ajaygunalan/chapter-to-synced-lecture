# Quizzing

A full chapter quiz is a diagnostic instrument that teaches while it measures
— and its product is the work list for the next revision of the lecture. It
runs only when the listener asks for it, inside a revision session, and its misses go
into `notes.md` like any other listening feedback: what the learner missed
is what the lecture gets edited to fix.

## Brief prerequisite checks

During teaching, a short check can resolve uncertainty about a prerequisite
before the explanation depends on it. Use existing conversation evidence:
skip what the learner has demonstrated, refresh an explicitly forgotten
construct first, and treat untested knowledge as unknown rather than weak.
Ask about the prerequisite in isolation, with only familiar surrounding
syntax and all relevant code or data in the message. A plain meaning or role
question can be enough; do not require a combined deduction/capture/ownership
trace to discover whether a type placeholder is understood.

These checks do not start the full-syllabus quiz below, require code files,
or require an escalation sequence. Respond to the specific gap, then connect
the refreshed idea to the pending topic. If the learner skips a check, supply
a concise bridge and continue; do not mark the topic mastered.

An authorized build or rebuild proceeds without an unsolicited live quiz.
Author the appropriate refresher and optional pause into the lesson; wait
for chat answers only when that interaction is requested. The full quiz's
coverage, interleaving, and difficulty guidance below does not govern these
bounded prerequisite checks.

## High level

The tutor keeps two maps: the **syllabus map** — every concept the material
carries — and the **learner map** — which of those concepts are
demonstrated, shaky, or untouched, updated after every answer. Each
question is aimed where the maps disagree: at the most important concept
not yet demonstrated. It is framed as a decision in a concrete situation,
with all needed data inside the question itself, so answering requires
retrieval and judgment, never recognition or memory of a slide. The learner
commits first; the tutor returns an immediate one-line verdict, teaches
only into the actual gap, and adapts — escalate on success, decompose on
failure, re-queue misses later, retire what is proven. Difficulty steers
toward "mostly right, but working for it", topics are interleaved so
confusable ideas collide, and the session ends when the syllabus map is
covered — not when a question count runs out.

## Framing a question

1. One concept per question, stated completely in the stem, with its own
   diagram or data included. Never bundle two asks; never require recalling
   an earlier visual.
2. Frame every question as a decision — predict, trace, choose, debug, or
   distrust: a situation where the concept changes what the learner would
   do. Never "what is X".
3. Hinge design: every plausible wrong answer must diagnose one specific
   misconception, and the right answer must not be reachable by wrong
   reasoning.
4. The source material's own vocabulary; no invented metaphors, no trick
   wording, no trivia.

## Adapting from answers

5. The learner commits before any hint or partial reveal.
6. Verdict immediately, in one line; teach only into the demonstrated gap;
   then move.
7. On a right answer: escalate — new context, an edge case, or "now break
   it". Periodically probe the reasoning behind a right answer.
8. On a wrong answer: never repeat the question; decompose to the smallest
   sub-question the learner can answer and rebuild upward; don't advance
   past the concept until it's demonstrated.
9. Steer toward roughly 85% success: a streak of clean answers means
   escalate; consecutive misses mean step down.
10. Re-queue every miss later in the session, in a different guise, until
    answered cold; retire a concept once demonstrated — including anything
    the learner already proved unprompted in conversation.

## Covering the syllabus

11. Before the first question, draw up the concept checklist for the
    material; draw every question against it; the session ends only when
    every item is demonstrated, taught, or explicitly deferred.
12. Interleave confusable neighbors; never ask consecutive questions on one
    topic.
13. End with one synthesis question spanning the whole material — a fresh
    problem where the learner must choose which tool applies and say why.
14. The misses are the output: they become the work list, in `notes.md`,
    for revising the lecture.

## Conduct

15. Plain chat, strictly one question per message, never an option-picker
    UI (never the AskUserQuestion tool).
16. Smoothness is not the goal: effortful and slightly uncomfortable
    retains more than fluent and fast; in-session fluency is not evidence
    of learning. If the listener caps the question count, honor the cap and
    spend the questions on the highest-value uncovered concepts.

## Sources

- Retrieval practice / testing effect — Roediger & Karpicke; Karpicke's
  review: https://files.eric.ed.gov/fulltext/ED599273.pdf
- Desirable difficulties — Bjork & Bjork:
  https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-introducing-desirable-difficulties-into-practice-and-instruction-bjork-and-bjork.pdf
- ~85% optimal difficulty — Wilson et al., Nature Communications 2019:
  https://www.nature.com/articles/s41467-019-12552-4
- Hinge questions — Dylan Wiliam:
  https://www.ascd.org/el/articles/designing-great-hinge-questions
- Item-writing rules — NBME guide:
  https://www.nbme.org/sites/default/files/2021-02/NBME_Item%20Writing%20Guide_R_6.pdf
  and Haladyna 2002:
  https://cmapspublic3.ihmc.us/rid=1P2XTLCSS-11K09T9-BD5/Haladyna_2002_-Appl_Meas_Educ.pdf
- Bloom's taxonomy (target apply/analyze) — Vanderbilt CFT:
  https://derekbruff.org/vanderbilt-cft-teaching-guides-archive/blooms-taxonomy/
- Socratic probing — Paul & Elder:
  https://www.criticalthinking.org/store/get_file.php?inventories_id=231&inventories_files_id=422
- Mastery / immediate feedback — Bloom's 2-sigma:
  https://en.wikipedia.org/wiki/Bloom%27s_2_sigma_problem
- Interleaving — Rohrer & Taylor via:
  https://my.chartered.college/impact_article/the-application-of-spacing-and-interleaving-approaches-in-the-classroom/
- Successive relearning — Rawson & Dunlosky:
  https://www.researchgate.net/publication/274741632_Practice_tests_spaced_practice_and_successive_relearning_Tips_for_classroom_use_and_for_guiding_students%27_learning

## Quizzing with code files

When the listener asks to be quizzed on code (rather than on prose), each
question ships as a compilable file in `<outdir>/quiz/`, in the language the
listener asked for, and the question itself is asked in the chat.

- **Name by question and version only:** `qNN_v0.cpp` is the code as the
  question presents it; `v1`, `v2`, … are the successive rewrites the reveal
  shows. No topic in the name, and never "original"/"after"/"refactored" —
  the number is the timeline, line 1 of the file is the topic.
- **Every file builds and runs alone** (`g++ -std=c++23 -Wall`); `main`
  prints a small run with the expected values in the output.
- **Line 1 of each file** says the question, the version, the page(s) in the
  book, and `FOCUS: <function names>` — the handful of functions the
  question is about. A chapter example may be a hundred lines; the listener
  must never have to guess which twenty to read.
- **Before the question, in the chat:** the inputs, the outputs and side
  effects, and the data path from one to the other, as a short strip. The
  listener cannot name chunks in code they have not yet run in their head.
- **With the question, in the chat:** the same FOCUS pointer, so the file
  and the chat agree on where to look.
