# ADR-001: Stable Object Identifiers

Status: Accepted for M1  
Date: 2026-09-29

## Decision

IDs use `<type-prefix>_<first-16-hex-of-SHA-256>` with a deterministic collision suffix. The digest
input is object type, a format-specific stable source anchor, and a normalized content fingerprint.
Anchors are DOCX part plus body/XML index or relationship ID, and LaTeX normalized source path plus
character/line origin. Supported prefixes cover document, section, subsection, paragraph, figure,
figure legend, table, table legend, equation, citation, reference, footnote, endnote, supplement,
author, affiliation, and unsupported content.

Random UUIDs are forbidden by default. IDs are stable when content and its source anchor are
unchanged, unique within one parse, readable by type, and reproducible. Moving an object may change
its ID; future cross-version matching must use content fingerprints in addition to IDs. Identical
objects at the same anchor receive an ordered `.2`, `.3` suffix, never randomness.

## Consequences

Position is not the sole identity input, but formats do not provide universal persistent IDs.
Editing earlier DOCX body elements or LaTeX source may move anchors and therefore IDs. This is
preferable to pretending content-only IDs distinguish duplicates. Tests cover determinism,
uniqueness, and content sensitivity.

