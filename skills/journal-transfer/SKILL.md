---
name: journal-transfer
description: Create and independently verify a content-preserving journal-transfer candidate; use when safe automatic changes are allowed and semantic changes must stop for author action.
---

# Journal transfer

Use JournalPort through `scripts/run.py` for audit → plan → safe apply → independent verification. The script inspects
the schema-backed plan and stops before apply if any action is `AUTHOR_APPROVAL_REQUIRED` or
`FORBIDDEN_AUTOMATIC`. Existing artifacts may be resumed only after the core validates their
hashes and versions.

Never shorten an abstract, rewrite a title, remove references, alter claims/results/numbers, create
declarations, or invent author metadata. Approval does not add a semantic executor. Verification is
independent of transformation; failure terminates the workflow. The strongest result is
`VERIFIED_CANDIDATE`, never submission readiness.

Return exact action classes, proposed manual actions, verification status, hashes, artifacts, and
remaining work. Read [transformation policy](references/transformation-policy.md) for action routing
and [verification policy](references/verification-policy.md) for terminal behavior. The shared
approval, status, safety, and privacy policies are normative.
