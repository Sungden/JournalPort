# M2 Audit — Journal Profile System

Date: 2026-09-29  
Status: **PASS WITH CONDITIONS**

## Architecture, versioning, and inheritance

The implemented hierarchy is `PublisherProfile -> JournalProfile -> ArticleTypeProfile ->
ResolvedJournalProfile`. Canonical IDs, display names, profile/rule/schema/source-snapshot versions,
and precedence are distinct. JSON files are untrusted inputs; JSON Schema and semantic validation
precede frozen typed-record construction. M2 contains no compliance engine, transformer, crawler,
skill, or UI.

Profiles are immutable by `(profile_id, profile_version)` and every parent pins both values. Source
refresh requires a new source-snapshot/profile version. Resolution walks the explicit graph, detects
cycles, enforces precedence (100 publisher, 200 journal, 300 article type), requires all dependency
pins, and canonicalizes behaviorally relevant data before SHA-256 hashing. ADR-005 is normative.

## Resolution, conflicts, and freshness

Every rule emits candidate and selection provenance in a resolution trace. A changed higher-level
value is valid only with `override_of` and a reason. Equal-precedence disagreement and undeclared
overrides remain unresolved; load order never selects a winner. Duplicate and redundant definitions
are classified separately. Unresolved conflicts make the result `CONFLICTED`.

Profiles store `last_verified_at`, source retrieval times, and configurable freshness windows. The
initial 180-day window is JournalPort policy, not a publisher fact. Stale data stays auditable but
resolves `STALE` and cannot support fully verified submission readiness.

## Provenance and evidence policy

Every VERIFIED rule chains through profile -> source -> evidence. Validation rejects missing or
unknown references, evidence/source mismatch, altered evidence hashes, non-official VERIFIED
sources, and invalid confidence. Confidence is discrete. The evidence policy stores URLs, metadata,
hashes, locators, and minimal factual extracts, not complete publisher pages/templates.
`snapshot_scope` distinguishes `EVIDENCE_EXTRACT` from `FULL_CONTENT`.

## Schema change record

- Issue: the M0 placeholder schema lacked pinned inheritance, per-rule provenance, conflict, and
  freshness contracts.
- Reason: these are required for deterministic, auditable M2 behavior.
- Change: `journal_profile.schema.json` moved to 2.0.0; resolved-profile and conflict-report schemas
  were added; source records declare snapshot scope and whether content is stored.
- Backward compatibility: wire-breaking, explicitly signaled by a schema major version. No released
  profile instances were overwritten.
- Migration impact: v1/unknown files fail closed and require explicit migration; historical schema
  IDs must never be relabeled.

## Typed models, checking, and DOCX carry-over

ADR-006 selects frozen, slotted standard-library dataclasses plus JSON Schema boundary validation;
`jsonschema` is the sole M2 runtime dependency. Strict mypy covers all 10 profile modules without
issues. ADR-007 records configurable DOCX limits for archive bytes, ZIP members, total/per-member
uncompressed bytes, XML bytes/depth, and relationship count. Adversarial tests confirm member-count
and XML-size rejection. This is bounded parsing, not a complete process sandbox.

## Initial profiles and counts

Exactly three journals with one Article type each resolve `PARTIAL` from current official-source
metadata:

| Journal / Article | VERIFIED | PARTIAL | UNKNOWN | CONFLICTED | Resolved hash |
|---|---:|---:|---:|---:|---|
| Nature Communications | 8 | 5 | 3 | 0 | `sha256:dc4e8d69a7ee496fa4364fc763ea5ac125ecb836f42f964d6b34e59eab7f8d23` |
| Nature Computational Science | 11 | 1 | 5 | 0 | `sha256:80a0f658874ad92bbf201bbe8eda4a3014eea7889dcd32dd1a1595a66e9c2464` |
| Nature Machine Intelligence | 11 | 1 | 5 | 0 | `sha256:e574ae7e211dbd79971829b5fef22e6f9eb8d05e6c30b23287b55c9e9aa90dea` |

Resolved counts (publisher rules repeated per journal): 30 VERIFIED, 7 PARTIAL, 13 UNKNOWN, 0
CONFLICTED, 0 STALE. Unique definitions: 24 VERIFIED, 7 PARTIAL, 13 UNKNOWN. Unsupported title
limits, code-availability specifics, conditional ethics/consent, title pages, and separate-file
requirements remain explicit UNKNOWN where applicable. `profile_reports/` contains per-journal
source inventories, verification reports, resolution traces, and conflict reports.

## Metrics and tests

- Profile Schema Validation Rate: 7/7 = 100%.
- Resolution Determinism Rate: 3/3 golden profiles = 100%.
- Provenance Completeness: 24/24 unique VERIFIED definitions = 100% (30/30 resolved instances).
- Conflict Detection Rate: 2/2 labeled classes = 100% (equal precedence, invalid override).
- Cycle Detection Rate: 1/1 labeled cycle = 100%.
- Invalid Profile Rejection Rate: 8/8 = 100% (missing provenance, unknown source, altered evidence,
  schema mismatch, oversized input, duplicate rule, inflated status, executable extension).
- Hash stability: 3/3 committed trace hashes equal fresh canonical hashes.
- Final suite: 34 tests plus 16 schema subtests passed; ruff, strict mypy, schema validation, and
  compileall passed.

Adversarial coverage also includes three-layer override, missing pins, stale status, publisher/
journal collision, structured conflict output, duplicate rules, and DOCX resource exhaustion.

## Remaining risks / conditions

The profiles are intentionally incomplete. URLs can change, minimal extracts are not immutable
full-page archives, and publisher terms may limit stronger snapshots. Conditional code, ethics,
consent, title-page, and packaging rules need focused official-source refreshes. There is no signed
evidence registry or long-lived migration corpus. DOCX requires process isolation before exposed
service use. M0/M1 conditions remain inherited.

## Recommended M3 plan

Build a deterministic, read-only manuscript-versus-resolved-profile layer consuming the M1 model
and an explicitly pinned M2 hash. Define finding schemas and operator semantics first; make UNKNOWN,
CONFLICTED, and STALE fail closed for readiness claims; keep verification independent from later
transformation; add golden findings for exactly these profiles; and never auto-edit authorial or
scientific content without explicit approval.
