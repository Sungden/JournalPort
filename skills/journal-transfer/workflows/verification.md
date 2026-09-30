# Independent verification

After Core apply, run `journalport verify` independently. Continue only when
`transformation_verification_status` is `VERIFIED_CANDIDATE`, `unexpected_changes` is empty, and
`failure_reasons` is empty. Otherwise set the session to BLOCKED, explain the concrete delta, and stop;
approval never overrides verification. Re-audit the candidate and distinguish author work, submission
tasks, unsupported behavior, profile uncertainty, and genuine noncompliance.
