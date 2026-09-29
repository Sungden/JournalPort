# M9 Audit — Public Repository Stabilization & Release Candidate

## M9 status and version

**PASS — RELEASE_CANDIDATE_READY.** Version: **0.1.0rc1**. Public release remains
**BLOCKED BY USER METADATA/HOSTING ACTIONS**.

## Repository architecture

The public layout exposes `src/`, `skills/`, `journal_profiles/`, `schemas/`, `tests/`, `benchmark/`,
`examples/`, and `docs/`. The deterministic core stays provider-independent. Skills orchestrate the
CLI/API and remain separately distributable. No MCP, UI, journal expansion, or portal automation
was introduced.

## Public API and CLI

`journalport.api` freezes eight typed operations for the 0.1 line and is documented in
`docs/API.md`. Stable CLI commands and structured artifact paths are documented in `docs/CLI.md`.
`--version` reports `journalport 0.1.0rc1`; benchmark JSON can go to stdout or `--output`.
Exit codes distinguish success (0), manual/verification/argument outcomes (2), and input/schema
errors (3), with future blocked/internal reservations documented.

## Documentation, license, citation, and security

README answers scope, differentiation, partial coverage, source installation, first audit, and
trust boundaries without PyPI/journal/compliance overclaims. Documentation indexes API/CLI,
profiles, Skills, ADRs, privacy, threat model, contribution, release, and benchmark material.

Original code/docs are Apache-2.0; `THIRD_PARTY_NOTICES.md` and evidence policy delimit dependencies,
journal evidence, fixtures, and external assets. Repository inspection found only short evidence
extracts/metadata, not full publisher pages.

`CITATION.cff` is structurally checked for required rc fields and lists `Sungden` provisionally. It
contains no email, ORCID, repository URL, DOI, or release date. Git identity was not treated as
automatic publication metadata.

Security/privacy documentation covers unpublished manuscripts, DOCX/LaTeX resource/path attacks,
web prompt injection, provider secrets, profile/plan/report/package tampering, and local/offline core
operation.

## Packaging and installation

- `python -m build`: PASS; wheel and sdist produced.
- Wheel content: 140 files; 30 schemas, 17 profile/registry data files, metadata present, Skills
  excluded per ADR-025.
- Sdist content: 301 files; Skills and profile registry present.
- Fresh wheel install: PASS from outside the checkout; bundled profile/schema/benchmark lookup PASS.
- Fresh sdist install: PASS; audit smoke test PASS.
- Installed wheel E2E: `VERIFIED_CANDIDATE` then `PACKAGE_REQUIRES_MANUAL_REVIEW`, correctly
  reflecting current PARTIAL profile scope.

Skills are source-repository/sdist assets (ADR-025). Curated profiles are pinned wheel data with no
automatic update (ADR-026). `journal_profiles/registry.yaml` version 1.0.0 records all three current
Article root profiles, versions, PARTIAL status, dates, and verified SHA-256 hashes.

## Benchmark reproducibility

The frozen snapshot records benchmark version 1.0.0, JournalPort version, profile versions, fixture
set, date, per-journal counts, and aggregate metrics. The CLI independently recomputes recall and F1
and fails on inconsistency. Public claims remain limited to the curated three-journal set: precision
100%, recall 90.48%, F1 95.00%, hallucination 0%.

## Tests and scans

- Full tests: **156 passed, 60 schema subtests passed**.
- Ruff check/format, mypy (69 source files), compileall, and `git diff --check`: PASS.
- Public API tests, CLI/version/benchmark contract tests, profile registry hashes, citation checks,
  and documentation structure checks: PASS.
- Machine-path scan: PASS, zero findings.
- Credential/private-key token scan: PASS, zero findings.
- Email scan: one intentional synthetic `https://user@...` parser-security fixture; no personal
  email in tracked content.
- CI YAML reviewed locally and matrix prepared for 3.11–3.13; **hosted CI not yet run**.
- Declared Python: 3.11+; directly tested locally/build installs on Python 3.14. Hosted matrix must
  validate 3.11–3.13 before public release.

## Git provenance

Repository-local identity is the user-provided `Sungden <dengy066@gmail.com>`; global configuration
was not changed. The repository began with no commits. M9 creates logical reviewed commits for the
core/profile foundation, guideline/Skill workflows, and rc stabilization. Final commit hashes and
clean-tree status are appended after commit creation. No history rewrite, tag, remote, or push occurs.

Reviewed history:

- `d5271d0b7eb8cc4d19ea620fd5a873b2536342b0` — deterministic core, schemas, profiles, tests.
- `7de335bd24ea4a8ea2ef19b2eaafe5b8a5764d8a` — guideline extraction and reusable Skills.
- `670999e54f228b30be739c79919ba0ad0f7e7878` — submission-package distribution correction.
- `14f01473a8969186f377cd69253461376aba3ee4` — rc1 documentation, metadata, CI, and audits.

`git fsck --full --no-dangling` passed. A final audit-record commit adds this immutable provenance
listing; its hash is reported in the final M9 response because a commit cannot contain its own hash.

## Readiness and remaining blockers

Release Candidate Readiness: **READY**.

Public Release Readiness: **BLOCKED BY USER METADATA/HOSTING**.

- METADATA_BLOCKER: approve citation author form, optional public email/ORCID, canonical repository
  URL, and release metadata.
- HOSTING_BLOCKER: select repository owner/name, add remote, and obtain hosted CI success.
- SECURITY METADATA BLOCKER: provide a private vulnerability-reporting contact.
- SCIENTIFIC_SCOPE_LIMITATION: all three profiles remain PARTIAL; this is disclosed and does not
  invalidate the engineering candidate.

Prepared but not executed: final tag command after approval, e.g. `git tag -a v0.1.0rc1`.

## Recommended next stage

First let the user unblock and perform **C. Public GitHub release** metadata/hosting steps and hosted
CI review. In parallel or immediately afterward, prioritize **A. real-LLM provider benchmark**, then
**B. JournalComplianceBench expansion**. Defer more profiles until benchmark/curation capacity grows,
and defer the MCP adapter until public CLI/API feedback stabilizes the contracts.
