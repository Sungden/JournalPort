# Changelog

All notable changes will follow Keep a Changelog and semantic versioning.

## [Unreleased]

### Removed

- Remove the completed M2.5 batch migration script and its unused filesystem writer.
  Preserve the pure migration function used by reproducibility tests, semantic decisions,
  migration report and immutable profile snapshots.

### Added

- Add opt-in Nature-oriented model rewriting with DOCX/Markdown/text/LaTeX/text-PDF input,
  source-bound coverage and numeric/citation checks, separate semantic review, bounded repair,
  HTTP or authenticated Codex backends, draft DOCX/Markdown output and render diagnostics.
- Add a reviewed content-preserving IEEE scientific structure migration and synthetic live-model example.


### Added

- Add pinned Nature Communications Article 1.3.0 document targets, inherited Nature Portfolio
  declaration targets, stage-aware full-format planning, structural/layout DOCX operations,
  numeric citation linkage, explicit supplementary artifacts, render diagnostics and coverage reports.
- Add five public synthetic NC corpus generators and installed DOCX workflow validation.
- Report NC_DOCX_NOT_CLOSED while reference rendering, uncertain profile details and rendering
  validation remain unresolved; packages retain manual-review status.

### Fixed

- Preserve extraction-only DOCX candidates byte-for-byte and preserve namespace prefixes in
  full-format structural execution; keep new ZIP artifact timestamps deterministic.
- Bind packaging to verified candidate/artifact hashes and reject unsafe artifact paths.

## [1.0.0rc1] - 2026-09-30

### Added

- Freeze the v1 deterministic Core, M10/M12 transformation boundary, operation-aware verification,
  stage-aware journal profiles, portable journal-transfer Skill, and release documentation.
- Add Nature Communications Article profile 1.2.0 with conservative REVISION-stage targets.

### Fixed

- Resolve article profiles through their immutable parent-version pins so mixed parent versions work
  from an installed CLI.
- Fail closed when a VERIFIED formatting target exceeds the executor's actual target semantics.

### Security

- Exclude real manuscripts, sessions, approval payloads, disclosure ledgers, and private runtime
  outputs from distribution artifacts.

### Added

- Add the M11 Codex-native transfer skill, resumable local transfer sessions, proposal and disclosure
  contracts, deterministic scientific-token diff safeguards, privacy minimization, and focused
  abstract/declaration/cover-letter/verification/package workflows.
- Add the confidential local DOCX transformation executor with payload-bound approvals, surgical
  abstract replacement, administrative-section insertion/heading normalization, atomic output,
  authorized-delta verification, and an offline CLI approval workflow.
- Add a confidential-manuscript threat model and network-disabled, log-redaction, source-preservation,
  cleanup, independent-verification, and package-pipeline regression coverage.

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
- Support single-run flattened `Abstract` front matter only when exact token boundaries, substantial
  body text, preceding author/contact structure, and the following first numbered section all agree;
  recognize independently corroborated large-font bold BodyText titles.
- Report pending/manual action postconditions as not applicable instead of multiplying an unrelated
  global preservation failure across every unexecuted action.

### Changed

- Evaluate target article type from resolved submission context and cover-letter presence at the
  package artifact layer instead of requiring visible manuscript metadata.
- Historical development state prepared package version `0.1.0rc3` without a tag or release.

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

