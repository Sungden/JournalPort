# Safe Transformation Engine

M4 separates planning from execution. `journalport plan` validates manuscript, report, profile, and
artifact hashes and writes a deterministic dry-run plan. `journalport apply` accepts a plan only when
its hash and all bound inputs still match. Original artifacts are immutable and all output paths are
confined beneath a distinct output root.

The supported automatic transformation set is intentionally one operation: lossless artifact copy
with a verified safe output filename. It is deterministic and idempotent. Current real journal
profiles contain no VERIFIED filename transformation rule, so they produce manual actions and an
unchanged candidate copy rather than invented formatting.

Abstract/title shortening, manuscript-length reduction, statement generation, reference/figure
removal, scientific rewriting, section relocation, style regeneration, title-page extraction,
bibliography rendering, line numbering, image conversion, and unknown DOCX/LaTeX edits are currently
unsupported. They are explicit manual/approval or forbidden actions, never silent skips.

Candidates are labelled `TRANSFORMED_CANDIDATE`, never submission-ready. Numeric, equation,
citation, reference, and asset fingerprints receive a preliminary same-process check. This is not
independent verification; M5 remains responsible for reparse, compliance rerun, and acceptance.
