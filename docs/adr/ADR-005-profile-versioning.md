# ADR-005: Profile Versioning and Reproducibility

Status: Accepted for M2  
Date: 2026-09-29

Four versions remain distinct: `schema_version` governs the wire contract; `profile_version`
identifies an immutable publisher/journal/article-type definition; `source_snapshot_version`
identifies its evidence set; and `resolved_profile_version` identifies the resolver output format.
Rules additionally carry `rule_version`.

Canonical IDs never encode display names. Renaming creates metadata changes or a new ID with an
explicit migration; it never overwrites history. Parent references pin both ID and version. The
registry rejects duplicate `(profile_id, profile_version)` pairs and missing pins. Historical files
remain immutable and may coexist.

Resolved hashing covers effective rules, pinned profiles, trace, conflicts, status, and resolver
metadata. It excludes JSON whitespace, key order, and comments. The same immutable inputs and
software behavior therefore produce the same hash. Source refresh creates a new snapshot/profile
version, never an in-place replacement.

