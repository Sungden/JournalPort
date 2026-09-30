# RC2-1 real DOCX verification and Abstract parsing audit

## Status

**PASS — implementation complete; `0.1.0rc2` prepared but not tagged or released.** The private
manuscript was not read, copied, or committed. Reproduction uses only minimized synthetic DOCX
packages.

## Root causes

1. Unsupported-content preservation included `object_id`. DOCX unsupported IDs derive partly from
   source locators, including the filename, so a byte-identical copied candidate could compare
   unequal after an otherwise permitted rename.
2. Every pending/manual action reused the aggregate preservation result as its own postcondition.
   One global preservation failure therefore appeared as many unrelated action failures.
3. DOCX section recognition required a `Heading1`–`Heading9` style. Common manuscripts using an
   exact plain or bold `Abstract` paragraph, followed by an unstyled numbered Introduction, left
   `canonical.abstract` empty.

## Code changes

- `verify/preservation.py` now compares unsupported content as an order-insensitive `Counter` of
  `(object_type, severity, source_fragment_hash, raw_fragment_preserved,
  preservation_possible)`. Object IDs and source locators are excluded. Multiplicity remains part
  of identity, so additions/removals cannot disappear.
- `verify/verifier.py` reports unexecuted pending/manual action postconditions as
  `NOT_APPLICABLE`. Only applied actions claim and verify an actual postcondition. Global
  preservation failures remain independently fail-closed and appear once at their root.
- `manuscript/parser_docx.py` conservatively recognizes exact plain/bold Abstract headings before
  substantive body sections and common numbered section headings. Existing Word Heading styles
  remain supported. Arbitrary body occurrences containing the word “abstract” are not headings.
- Verification implementation version is `1.0.1`; package development version is `0.1.0rc2`.

## Regression fixtures and behavior

The synthetic DOCX builder now covers front matter, styled/plain/bold Abstract headings, numbered
Introduction, a preserved unsupported REF field, and ambiguous non-heading abstract text.

| Scenario | Before | After |
|---|---|---|
| Byte-identical DOCX copied to a different filename with identical unsupported content | false `unsupported_content` failure | `PASS`; candidate verifies |
| Unsupported entries reordered | false failure possible | `PASS` by explicit order-insensitive semantics |
| Unsupported fragment added/removed/modified | fail-closed | `FAIL` |
| Unsupported type or severity changed | fail-closed | `FAIL` |
| Unrelated preservation failure with pending actions | duplicated action failures | one preservation root failure; actions `NOT_APPLICABLE` |
| Styled/plain/bold Abstract after front matter | non-styled forms missed | abstract populated |
| Abstract followed by `1 Introduction` | abstract could absorb later text | numbered body section recognized |
| Body sentence containing “abstract” | not a heading | remains fail-closed/not classified as Abstract |

The complete synthetic audit → plan → apply → verify flow produces `VERIFIED_CANDIDATE` for a
byte-identical renamed DOCX containing path-sensitive unsupported parser IDs. Compliance readiness
remains independent and may still require manual review.

## Safety properties

Unsupported content is not ignored. Raw-fragment hashes, type, severity, preservation flags, and
entry counts must match. Real mutation, deletion, addition, type/severity mutation, or multiplicity
change fails preservation. Tamper checks, manifest reconciliation, compliance deltas, profile
hashing, and source/candidate artifact hashing are unchanged.

## Validation

- Full pytest suite: 168 passed (156 existing plus 12 RC2 regressions)
- Ruff check and format check: passed
- mypy strict configured scope: passed
- compileall and `git diff --check`: passed
- CLI version: `journalport 0.1.0rc2`

## Remaining real-manuscript limitations

Complex floating shapes, text boxes, comments, tracked changes, unknown fields, unconventional
heading systems, and ambiguous mixed formatting remain unsupported or fail closed. Front matter is
not yet semantically decomposed into full author/affiliation/contact fields. Compliance rules marked
PARTIAL/UNKNOWN and missing author artifacts still require human review.

## RC2 readiness

The scoped bugfix is ready for review and hosted CI. No production profile, benchmark baseline,
`v0.1.0rc1` tag, or release asset changed. Creating an rc2 tag/release requires separate approval.
