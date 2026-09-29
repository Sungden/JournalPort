# M8 Audit — Agent Skills & Reusable Workflow Layer

## M8 status

**PASS WITH CONDITIONS.** Four versioned skills, a stable public API façade, machine-readable
registry/run records, shared safety semantics, tests, examples, CI configuration, and public-repo
readiness documentation are implemented. Public release is separately **BLOCKED**.

Conditions: the real-provider repeated-run benchmark remains deferred; the skill-creator bundled
validator could not run because its environment lacks PyYAML (repository-native validation
passed); and the three production profiles are intentionally `PARTIAL`, so an end-to-end transfer
skill run correctly stops for approval/manual review rather than claiming readiness.

## Skill architecture and implemented skills

```text
Agent host → skills/*/SKILL.md → thin scripts → stable JournalPort CLI/API → deterministic core
                                      ↓
                               skill_run.json
```

Implemented at version **1.0.0**: `journal-profile` (draft-only), `journal-audit` (read-only),
`journal-transfer` (approval-gated), and `submission-package` (artifact build/verification).
Conditional detail lives in focused references; shared status, safety, approval, and privacy
policies are not duplicated. Core code imports no skill modules and no provider SDK.

## Skill/core boundary and public interfaces

Skills orchestrate the stable commands `audit`, `plan`, `apply`, `verify`, `package plan/build/verify`,
and `profile discover/refresh-draft`. They do not count words, encode journal rules, evaluate
compliance, edit scientific prose, or verify their own output. `journalport.api` is a minimal typed
façade over the existing tested functions: audit, plan, apply, verify, package plan/build/verify,
and profile draft refresh. No core refactor or MCP layer was introduced.

The wheel now includes JSON Schemas. Clean-install testing discovered and fixed the previous
source-tree-only schema lookup in the profile loader.

## Registry, versioning, and machine-readable records

`skills/registry.yaml` is JSON-compatible YAML validated by `skill_registry.schema.json`. It records
IDs, independent semantic versions, entry points, minimum JournalPort version, I/O, capabilities,
and safety level. `skill_run.schema.json` records input/output SHA-256 hashes, commands, exact final
status, profile hash when available, and manual-review items; it deliberately excludes private
reasoning.

## Safety semantics

- Profile refresh refuses `journal_profiles/` or any descendant as output and cannot promote a
  draft.
- Audit never mutates the manuscript and preserves `UNKNOWN`/manual status.
- Transfer stops before apply when approval-required or forbidden actions exist. Semantic edits
  have no skill executor. Independent verification failure is terminal; maximum status is
  `VERIFIED_CANDIDATE`.
- Package creation accepts only supplied artifacts and preserves blocked/manual package statuses.
- All workflows are local-first and expose hashes/statuses rather than manuscript text to the host.

## Workflow and adversarial metrics

Metric denominators are the explicit M8 workflow/safety cases, with deterministic core regression
tests included where the enforcement belongs in core.

| Metric | Result |
|---|---:|
| Skill Workflow Completion Rate | 4/4 = **100%** |
| Correct Stop Rate | 10/10 = **100%** |
| Status Preservation Accuracy | 10/10 = **100%** |
| Approval-Bypass Prevention Rate | 1/1 = **100%** |
| Unsafe Action Prevention Rate | 7/7 = **100%** |
| Production Profile Protection Rate | 2/2 = **100%** |
| Core Artifact Validity Rate | 4/4 = **100%** |
| Unauthorized draft → VERIFIED prevention | 1/1 = **100%** |
| UNKNOWN → PASS coercion prevention | 1/1 = **100%** |
| Fabricated artifact prevention | 1/1 = **100%** |
| Continue-after-verification-failure prevention | 1/1 = **100%** |

The golden cases cover profile draft success/blocked evidence, audit known and unknown findings,
safe transformation/approval/verification outcomes, and complete/missing/unknown package inputs.
Seven adversarial policies are exercised by skill contracts plus executable core gates.

## Validation evidence

- Full suite: **150 passed, 60 subtests passed**.
- Skill/schema subset: **14 passed, 60 subtests passed**.
- Ruff check: PASS; Ruff format check: PASS after formatting.
- mypy strict configured scope: PASS, 69 source files.
- Draft 2020-12 schema/meta-schema checks: PASS, 30 schemas.
- `compileall src skills`: PASS.
- `git diff --check`: PASS.
- Skill-creator `quick_validate.py`: NOT RUN (external validator environment lacks PyYAML); the
  repository independently validates frontmatter, names, registry, scripts, and behavior.

## Clean install and end-to-end result

Fresh Python venv `pip install .`: **PASS**. Installed `journalport --help` and
`journalport audit --help`: **PASS**. A complete installed-CLI synthetic flow produced
`VERIFIED_CANDIDATE` and `PACKAGE_REQUIRES_MANUAL_REVIEW`; the latter accurately reflects the
current partial profile. The profile skill produced a schema-valid `DRAFT`; audit emitted
structured JSON with preserved unknowns; transfer stopped at `APPROVAL_REQUIRED`; and the package
skill independently reproduced `PACKAGE_REQUIRES_MANUAL_REVIEW`.

End-to-end skill result: **PASS WITH EXPECTED MANUAL STOP**. A no-stop production-profile chain is
not a valid target while all curated profiles are `PARTIAL`; creating a permissive profile solely
to make the demo green would weaken the safety claim.

## M0–M7 regression and provider independence

**PASS**: all pre-M8 tests remain green. Removing `skills/` leaves the installed core operational;
the core has no skill or provider dependency. No real-LLM repeated-run evaluation was attempted,
because it is optional and no configured provider is required for M8.

## Public repository readiness and Git provenance

Engineering readiness is **READY WITH CONDITIONS**; see `PUBLIC_REPO_READINESS.md`. README,
examples, installation, CI workflow, package metadata, and safety claims now match tested scope.
`CITATION.cff` no longer invents a repository URL or release date.

Public Release Readiness is **BLOCKED**. Both `git config user.name` and `git config user.email` are
unset, the repository has no reviewed initial commits, the canonical repository URL is undecided,
and citation authors/preferred citation/release metadata require owner confirmation. No identity,
commit, URL, DOI, or release was fabricated.

## Remaining risks

- Three profiles remain partial and cannot establish complete journal compliance.
- M7 recall was 90.48% on a small curated three-journal benchmark; no live-provider variance study
  exists.
- Skill run records validate hashes but do not yet provide a single high-level resume command.
- CI is configured but has not run on a hosted repository.
- Package version `0.0.0` and provisional citation metadata are unsuitable for public release.

## Next-stage recommendation

Recommended order: **A. Public repository stabilization**, then **E. real-provider benchmark**,
then **B. JournalComplianceBench expansion**. Consider **C. MCP adapter** only after the CLI/API
contracts stabilize under public CI; undertake **D. additional journal profiles** only after the
benchmark and curation process scale safely. No next stage was started.
