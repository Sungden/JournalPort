# Verification policy

The verifier must independently reparse source and candidate, validate plan/log/manifest hashes,
rerun compliance, and check preservation fingerprints. Any mismatch or status other than
`VERIFIED_CANDIDATE` stops the workflow and must remain visible.
