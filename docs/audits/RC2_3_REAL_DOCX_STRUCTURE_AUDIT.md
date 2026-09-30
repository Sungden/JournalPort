# RC2-3 real-world DOCX structure audit

## Status

**PASS — narrowly scoped parser fix implemented and locally validated on 2026-09-30.** No private
manuscript was read, copied, or committed. No journal profile, production rule, tag, or release was
changed.

## Exact root causes

1. The parser only recognized Abstract when the complete paragraph text was the heading label. A
   bold `Abstract` run followed by normal abstract text in the same paragraph therefore remained
   ordinary front-matter text.
2. Title corroboration searched only for a whole-paragraph Abstract label. Missing the inline
   boundary also removed the front-matter evidence needed to recognize a bold BodyText title.
3. Unstyled numbered headings were restricted to a small label vocabulary. Real, fully bold
   headings such as `2 Operational Definition` through `11 Toward Virtual Cell Banks and Digital
   Organisms` were consequently treated as prose.

## Parser changes

- Inline Abstract recognition inspects direct paragraph runs. The first non-empty run must be
  distinctly bold and normalize exactly to `Abstract` or `Abstract:`; later content in that same
  paragraph must be non-empty. Only the lead-in is removed, while remaining semantic text continues
  through normal paragraph, field, equation, image, and unsupported-content handling.
- Front-matter discovery treats a structurally valid inline Abstract as a boundary candidate without
  depending on successful standalone-heading parsing. Conservative title inference can therefore
  use the independent sequence of first paragraph, short author/front-matter paragraphs, and the
  later Abstract boundary.
- Generic numbered candidates must be fully bold, at most 20 words and 200 characters, and not end
  as a normal sentence. Top-level numbers must form a continuous sequence starting at 1. N.N
  headings are accepted only under the active N section and in continuous minor order. N maps to
  level 1 and N.N to level 2.

## Synthetic fixture structure

The minimized package contains a bold BodyText title, bold BodyText authors and affiliation,
BodyText emails and date, a bold inline Abstract lead-in plus normal body text, twelve fully bold
BodyText headings from `1 Introduction` through `12 Conclusion`, intervening body paragraphs, and a
bold BodyText References heading. It contains no private manuscript content.

## False-positive safeguards

- `Abstract` must occupy its own first non-empty run, be distinctly bold, have non-empty following
  content, and occur before substantive body sections.
- A sentence merely beginning with the word “Abstract” is not promoted.
- A first bold paragraph without corroborating front matter is not inferred as a title.
- Generic numbered prose without full bold formatting, sentence-like candidates, sequence gaps, and
  orphan/out-of-order subsections are not promoted to headings.
- Missing titles retain the RC2-2 fail-closed `EVALUATION_ERROR` behavior.

## Before and after

| Field | Before | After |
|---|---|---|
| `metadata["title"]` | empty | `A World Model of the Virtual Cell` in the synthetic analogue |
| `canonical.abstract` | empty | one section containing the same-paragraph abstract body |
| Generic numbered body sections | only vocabulary matches such as 1 and 12 | all structurally valid continuous sections 1–12 |
| N.N hierarchy | not generally recognized | preserved as level 2 under the active N section |
| Missing title compliance | `EVALUATION_ERROR` after RC2-2 | unchanged and fail-closed |

## Regression and pipeline results

Tests cover standalone styled/plain/bold Abstract headings, inline bold `Abstract` and `Abstract:`,
front matter, a following numbered section, non-heading Abstract sentences, styled and corroborated
bold titles, ambiguous bold first paragraphs, generic N and N.N headings, normal numbered prose,
sequence gaps, all twelve real-pattern sections, References, and missing-title compliance.

The realistic synthetic DOCX was also exercised through audit → plan → apply → verify and produced
transformation status `VERIFIED_CANDIDATE`; compliance readiness remains an independent result.

Final validation: 183 pytest tests passed; Ruff lint and format checks passed; mypy passed; Python
compileall passed; and `git diff --check` passed.

## Remaining unsupported patterns

Inline labels split across multiple formatted runs, labels inside text boxes or floating shapes,
automatic numbering whose visible number is absent from paragraph text, non-decimal numbering,
out-of-order or intentionally skipped section sequences, and visually prominent formatting inherited
only through complex style hierarchies remain unclassified or require manual review. These cases are
not silently inferred.
