# ADR-023: Agent-generated profile status policy

Status: Accepted for M7

Every generated candidate profile is `DRAFT`. Schema-valid, evidence-backed, independently reviewed, conflict-free rules may enter a maintainer review queue, but cannot become `VERIFIED` automatically. Deterministic validation can at most support a later `PARTIAL` proposal. Only the established independent maintainer/evidence workflow may approve production status changes.

Drafts are immutable, hash-addressed run directories outside `journal_profiles/`; collisions fail rather than overwrite.
