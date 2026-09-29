# ADR-026: Profile distribution strategy

Status: Accepted for 0.1.0rc1

## Context

Offline audits need pinned profiles after wheel installation, without automatic network updates.

## Decision

Bundle the curated profile registry in the wheel under package data. Prefer an explicit checkout
profile path when supplied. Never update profiles during install or ordinary execution.

## Consequences

Installed audits work offline and reproduce pinned releases. Profile corrections require a new
profile/package version; a separate signed registry distribution may be evaluated later.
