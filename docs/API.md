# Public Python API — 0.1 release line

`journalport.api` is the supported Python façade. Its `__all__` contract is frozen for the 0.1
release line: `audit`, `plan`, `apply`, `verify`, `package_plan`, `package_build`, `package_verify`,
and `refresh_profile_draft`.

These are typed aliases to the tested domain operations. They accept and return JournalPort's
frozen dataclasses; serialized boundaries are governed by the versioned JSON Schemas. Callers must
resolve a pinned profile and preserve the hash-linked artifacts between stages. Exceptions are
fail-closed input, schema, tamper, or policy failures.

The CLI is preferred for cross-process automation because it writes schema-backed JSON artifacts.
Modules outside `journalport.api` and the documented model/schema contracts are not covered by the
0.1 compatibility promise. This façade does not offer journal-specific helpers, semantic rewriting,
submission, networking, or provider integration.
