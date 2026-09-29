# Changelog

All notable changes will follow Keep a Changelog and semantic versioning.

## [Unreleased]

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

