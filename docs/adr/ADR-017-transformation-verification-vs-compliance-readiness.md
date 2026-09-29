# ADR-017: Transformation verification versus compliance readiness

Status: Accepted for M5

`transformation_verification_status` answers whether the candidate faithfully implements the plan without unexpected scientific change or tampering. `compliance_readiness_status` is the fresh M3 assessment under the same pinned profile. They are independent dimensions: a transformation can be `VERIFIED_CANDIDATE` while unresolved, partial, or manual journal rules still require review.

M5 never emits `SUBMISSION_READY`. Package completeness and submission-level readiness remain M6 responsibilities.
