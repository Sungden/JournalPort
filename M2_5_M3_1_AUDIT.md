# M2.5 / M3.1 Audit — Journal Profile Semantic Migration

Date: 2026-09-29  
Status: **PASS**

## Schema and version changes

Journal profile schema 2.1.0 adds explicit `applicability_mode`, `critical_for_readiness`, and
`evaluation_scope` for every new active rule. Schema 2.0.0 remains loadable for immutable history;
2.1.0 conditionally requires the three fields. Profile versions moved from 1.0.0 to 1.1.0, including
publisher and journal ancestors, while all 1.0.0 files remain unchanged. Default-valued legacy model
fields are omitted from hash canonicalization, preserving historical M2 hashes; explicit 1.1.0
semantics are hash-significant.

Migration is reproducible through `profiles/migration.py`, the reviewed decision manifest, and
`profile_migration_report.json`. The report distinguishes unchanged publisher evidence from each
JournalPort operational decision. No rule status or evidence text/hash was changed.

## Applicability and criticality policies

Applicability is closed to ALWAYS, CONDITIONAL, NOT_APPLICABLE, and UNKNOWN. CONDITIONAL is used only
for evidence-backed Extended Data use and Nature Communications' explicitly qualified section
structure. Code, ethics/consent, title-page, and ambiguous figure-file requirements remain UNKNOWN;
they were not promoted merely to improve coverage.

ADR-010 applies one cross-journal criticality policy. Explicit hard limits, mandatory identity,
required declarations/components/files are critical. Recommendations, permissions, unresolved
applicability, and qualified guidance are non-critical. This is JournalPort policy and is never
represented as publisher wording.

## Scope and executable-semantics audit

Every active rule now explicitly records applicability, criticality, machine-checkability, severity,
autofix class, operator, unit, and evaluation scope. VERIFIED numeric rules are executable only when
the official evidence provides a deterministic scope. Guideline reference limits, Nature
Communications' ideal main-text limit and word-count-dependent display allowance, optional
supplements, section structures not reliably represented by the current canonical model, and
conditional Extended Data are manual-review rules.

The official URLs were re-requested on 2026-09-29. Nature Communications and Nature Computational
Science content confirmed the stored facts. Some Nature pages returned cookie/temporary fetch
failures; no unsupported freshness or evidence-content claim was introduced. Since the stored M2
evidence was retrieved the same day and no material confirmed change was found, evidence hashes and
extracts remain unchanged; source snapshot/profile versions still advance to record the semantic
migration.

## Per-journal results

| Journal / Article | VERIFIED | PARTIAL | UNKNOWN | ALWAYS | CONDITIONAL | UNKNOWN applicability | Machine-checkable | Evaluated | Manual | Critical |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nature Communications | 8 | 5 | 3 | 11 | 1 | 4 | 7 | 7 | 9 | 7 |
| Nature Computational Science | 11 | 1 | 5 | 12 | 1 | 4 | 9 | 8 | 9 | 11 |
| Nature Machine Intelligence | 11 | 1 | 5 | 12 | 1 | 4 | 9 | 8 | 9 | 11 |
| **Total resolved instances** | **30** | **7** | **13** | **35** | **3** | **12** | **25** | **23** | **27** | **29** |

The two machine-checkable but unevaluated rules are UNKNOWN title rules, not VERIFIED rules.
Therefore:

`Verified Machine-Checkable Evaluation Coverage = 23 / 23 = 100%`.

Profile completeness remains 30 VERIFIED / 7 PARTIAL / 13 UNKNOWN and is separate from engine
coverage. No conflicts or stale rules are active.

## Real-profile audits

A deliberately compliant canonical synthetic manuscript now produces meaningful results:

- Nature Communications: 7 PASS, 9 UNKNOWN, REQUIRES_MANUAL_REVIEW.
- Nature Computational Science: 8 PASS, 9 UNKNOWN, REQUIRES_MANUAL_REVIEW.
- Nature Machine Intelligence: 8 PASS, 9 UNKNOWN, REQUIRES_MANUAL_REVIEW.

Unsupported evaluator rules: 0. Silent rule skips: 0. UNKNOWN remains explicit. PARTIAL profile
status continues to prevent a verified submission-ready claim.

## Provenance and determinism

VERIFIED provenance completeness remains 30/30 resolved instances = 100%. The migration changes
only executable JournalPort metadata and records evidence changes as empty. Repeated pinned 1.1.0
resolution produces identical objects and hashes:

- Nature Communications: `sha256:cd2d68eaa92d7213d5bf7c2c2bf2b59aec0e591f3cb209a63c997b7a0f94a43f`
- Nature Computational Science: `sha256:2f39bd960fba5259360f809a6f02c095622e395612092de467ac084a9268ce24`
- Nature Machine Intelligence: `sha256:5b9b50f1f1c53407e72412f76ca4400dbb99b969a2d7614a1d7c3c438fed7db1`

## Tests

Migration tests regenerate all seven 1.1.0 layers in memory and compare them byte-semantically with
committed JSON. Real-profile tests assert every VERIFIED machine-checkable rule receives PASS,
WARNING, or BLOCKED; all three have zero unsupported evaluators and deterministic resolution. Full
M0-M3 regression, schema, formatting, type, compilation, offline, no-mutation, silent-loss, and
silent-skip gates are included in the final command run.

Git identity remains unconfigured, so no commit was fabricated. The no-commit repository condition
continues to require owner action.

## Remaining risks

Profiles remain PARTIAL. Current canonical manuscripts do not deterministically represent all
submission-file inventories, Extended Data distinctions, unheaded introductions, title-page detail,
or conditional research ethics/code applicability. Those rules correctly remain manual/UNKNOWN.
Some official pages can intermittently block automated retrieval, limiting stronger snapshot
freshness evidence. No new journal or requirement was introduced.

## M4 readiness decision

**YES**, for architecture work only: VERIFIED machine-checkable coverage is 100%, silent skips are
zero, every active 1.1.0 rule has explicit applicability and criticality, and all three profiles now
produce non-UNKNOWN machine findings where evidence permits. M4 must still preserve PARTIAL/UNKNOWN
profile caveats and may not transform authorial or scientific content without explicit approval.
