---
name: journal-audit
description: Run a local, read-only manuscript compliance audit against a pinned JournalProfile; use for evidence-backed findings without changing the manuscript.
---

# Journal audit

Use `scripts/run.py`, which calls the stable `journalport audit` command and consumes its JSON
artifacts. Require the manuscript, journal, article type, profile version, and profile directory.
The core resolves the pinned profile, parses the file, and evaluates deterministic rules.

Do not modify or copy-edit the manuscript. Fail closed on missing/stale/conflicted profiles,
blocking parser findings, or invalid artifacts. Preserve `UNKNOWN` and manual-review states exactly.
Report target, profile status, audit status, blocking findings, warnings, unknown/manual items,
generated artifacts, and the next safe action. Cite finding, rule, and official evidence when asked
why. See [profile policy](references/profile-policy.md) and the shared status/failure/privacy rules.
