# Private manuscript guide

Store unpublished manuscripts outside the repository or in an ignored directory such as `private/`,
`paper/`, or `real-run/`. Confirm with `git check-ignore`. Never copy them into tests, fixtures,
examples, docs, CI, issues, or public logs. Protect proposals, approval payloads, sessions, candidates,
ledgers, and packages like the manuscript and maintain appropriate backups.

`LOCAL_ONLY` avoids external-model disclosure. `CODEX_HOSTED` permits only task-required objects to
reach the hosted model; it does not imply provider invisibility or prove provider retention behavior.
JournalPort records disclosed object identifiers and hashes, not prompt/manuscript plaintext. Consult
the provider's policies for upstream retention and access.

JournalPort verifies local hashes, approval binding, expected deltas, preservation invariants,
artifact hashes, and package inventory. It cannot prove author-supplied facts, upstream provider
retention, or editorial acceptance. Cleanup is not automatic. Delete private runtime directories only
under the applicable institutional retention/backup policy. JournalPort does not claim encryption at
rest.
