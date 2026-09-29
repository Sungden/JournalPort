# M3 Audit — Deterministic Submission Compliance Engine

Date: 2026-09-29  
Status: **PASS WITH CONDITIONS**

## Compliance architecture

M3 implements the read-only path `CanonicalManuscript + pinned ResolvedJournalProfile ->
ComplianceFinding[] -> ComplianceReport -> Submission Readiness`. The engine is LLM-free, offline,
deterministic, and checks the canonical manuscript hash before and after evaluation. It performs no
rewrite, formatting change, section move, rendering, or packaging.

Evaluation is policy gate -> selector -> operator -> template finding -> readiness. Every effective
profile rule yields a finding; unsupported operators and missing selectors are explicit errors.
Canonical integrity checks cover citation/bibliography mismatch, uncited and duplicate references,
duplicate DOI values already present, missing figure assets, and figure/table captions.

## Operators and selectors

The registry implements 17 operators: EQ, NE, LT, LTE, GT, GTE, EXISTS, NOT_EXISTS, IN, NOT_IN,
COUNT_EQ, COUNT_LTE, COUNT_GTE, MATCH_REGEX, NOT_MATCH_REGEX, CONTAINS, and NOT_CONTAINS. All 17 have
positive unit cases. Unsupported operators produce EVALUATION_ERROR; silent skips are impossible.

Selectors cover title, article type, abstract, main text, controlled canonical section order,
references, combined figures/tables, figure files, supplementary materials, required statements,
and explicit submission metadata. Missing/ambiguous fields fail explicitly. Section aliases are
closed and versioned; there is no semantic LLM matching.

## Counting and applicability semantics

ADR-008 freezes Unicode NFC word/character and canonical-object counting, including exclusions and
known differences from office-suite counters. Ambiguous/partial word-count scope is UNKNOWN.

Formal applicability is ALWAYS, CONDITIONAL, NOT_APPLICABLE, or UNKNOWN. Conditional rules without
a deterministic condition result become UNKNOWN. The M2 profile schema received optional additive
`applicability_mode` and `critical_for_readiness` properties. M2-era instances default to UNKNOWN
and false in typed models, preserving hashes and failing closed. Criticality is never inferred from
severity.

## UNKNOWN, CONFLICTED, STALE, and readiness

UNKNOWN never becomes PASS. PARTIAL/UNKNOWN rules explain the missing evidence or applicability and
require manual review. CONFLICTED and STALE profiles cannot be fully ready. ADR-009 defines readiness
precedence and distinguishes manuscript BLOCKED, PROFILE_NOT_VERIFIABLE, and EVALUATION_FAILED.
Reports retain the active profile status and a concise coverage/acceptance disclaimer.

## Finding and trace design

ComplianceFinding schema v1 includes stable hash-derived IDs, rule/profile/hash identities,
finding and rule statuses, current/expected values, objects, provenance, resolution reference,
evaluator method/version, severity, applicability-derived result, and non-executing autofix metadata.
ComplianceReport schema v2 adds canonical/input/profile hashes, readiness, coverage, caveats,
unsupported content, manual review, findings, and timestamp-independent canonical report hash.
EvaluationTrace v1 projects the complete manuscript-rule-profile-evaluator chain.

Schema migration record: the M0 ComplianceReport v1 placeholder could not represent M3 readiness,
hashes, coverage, evaluation errors, or traces. It was replaced by v2, a deliberate wire-breaking
major bump. No M3 reports existed to migrate; future v1 consumers require explicit conversion. The
two new M2 profile fields are additive and default fail-closed. M2 resolved hashes remain identical
because default fields are omitted from hash canonicalization; explicit behavior-changing values are
included.

## CLI and network independence

`journalport audit MANUSCRIPT --journal SLUG --article-type article --profile-version 1.0.0
--output DIR --format json|html|both` supports DOCX and TeX. It loads local pinned profiles and writes
JSON, static escaped HTML, and evaluation trace JSON. No network call or API key exists in the audit
path. CLI integration ran against a local LaTeX fixture.

## Initial three-profile audit

| Profile | Rules | Machine-checkable | Evaluated | UNKNOWN findings | Readiness |
|---|---:|---:|---:|---:|---|
| Nature Communications / Article | 16 | 13 | 0 | 16 | REQUIRES_MANUAL_REVIEW |
| Nature Computational Science / Article | 17 | 12 | 0 | 17 | REQUIRES_MANUAL_REVIEW |
| Nature Machine Intelligence / Article | 17 | 12 | 0 | 17 | REQUIRES_MANUAL_REVIEW |

Machine-evaluable marking coverage is 37/50 (74%), but successful evaluation coverage is 0/50 for
the existing profiles because they predate formal applicability fields. This is intentional:
`machine_checkable` does not authorize M3 to guess applicability or criticality. A future reviewed
profile revision can opt rules into deterministic evaluation without changing engine code.

## Synthetic metrics

Eleven labeled ground-truth fixtures cover perfect minimal, long abstract, missing data and competing
statements, excessive references/figures, missing figure asset, citation mismatch, conditional
applicability, unsupported operator, and UNKNOWN profile rule.

- Finding Detection Precision: 11/11 = 100%.
- Finding Detection Recall: 11/11 = 100%.
- Finding Detection F1: 1.000.
- Status Accuracy: 11/11 = 100%.
- Readiness Accuracy: 11/11 = 100%.
- Unsupported Rule Detection Rate: 1/1 = 100%.
- UNKNOWN Preservation Rate: 2/2 = 100%.
- Silent Rule Skip Count: 0.
- Determinism: stable finding IDs/statuses/readiness and report hash across timestamps, 100%.
- No mutation: canonical pre/post hashes equal in all engine and CLI tests.

## Tests and validation

Final results: 72 tests and 20 schema subtests passed; all 10 schemas passed Draft 2020-12 contract
checks; ruff check and format-check passed; strict mypy passed 27 profile/compliance/CLI source files;
compileall and `git diff --check` passed. The CLI test replaces socket connection and DNS functions
with hard failures and still passes, and verifies the input manuscript bytes remain unchanged.

Git baseline condition: the repository has no initial commit and no configured `user.name` or
`user.email`. No baseline or M3 commit was fabricated under a false identity; all files remain
untracked and this must be resolved by the repository owner.

## Remaining risks

The three initial profiles need an evidence-reviewed version adding formal applicability and
criticality before useful journal-specific machine evaluation. Canonical metadata does not yet carry
reliable image dimensions/DPI, author/affiliation lists, keyword objects, or submission-file
inventory, so those checks are UNKNOWN/error rather than guessed. Citation links depend on parser
object IDs; no Crossref/network verification is performed. The CLI has no installed-release/version
migration workflow yet. M0–M2 conditions remain inherited.

## Recommended M4 plan

Only after reviewed profile migration, design an approval-gated transformation plan that consumes
M3 findings without mutating source files in place. Separate content-preserving formatting from
authorial/scientific changes, require explicit approval for the latter, preserve object IDs and
provenance, and leave independent post-transformation verification for M5.
