# M11 Codex-native privacy-preserving journal transfer agent audit

## 1. Status and architecture

**M11 = PASS.** JournalPort now has a Codex-compatible agent skill above—not instead of—the M10
deterministic core. The probabilistic layer interprets findings, requests facts, creates proposals,
and orchestrates commands. Core remains the truth-producing layer for parsing, profiles, compliance,
approval binding, OpenXML execution, hashes, independent verification, and package integrity.

## 2. Codex Skill layout and supported tasks

`skills/journal-transfer/` contains the concise entry instruction plus progressively disclosed
workflows for complete transfer, abstract revision, administrative statements, cover letters,
verification, and packaging. It also points to canonical schemas and a synthetic example. The skill
supports source-to-target gap classification, minimized proposal tasks, author pauses, M10 execution,
post-transform audit, and package orchestration. It does not submit manuscripts or provide a second
editing engine.

## 3. Agent/Core responsibility boundary

Agent output is never evidence or deterministic truth. Generated wording is an `AgentProposal` with
the original/proposed hashes, rationale, evidence references, risk, scientific-diff flags, and pending
approval. Author approval does not authorize arbitrary file edits: exact content is subsequently bound
to the M10 action, plan, and payload hash and applied only by the supported Core executor.

## 4. Transfer session and resume

`TransferSession` records source hash/path, source/target context, pinned profile version, privacy
mode, artifact references, disclosure ledger, and a closed status vocabulary. Explicit transition
validation rejects skipped gates. JSON round-trip tests resume both `WAITING_FOR_AUTHOR_INPUT` and
`WAITING_FOR_APPROVAL`. Session records contain artifact references rather than manuscript prose.

## 5. Privacy model and minimization

`LOCAL_ONLY` rejects any non-local model host and has zero external model disclosure.
`CODEX_HOSTED`/`REMOTE_AGENT` require truthful disclosure that selected content may be processed by
the provider; JournalPort makes no claim that the provider cannot see it or that ordinary inference is
end-to-end encrypted. Abstract context contains only the abstract, counts, target journal, and rule.
Cover letters and administrative workflows similarly limit inputs. The Core itself adds no external
upload.

Sensitive runtime roots (`private/`, `sessions/`, `payloads/`, `approvals/`, and `real-run/`) are Git
ignored. No real manuscript, proposal payload, transformed candidate, API key, or plaintext manuscript
log is present in this change.

## 6. Disclosure ledger

The local ledger stores timestamp, session/task, known host/model, privacy mode, disclosed object IDs,
content hashes, purpose, approximate size, and full-document flag. It deliberately excludes prompts
and plaintext objects. A synthetic secret-marker test proves ledger text contains only identifiers and
hashes. The ledger records what this workflow can observe; it does not describe unobservable provider
internals.

## 7. Scientific-diff safeguards

`ScientificDiffReport` deterministically compares integers/floats, percentages, p-values, confidence
intervals, dates, gene/protein-like symbols, dataset accessions, DOI/URL strings, citations,
figure/table references, equation tokens, and reference identifiers. Any detected protected-token
delta changes the report to `REVIEW_REQUIRED` and escalates a proposal to HIGH risk. Tests cover
numbers, percentages, citations, figure references, DOI changes, and a no-change safe case. These
heuristics are warnings, not proof of semantic equivalence.

## 8. Author input and approval flow

Missing Author Contributions and Competing Interests always pause for author facts. Data and Code
Availability first use explicit existing text; insufficiency pauses rather than inventing a repository,
accession, or URL. Abstract shortening remains a MEDIUM-risk proposal unless protected deltas escalate
it. The skill displays original/proposed text, rationale, count change, and warnings before explicit
approval, then uses `journalport approve` and `journalport apply`. Unsupported actions remain manual;
equation/scientific edits are forbidden automatic operations.

## 9. Verification and package behavior

Packaging is permitted only when transformation status is `VERIFIED_CANDIDATE`,
`unexpected_changes = []`, and `failure_reasons = []`. Any failure blocks the session. The candidate is
re-audited and residual findings are separated into author input, manual submission tasks, unsupported
work, profile uncertainty, and genuine noncompliance. A cover letter is a separate artifact labelled
`DRAFT — AUTHOR REVIEW REQUIRED`; it never enters manuscript body. Package readiness remains distinct
from transformation verification.

## 10. Source-to-target logic

The workflow reports `KEEP`, `MODIFY`, `REMOVE`, `ADD`, `SPLIT_ARTIFACT`, `MANUAL_REVIEW`, and
`UNKNOWN`. Target silence never authorizes removal of scientific content. Profile `PARTIAL`, `STALE`,
`CONFLICTED`, and `UNKNOWN` states are surfaced as uncertainty rather than manuscript failure.

## 11. Synthetic acceptance result

Only generated fixtures were used. The combined M11 orchestration/safeguard suite and existing M10
confidential synthetic workflow exercised audit/plan interpretation, abstract proposal, factual-input
pauses, payload-bound approval, genuine candidate modification, source preservation, independent
verification, and package plan/build/verify. The M10 synthetic result remains:

- source unchanged: **yes**
- candidate genuinely modified: **yes**
- transformation status: **VERIFIED_CANDIDATE**
- unexpected changes: **[]**
- package integrity verification: **passed**
- private plaintext in logs/ledger: **no**

No remote model was invoked; proposal generation was represented by a synthetic mock-produced payload.

## 12. Tests and quality gates

- pytest: **209 passed, 68 subtests passed**
- Ruff lint: **passed**
- Ruff format check: **passed**
- mypy strict configured scope, no incremental cache: **passed**
- `python -m compileall src`: **passed**
- `git diff --check`: **passed**

Coverage includes plan classification, proposal construction, approval gating contracts, unsupported
actions, verification stop behavior, protected scientific tokens, prompt minimization, hash-only
ledger behavior, LOCAL_ONLY enforcement, Git-ignore safety, public secret scans, and waiting-state
resume.

## 13. Remaining limitations and privacy limits

Scientific token detection is conservative regex-based analysis and cannot prove preservation of
meaning, recognize every biomedical symbol, or validate novelty. Model-provider retention/training,
host telemetry, local OS backups, filesystem encryption, secure deletion, and Codex infrastructure are
outside JournalPort's observable process boundary. The three production profiles remain PARTIAL.
Figure splitting, complex equation/reference edits, arbitrary scientific rewriting, publisher-site
submission, and unsupported DOCX constructs remain manual or forbidden.

## 14. Release readiness and stop condition

All 18 M11 gates pass for the synthetic scope. The implementation remains unreleased development work
on top of `0.1.0rc3`; no tag or release was created. M12 has not started. No unpublished manuscript was
processed. A first real transfer requires a separate explicit instruction, an informed privacy-mode
choice, factual author input, and proposal-by-proposal approval.
