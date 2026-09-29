# Status model

Preserve the exact status emitted by JournalPort. `UNKNOWN` is not `PASS`, a draft is never
`VERIFIED`, `VERIFIED_CANDIDATE` is not submission readiness, and package readiness is only one
of `PACKAGE_READY`, `PACKAGE_READY_WITH_WARNINGS`, `PACKAGE_REQUIRES_MANUAL_REVIEW`,
`PACKAGE_BLOCKED`, or `PACKAGE_VERIFICATION_FAILED`. Summaries may explain a status but must not
rename or upgrade it.
