# Contributing journal profiles

1. Use official journal/publisher sources and record owner, URL, retrieval time, locator, hash, and
   minimal evidence excerpt. Do not redistribute full pages without permission.
2. Add or update the pinned publisher → journal → article-type profile chain. Use a new semantic
   profile version; never mutate a released version in place.
3. Mark unavailable facts `UNKNOWN`, ambiguity `PARTIAL`, and unresolved authoritative disagreement
   `CONFLICTED`. Do not infer a missing value from another journal or model memory.
4. `VERIFIED` means a human reviewed the official evidence, scope, value/operator, applicability,
   and provenance, and deterministic validation passes. Agent-generated profiles remain `DRAFT`.
5. Add synthetic/open fixtures, profile resolution/audit tests, expected conflicts, and update
   `journal_profiles/registry.yaml` with the canonical JSON SHA-256 hash and verification date.
   Canonical JSON uses sorted keys, UTF-8, no insignificant whitespace, and preserved Unicode
   (`sha256-canonical-json-v1`), so provenance checks are independent of line endings.

Evidence licensing follows `EVIDENCE_AND_LICENSING_POLICY.md`. Profile status is scientific
metadata, not a marketing label.
