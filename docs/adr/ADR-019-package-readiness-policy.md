# ADR-019: Package readiness policy

Status: Accepted for M6

Candidate verification, compliance readiness, known package completeness, and profile confidence are separate status dimensions. `PACKAGE_READY` requires a verified candidate, no blocking compliance result, all known critical artifacts, passing integrity/format checks, and a sufficiently complete profile. Missing known requirements block. Unknown or unresolved conditional requirements require manual review and are never treated as optional.

Current partial profiles therefore normally yield `PACKAGE_REQUIRES_MANUAL_REVIEW`, even when every known required artifact is present. This is not a journal acceptance or certification claim.
