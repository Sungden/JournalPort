# Changelog

All notable changes will follow Keep a Changelog and semantic versioning.

## [Unreleased]

### Fixed

- Compare unsupported DOCX content by path-independent semantic fragment identity, while retaining
  strict detection of additions, removals, mutations, type/severity changes, and multiplicity.
- Recognize common styled, plain, and bold Abstract headings with front matter and numbered body
  headings without treating arbitrary body mentions as headings.
- Recover conservative first-paragraph titles from common DOCX styling/front matter, and fail with
  an evaluation error when a title rule has no non-empty canonical title instead of counting zero
  words as a passing value.
- Parse distinctly bold inline `Abstract` lead-ins without dropping their same-paragraph body, and
  recognize short, fully bold N/N.N section headings only when their numbering is sequentially
  plausible.
- Report pending/manual action postconditions as not applicable instead of multiplying an unrelated
  global preservation failure across every unexecuted action.

### Changed

- Prepare package version `0.1.0rc2`; no tag or release has been created.

## [0.1.0rc1] - 2026-09-29

### Added

- Deterministic DOCX/LaTeX parsing, profile resolution, compliance audit, safe transformation,
  independent verification, and submission-package pipeline.
- Provenance-backed guideline extraction into immutable draft profiles and review queues.
- Four versioned Agent Skills, stable CLI/Python façade, 30 JSON Schemas, bundled profile registry,
  reproducible benchmark command, and release/security/contribution documentation.

### Changed

- Version now comes from one package source; wheel installations include schemas and profiles.
- Public CLI has documented structured artifacts and exit-code semantics.

### Security

- Fail-closed unknowns, parser resource/traversal controls, prompt-injection resistance, approval
  gates, hash binding, independent verification, and local-first manuscript handling.

### Known limitations

- Three Article profiles are `PARTIAL`; safe transformation support is intentionally narrow.
- No submission automation, UI, MCP adapter, PyPI publication, DOI, or live-provider benchmark.

