# M6 Audit — Submission Package and Final Readiness

## M6 status

**PASS WITH CONDITIONS** (2026-09-29). The deterministic local pipeline now covers audit, plan, apply, candidate verification, package plan, package build, and independent package verification. M7, Skills, UI, mass journal expansion, transformation expansion, and portal automation were not started.

Conditions: current real profiles remain partial; M1 cannot represent every submission field; artifact format/resolution checks are limited to properties justified by current profile evidence; package readiness is not an acceptance claim; Git provenance remains incomplete.

## Submission package architecture

`journalport.package` separates profile-driven requirement extraction, bounded discovery, planning, building, hashing, path safety, independent verification, readiness, and report rendering. Planning must precede building. Verification reloads and enumerates the built package and does not trust builder success.

## Artifact taxonomy and requirement model

The closed journal-neutral taxonomy includes main manuscript, title page, cover letter, figures, tables, supplementary information/data, graphical abstract, highlights, reporting checklist, data/code availability documents, ethics/consent documents, author-contribution and competing-interest documents, source files, and other required files.

Requirements retain REQUIRED, OPTIONAL, CONDITIONAL, or UNKNOWN state; allowed formats/counts, filename/separate/embedded policy, source rule, provenance, condition, and readiness criticality. Rules are mapped by generic profile targets rather than per-journal Python branches. UNKNOWN and unresolved CONDITIONAL requirements always require manual review.

## Package planning

The planner validates the M5 logical report hash, candidate byte hash, post-transform compliance hash, and resolved profile hash. Discovery is limited to the candidate and explicitly supplied paths. It emits explicit found, missing, conditional, unknown, target-path, copy, and manual-action records. Missing known required artifacts produce `PACKAGE_BUILD_BLOCKED` before any copy.

## Package building

The builder rechecks the plan hash and every source hash, rejects nonempty output roots, symlinks, duplicate identities/targets, traversal, and changed sources, then copies only planned files. It generates `submission_manifest.json`, `PACKAGE_INDEX.md`, and optionally `submission_package.zip`. It never generates authorial content or mutates source/candidate artifacts.

## Package verification and readiness policy

Independent verification reloads the manifest, recomputes its logical hash, validates the profile and M5 report, enumerates all files, recomputes hashes/sizes/formats, detects undeclared files and symlinks, and confirms candidate identity. Status dimensions remain separate: candidate verification, compliance readiness, known package completeness, and profile confidence.

`PACKAGE_READY` requires a verified candidate, passing integrity, no missing known requirements, no blocking compliance result for a complete profile, and sufficient profile confidence. Missing requirements block. Partial profiles or UNKNOWN/CONDITIONAL requirements yield `PACKAGE_REQUIRES_MANUAL_REVIEW` rather than a false ready result.

## Package versus profile completeness

Known requirement completeness records whether every currently known required artifact exists. Profile completeness records whether the rule source is sufficiently complete to claim full readiness. A package can therefore be `COMPLETE` for known requirements while the profile remains `PARTIAL`, producing `PACKAGE_REQUIRES_MANUAL_REVIEW`.

## Manifest, provenance, and paths

The manifest contains only portable package-relative paths plus hashes, sizes, formats, artifact types, requirement states, validation results, origin types/hashes/object IDs, generator labels, pinned profile identity, and M5/M3 evidence hashes. Author files remain `AUTHOR_SUPPLIED`; generated evidence is labelled `JournalPort`. Absolute build paths are confined to the nonportable package plan.

## Logical package hashing and ZIP reproducibility

The logical hash canonicalizes manifest content while excluding timestamp, absolute paths, and filesystem ordering. Repeated builds with different timestamps produce the same logical hash. ZIP creation uses sorted entries, fixed timestamps, fixed permissions, and fixed compression; equivalent rendered inputs produce byte-identical ZIPs.

## Path security

Absolute paths, `..`, drive/alternate-stream syntax, unsafe components, output escape, symlink artifacts, duplicate identities, changed sources, and nonempty output roots fail closed. Package verification additionally rejects symlinks and undeclared payloads.

