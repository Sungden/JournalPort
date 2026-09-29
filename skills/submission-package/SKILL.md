---
name: submission-package
description: Build and verify a submission package from a VERIFIED_CANDIDATE and author-supplied artifacts; use after independent candidate verification, not to author missing materials.
---

# Submission package

Use JournalPort through `scripts/run.py` for package plan → build → independent package verify. Require a
`VERIFIED_CANDIDATE`, its verification and post-transform compliance reports, a pinned profile,
and explicitly supplied auxiliary artifacts. The core resolves artifact requirements and validates
hashes.

Never fabricate a cover letter, title-page data, ethics/consent/contribution statements, graphical
abstract, or other author material. Missing or conditional artifacts remain author input or manual
review. Stop on invalid candidate verification, unknown requirements, tampering, or package
verification failure.

Return the exact package status and missing/manual artifacts. Only report the core's
`PACKAGE_READY`, `PACKAGE_READY_WITH_WARNINGS`, `PACKAGE_REQUIRES_MANUAL_REVIEW`,
`PACKAGE_BLOCKED`, or `PACKAGE_VERIFICATION_FAILED`. See [artifact policy](references/artifact-policy.md)
and the shared status, safety, and privacy policies.
