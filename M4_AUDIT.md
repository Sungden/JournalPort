# M4 Audit — Transformation Planning and Safe Transformation Engine

Date: 2026-09-29  
Status: **PASS WITH CONDITIONS**

## Architecture and classes

M4 implements `ComplianceFinding[] -> deterministic TransformationPlan -> approval gate -> safe
executor -> TRANSFORMED_CANDIDATE`. Planning never executes. The four classes are
SAFE_AUTOMATIC, CONTENT_PRESERVING_AUTOMATIC, AUTHOR_APPROVAL_REQUIRED, and FORBIDDEN_AUTOMATIC.
Every non-passing finding becomes an action; unsupported work is explicit rather than omitted.

The planner validates canonical manuscript, resolved-profile, compliance-report, and source-artifact
hashes. Stable action IDs cover finding, operation, object IDs, and profile hash. Plan hashes cover
all logical plan content except timestamp/hash. The executor repeats every bound-input check, confines
output paths, rejects in-place writes, and verifies the original byte hash before and after execution.

## Approval integrity

Approvals are external records with NOT_REQUIRED, PENDING, APPROVED, REJECTED, or EXPIRED status.
They bind action ID, plan hash, and proposed-content hash. Tests reject wrong action, wrong plan,
changed proposal, changed parameters, pending/rejected state, and stale source/profile/report/plan.
Production logic never creates APPROVED. Even a valid approval cannot run authorial changes because
M4 intentionally has no semantic executor; the result remains MANUAL_ACTION_REQUIRED.

## DOCX and LaTeX strategies

ADR-011 selects minimal Open XML patching for future DOCX work and forbids simplified whole-package
round trips. The current implementation only losslessly copies the package and can safely name the
candidate. M1 UNSUPPORTED_BLOCKING content blocks automatic actions. ADR-012 similarly requires
exact-locator minimal LaTeX patches; current support is lossless copy/name only. Compilation and
independent reparse are outside M4.

ADR-014 separates byte, canonical, scientific-fingerprint, and future normalized-ZIP hashes. Because
the current operation is a byte-preserving copy, byte and preliminary logical-package hashes match;
this equivalence is not generalized to future DOCX edits.

## Supported and unsupported transformations

Supported automatic operations:

1. verified safe output filename normalization;
2. lossless source-to-candidate copy.

The operation is deterministic and idempotent. Supported safe transformation coverage is 1 of 7
suggested first-set transformation categories (14.3%); safety takes precedence over coverage.

Unsupported/manual: style changes, line numbering, section relocation, title-page extraction,
bibliography rendering, figure/supplement renaming without a verified rule, abstract/title/main-text
rewriting, declaration generation, reference/figure removal, image conversion, and all scientific
content changes. Unknown operations fail closed. No missing declaration text is invented.

## Schemas and versioning

TransformationPlan advances from the M0 placeholder v1 to executable v2, a deliberate breaking wire
change with no existing production plans to migrate. New v1 schemas define TransformationAction,
Approval, TransformationLog, and CandidateManifest. Candidate status is fixed to
TRANSFORMED_CANDIDATE and can never claim submission readiness.

## Preservation and tamper results

- Plan/action determinism: 100% across timestamp changes.
- Safe action execution: 2/2 repeated/idempotent runs = 100%.
- Approval-gate accuracy: 5/5 labeled approval bindings/states = 100%.
- Tamper detection: 8/8 plan, source, profile, report, action, proposal, wrong-plan, and wrong-action
  cases = 100%.
- Output traversal/unsafe filename detection: 2/2 = 100%.
- Numeric preservation: 2/2 = 100%.
- Equation preservation: 2/2 = 100%.
- Citation identity preservation: 2/2 = 100%.
- Reference/asset identity preservation: 2/2 = 100%.
- Original source preservation: all executor and CLI cases = 100%.
- Silent transformation skip count: 0.
- Unexpected semantic change count: 0.

Fingerprint checks compare numeric, equation, citation, reference, and asset identities before and
after supported execution. They are preliminary same-process gates, not M5 independent verification.

## CLI and real profiles

`journalport plan` is a dry run that writes transformation_plan.json and its bound compliance report.
`journalport apply` is explicit, accepts no in-place mode, re-resolves the local pinned profile, and
writes candidate artifact, transformation log, and candidate manifest beneath the chosen output
root. Audit/plan/apply require no network or API key.

The three 1.1.0 real profiles have no VERIFIED safe transformation rule. Each compliant synthetic
audit therefore produces zero automatic actions and nine explicit unsupported/manual actions, with
plan status APPROVAL_REQUIRED. This is correct no-op behavior: JournalPort does not manufacture
format changes for demonstration.

## Tests and conditions

Full M0-M3 regression plus M4 planner, stable ID/hash, approval, replay, tamper, traversal,
idempotence, CLI dry-run/apply, real-profile, manifest, log, and preservation tests pass. Git
provenance remains incomplete because user.name/user.email are not configured; no identity was
fabricated.

Conditions: transformation coverage is deliberately narrow; DOCX/LaTeX structural editing,
normalized ZIP hashing, exact source patches, style/line-number actions, and approved semantic
proposal execution are not implemented. Preliminary fingerprints use the trusted canonical object;
candidate reparse and independent comparison belong exclusively to M5.

## M5 readiness

**YES.** All implemented M4 safety gates pass, candidate artifacts are produced without source
mutation, approval-required/forbidden work cannot enter the automatic executor, and preliminary
preservation checks pass. M5 must independently reparse the candidate, rerun compliance, compare
scientific semantics, and decide acceptance; M4 execution alone is not proof of correctness.
