# ADR-006: Typed Model Strategy

Status: Accepted for M2  
Date: 2026-09-29

## Decision

Use frozen, slotted standard-library dataclasses for internal profile, rule, provenance, trace, and
conflict records. Validate untrusted JSON at the boundary with `jsonschema` Draft 2020-12, then run
semantic validators. Use strict mypy for profile modules.

Pydantic (MIT) offers convenient runtime coercion/schema generation but adds coupling and may
silently coerce inputs unless carefully configured. attrs (MIT) is smaller but duplicates features
needed here. Dataclasses minimize runtime surface and keep public JSON Schema authoritative;
`jsonschema` becomes the one M2 runtime dependency.

Schema validation is not sufficient for cycles, provenance chains, freshness, or equal-precedence
conflicts; typed deterministic code handles those. Unknown schema versions and extra fields are
rejected, not coerced.

