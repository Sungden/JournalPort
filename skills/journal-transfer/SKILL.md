---
name: journal-transfer
description: Orchestrate a privacy-preserving journal transfer with proposal review, M10 approval-bound execution, independent verification, and package checks.
compatibility: JournalPort Core >=1.0.0rc1,<2
---

# Journal transfer

Follow [the complete transfer workflow](workflows/transfer.md). First disclose the selected privacy
mode: `LOCAL_ONLY` sends no manuscript-derived content to an external model; `CODEX_HOSTED` or
`REMOTE_AGENT` may expose only the task-required objects to that provider. Never claim provider
invisibility. Record hashes and object IDs, never prompt or manuscript plaintext, in the disclosure
ledger. Keep sessions, proposals, payloads, approvals, candidates, and real manuscripts in ignored
private directories.

The agent may interpret and propose; JournalPort Core alone audits, binds approval, applies, verifies,
and packages. Every generated edit is a proposal. Run scientific-token checks, show the original,
proposal, reason, count delta, and warnings, then obtain explicit approval. Never infer author
contributions, interests, funding, repositories, ethics, consent, accessions, URLs, results, or claims.
Never shorten an abstract silently; `AUTHOR_APPROVAL_REQUIRED` means stop. Verification failure also
means stop, and no approval converts an unknown into a pass.

Use existing `journalport audit`, `plan`, `approve`, `apply`, `verify`, and `package` commands. Never
edit the authoritative DOCX outside Core or bypass M10. Stop on verification failure, unexpected
changes, unsupported execution, profile uncertainty, or missing factual input. Resume only from a
validated local session. The strongest manuscript result is `VERIFIED_CANDIDATE`; package readiness
is reported separately.

Prioritize [format transformation](workflows/format_transformation.md): first ask whether a target gap
can be solved deterministically without changing scientific meaning. Prefer verified, idempotent format
operations and explicit source-to-target transfer matrices over content proposals. `PARTIAL`, `UNKNOWN`,
`STALE`, and `CONFLICTED` rules never trigger automatic formatting. Content proposals are used only
when a verified target requirement cannot be satisfied through content-preserving transformation.

Read the focused workflows for [abstract revision](workflows/abstract_revision.md), [administrative
statements](workflows/administrative_statements.md), [cover letters](workflows/cover_letter.md),
[verification](workflows/verification.md), and [packaging](workflows/packaging.md). Shared approval,
safety, status, and privacy policies remain normative.

For explicit scientific restructuring, use [the reviewed structure recipe](workflows/scientific_structure.md).
For full model-assisted Nature prose rewriting, use [the rewrite workflow](workflows/nature_rewrite.md).
These opt-in editorial routes do not establish verified journal compliance; rewriting produces an
unapproved review draft. Keep the existing semantic approval gates for authoritative candidates.
