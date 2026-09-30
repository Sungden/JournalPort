# RC2-4 flattened DOCX front-matter audit

## Status

**PASS — scoped compatibility fix implemented and validated on 2026-09-30.** The private manuscript
was not read, copied, or committed. Numbered-section parsing, profiles, preservation, and independent
verification behavior were not weakened or changed. No tag or release was created.

## Exact root cause

Some DOCX generators flatten visually separate formatting into one normal BodyText run. The real
structure therefore yielded `AbstractThe outlook ...` from a single non-bold run. RC2-3 intentionally
required a distinct bold first run for inline Abstract recognition, so it could not separate this
flattened token. Title corroboration also remained coupled to finding an Abstract boundary unless
the title was centered, despite the first paragraph carrying a 34-half-point bold size signal and
being followed by author, affiliation, email, and date paragraphs.

## Parser changes

- Added a narrowly gated flattened-prefix splitter for `AbstractBody...`, `Abstract Body...`, and
  `Abstract: Body...`.
- Added direct run-size inspection using Word's half-point `w:sz` value.
- Added an independent title path requiring the first non-empty paragraph, plausible title shape,
  all-bold runs, at least 32 half-points, relative prominence over explicit following sizes, and four
  following front-matter paragraphs with at least two independent affiliation/email/date signals.
- Kept the RC2-3 numbered-heading implementation unchanged.

## Why run-level detection was insufficient

The visual heading boundary was not represented by separate OpenXML runs or explicit bold markup.
Run inspection could see only a single normal run containing both label and body. The fallback must
therefore inspect text, but text alone is insufficiently safe; recognition is allowed only when the
surrounding document structure independently corroborates the interpretation.

## Fallback safeguards

All of the following are required:

- The normalized text starts at position zero with capitalized `Abstract`.
- The next boundary is a colon, whitespace, or an uppercase character for the flattened form.
- The remaining body starts uppercase and contains at least eight words and 50 characters.
- At least four preceding paragraphs occur after the first title candidate, with at least two
  independent affiliation/email/date signals.
- The candidate occurs before the first validated numbered top-level section.
- The immediately following non-empty paragraph is that first numbered section.
- Normal paragraph processing continues, so fields, equations, images, tracked content, citations,
  numbers, and unsupported objects are still inspected.

These gates reject `Abstractly...`, lowercase `Abstract concepts...`, weak/ambiguous front matter,
and similar body paragraphs after section 1.

## Synthetic fixture and before/after

The fixture contains a 34-half-point bold BodyText title, bold authors, bold affiliation, email,
date, one normal BodyText run containing the flattened Abstract and body, then the unchanged bold
numbered sections 1–12 and References.

| Field | Before | After |
|---|---|---|
| `metadata["title"]` | empty when Abstract corroboration failed | `A World Model of the Virtual Cell` |
| `canonical.abstract` | empty for one-run flattened content | one Abstract section with body beginning `The outlook of an AI-driven digital organism...` |
| Main-body headings | sections 1–12 and References | unchanged |
| Missing-title rule | `EVALUATION_ERROR` | unchanged and fail-closed |

## Regression coverage

Tests cover the three accepted flattened forms, `Abstractly`, `Abstract concepts`, weak front matter,
late body occurrence, independent title recovery when Abstract parsing fails, ambiguous bold first
paragraphs, missing-title evaluation, all prior standalone/run-level Abstract cases, and all existing
numbered-section cases.

The realistic flattened fixture was exercised through audit → plan → apply → verify and produced
`VERIFIED_CANDIDATE`. Compliance status remains independent.

Final validation: 190 pytest tests passed; Ruff lint and format checks passed; mypy passed; Python
compileall passed; and `git diff --check` passed.

## Remaining unsupported patterns

Lowercase or unusually punctuated flattened labels, short/telegraphic abstracts below the safety
threshold, missing or reordered front matter, a non-adjacent first body heading, inherited font sizes
without explicit run size, text boxes/floating shapes, and automatic numbering absent from visible
paragraph text remain unclassified or require manual review. No scientific content is inferred for
these cases.
