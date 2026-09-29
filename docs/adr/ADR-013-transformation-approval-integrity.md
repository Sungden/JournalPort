# ADR-013: Transformation approval integrity

Status: Accepted for M4  
Date: 2026-09-29

Approvals are external records and production code never self-approves. An approval binds action ID,
canonical plan hash, and proposed-content hash, plus actor, time, status, and optional expiry. Any
change to an action, target, parameters, proposal, finding, profile, or plan invalidates the approval.
Rejected, pending, expired, replayed, wrong-plan, and wrong-action approvals cannot authorize work.

M4 has no semantic executor: even a valid approval for authorial content remains
`MANUAL_ACTION_REQUIRED`. FORBIDDEN_AUTOMATIC actions can never enter the automatic executor.
