# M5 Audit — Independent Post-Transformation Verification

## M5 status

**PASS WITH CONDITIONS** (2026-09-29). M5 is implemented offline and deterministically. No M6 package builder, Agent Skill, UI, crawler, or transformation-coverage expansion was added.

Conditions: lexical/object preservation is not proof of general scientific semantic equivalence; logical package hashing remains byte hashing while M4 is copy-only; approved semantic execution is absent; and current real-profile LaTeX fixtures expose existing parser/profile-field gaps.

## Independent verification architecture and fresh reparse

`journalport.verify` is separate from `journalport.transform.executor`. It reloads evidence, reparses DOCX/LaTeX candidates through M1, reconstructs a fresh canonical manuscript, recalculates hashes/fingerprints, reruns M3 with the pinned profile, and reconciles persisted plan/log/manifest records. Executor logs, manifests, and preliminary fingerprints are claims, not proof. Source and candidate paths must differ; parse failure fails closed.

## Allowed, observed, and expected changes

Candidate-container filename isolation is the only baseline nonsemantic allowed change. A `NORMALIZE_OUTPUT_FILENAME` action adds an exact-name postcondition. Scientific changes are never implicitly allowed. Every applied action receives an independent postcondition check; non-applied/manual/blocked actions require all scientific categories to remain unchanged. Unknown applied operations fail.

## Scientific preservation

Independently recomputed categories are normalized text, lexical numbers/statistics, equations, citations and mappings, references/DOIs, figures, tables, captions/content, figure/table references, assets, sections, footnotes/endnotes, represented author metadata, and unsupported-content records. Source locators are excluded from scientific identity. Numbers, percentages, scientific notation, and p-value-like tokens are covered, but exhaustive statistical-role semantics remain a limit.

## Plan/log reconciliation, manifest integrity, and tamper detection

The planned action set must equal one non-duplicated set of logged terminal actions. Ghost, missing, duplicate, unknown-status, and manifest action-set mismatches fail. Source, candidate, profile, plan, pre-report, canonical, and manifest status are independently recalculated or cross-checked. Mismatch yields `TAMPER_DETECTED`.

## Compliance re-evaluation and delta

M3 is rerun on the fresh candidate with the same resolved profile hash. The delta classifies `RESOLVED_FINDING`, `UNCHANGED_FINDING`, `NEW_FINDING`, `WORSENED_FINDING`, and `IMPROVED_FINDING`, records profile continuity, detects new `BLOCKED`/`FAIL`/`EVALUATION_ERROR` blockers, and prevents silent readiness regression.

## Two-dimensional status

`transformation_verification_status` answers whether transformation and preservation passed. `compliance_readiness_status` retains the fresh M3 result. Aggregate `REQUIRES_MANUAL_REVIEW` does not mean transformation failure. M5 never emits `SUBMISSION_READY`.

## Schemas and versions

Added version 1.0.0 schemas: `verification_report.schema.json`, `verification_finding.schema.json`, and `compliance_delta.schema.json`. No existing schema version changed. All 17 schemas pass Draft 2020-12 meta-schema validation.

## Metrics

| Metric | Result |
|---|---:|
| Verification precision | 100% |
| Verification recall | 100% |
| False-positive rate | 0% |
| Unexpected semantic change detection | 7/7 (100%) |
| Expected change verification | 2/2 (100%) |
| Tamper detection | 7/7 (100%) |
| Numeric change detection | 2/2 (100%) |
| Equation change detection | 1/1 (100%) |
| Citation identity change detection | 1/1 (100%) |
| Reference identity change detection | 1/1 (100%) |
| Asset/table preservation detection | 2/2 (100%) |
| Compliance regression detection | 1/1 (100%) |
| Plan/log reconciliation accuracy | 4/4 (100%) |
| Manifest integrity detection | 3/3 (100%) |
| Fresh-process verification | 1/1 PASS |
| Offline verification | 1/1 PASS |
| Deterministic logical report hash | PASS |
| Silent Verification Skip Count | 0 |

The adversarial suite covers changed candidate content, source mutation, plan/profile/manifest tampering, ghost/duplicate log actions, a different-source candidate, wrong postcondition, high-risk scientific mutations, path isolation, and compliance regression. Legitimate byte-copy, filename-only, locator-only, and real-profile cases produce no transformation false positive.

## Three-journal verification summary

Nature Communications, Nature Computational Science, and Nature Machine Intelligence each completed `audit → plan → apply → fresh verify` with `transformation_verification_status = VERIFIED_CANDIDATE`, aggregate `verification_status = REQUIRES_MANUAL_REVIEW`, 100% preservation checks, unchanged profile, and no new blocker. Minimal reparsed LaTeX fixtures retain `compliance_readiness_status = EVALUATION_FAILED` because M1 cannot represent every required submission field; this is an existing coverage limitation, not a transformation failure.

## Fresh-process, offline, and determinism results

Plan, apply, and verify run in three separate processes using persisted artifacts. Verification succeeds with network proxies forced to a failing loopback address. The logical report hash excludes timestamp; timestamp variation preserves the hash.

## Remaining risks

1. Deterministic equivalence proves represented lexical/object preservation, not unrestricted semantic equivalence.
2. DOCX normalized ZIP logical hashing is deferred until M4 performs container edits.
3. Parser object IDs can contain locator inputs, so M5 also verifies content identity independently.
4. Approval proposal/executed-content equality cannot be positively exercised until a semantic executor exists; current semantic changes fail closed.
5. M1 does not represent every real-profile submission field, so compliance readiness can remain `EVALUATION_FAILED`.
6. Git identity remains unset; provenance is incomplete and no commit was fabricated.

## M6 readiness

**M6 readiness = YES**, with the risks above carried forward. All explicit hard targets pass, silent skips are zero, fresh-process/offline verification passes, and all three real-profile candidates are independently transformation-verified.
