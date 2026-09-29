# ADR-009: Submission-readiness policy

Status: Accepted for M3  
Date: 2026-09-29

Readiness is a deterministic enum, not a boolean. Precedence is:

1. critical `EVALUATION_ERROR` -> `EVALUATION_FAILED`;
2. any manuscript violation with `BLOCKED` -> `BLOCKED`;
3. conflicted or stale profile/critical rule -> `PROFILE_NOT_VERIFIABLE`;
4. incomplete profile or critical UNKNOWN -> `REQUIRES_MANUAL_REVIEW`;
5. non-critical warning/unknown -> `READY_WITH_WARNINGS`;
6. otherwise -> `SUBMISSION_READY`.

`critical_for_readiness` and formal applicability come only from profile data. Missing M2-era fields
default fail-closed to `UNKNOWN` applicability and non-critical; the profile's PARTIAL status still
prevents verified readiness. CONDITIONAL applicability without a deterministic condition result is
UNKNOWN. M3 never resolves provenance conflicts or upgrades stale evidence.

Readiness covers only represented machine-readable rules. It does not predict editorial acceptance,
scientific quality, novelty, writing quality, statistical validity, or complete publisher coverage.