## Missing, unknown, and conditional requirements

- Missing verified required cover letter: detected and build blocked.
- UNKNOWN title-page requirement: preserved and final status manual review.
- CONDITIONAL ethics document with unresolved applicability: preserved and final status manual review.
- No cover letter, title page, declaration, checklist, highlight, or graphical abstract content was fabricated.

## Metrics

| Metric | Result |
|---|---:|
| Required Artifact Detection Accuracy | 100% |
| Missing Required Artifact Detection | 1/1 (100%) |
| Unknown Requirement Preservation | 1/1 (100%) |
| Conditional Requirement Preservation | 1/1 (100%) |
| Package Integrity Detection | 10/10 (100%) |
| Tamper Detection | 7/7 (100%) |
| Package Readiness Accuracy | 5/5 (100%) |
| Manifest Accuracy | 6/6 (100%) |
| Logical Package Hash Determinism | PASS |
| Deterministic ZIP Reproducibility | PASS |
| Offline Package Build/Verify | PASS |
| End-to-End CLI Success | PASS |
| Package False Positive Rate | 0% |
| Silent Package Skip Count | 0 |

Adversarial coverage includes modified and missing declared files, extra undeclared payload, manifest mutation, candidate mutation, verification evidence replacement, profile replacement, duplicate logical identity, traversal/absolute paths, and source mutation between plan/build.

## Offline and end-to-end CLI result

The full CLI sequence ran in fresh subprocesses with external HTTP(S) forced to a failing loopback proxy: `audit → plan → apply → verify → package plan → package build → package verify`. It completed successfully and produced a verified manual-review package without network access or in-memory state sharing.

## Three-journal package summary

All workflows included an explicit author-supplied cover-letter fixture so the known verified cover-letter requirement was not bypassed.

| Journal | Candidate | Known package completeness | Final package status | Logical package hash |
|---|---|---|---|---|
| Nature Communications | VERIFIED_CANDIDATE | COMPLETE | PACKAGE_REQUIRES_MANUAL_REVIEW | `sha256:6c2f29690e0a3fabd300d9a3bb3ab829b35c3843c11fab7217f8d409764146d7` |
| Nature Computational Science | VERIFIED_CANDIDATE | COMPLETE | PACKAGE_REQUIRES_MANUAL_REVIEW | `sha256:5387ea0fe5650a3fde99599d2059a0e5ebff07d4c19ccd135414efd0c573dbb8` |
| Nature Machine Intelligence | VERIFIED_CANDIDATE | COMPLETE | PACKAGE_REQUIRES_MANUAL_REVIEW | `sha256:22ea1b64612b94127acae3ec06813e30b4cc7b544223432e621ea73f09270fd3` |

The manual-review outcome is caused by partial/unknown profile requirements and is not weakened to demonstrate readiness.

## Schemas and versions

Added version 1.0.0 schemas: `submission_artifact.schema.json`, `submission_package_plan.schema.json`, `submission_manifest.schema.json`, and `package_readiness_report.schema.json`. Existing schema versions were unchanged. The repository schema inventory is now 21 files.

## Remaining risks

1. Profile-to-artifact mapping is generic but current profile vocabulary does not yet encode every possible portal upload requirement.
2. Image resolution and specialized document-content validation require explicit verified profile constraints and reliable metadata before enforcement.
3. Author identity checks are limited by M1 structured-author coverage; no author order or identity is modified.
4. Logical identity includes the M5 verification hash, whose current canonical representation retains known parser-locator limitations.
5. Clean-install testing uses the repository environment rather than provisioning a new network-isolated virtual environment; the fresh-process CLI boundary is covered.
6. Git identity is unset, no commit was fabricated, and public-release provenance must be fixed before release.

## M7 readiness

**M7 readiness = YES.** The complete deterministic pipeline exists, independent package verification passes, all synthetic safety gates pass, offline/fresh-process execution passes, and the three real profiles produce conservative manual-review packages.
