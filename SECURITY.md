# Security policy

JournalPort is pre-release and processes potentially confidential manuscripts. Do not include
manuscript content, author data, provider secrets, or credentials in a public report. A private
security contact remains a public-release metadata blocker.

Security-sensitive surfaces include hostile DOCX ZIP/XML resource exhaustion; LaTeX traversal and
unsafe commands; malicious journal-page prompt injection; provider credentials; profile and plan
tampering; output path escape; and report/package mutation. Controls include strict resource
limits, no TeX/macro execution, confined paths, closed schemas, pinned hashes, draft-only agent
output, approval gates, and independent verification. See `docs/THREAT_MODEL.md` and
`docs/PRIVACY.md`.

The deterministic core is local-first. External manuscript transmission is unnecessary and must be
separately authorized. Supported versions will be listed after the first public release; until
then, report issues against `0.1.0rc1` without assuming backward security support.

