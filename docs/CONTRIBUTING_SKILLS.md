# Contributing Agent Skills

Skills orchestrate the public JournalPort CLI/API; they do not implement parsers, rule evaluation,
counting, transformations, or verification. Keep `SKILL.md` concise and route conditional detail to
references. Deterministic helpers must be thin wrappers.

A skill may not bypass `AUTHOR_APPROVAL_REQUIRED`, execute `FORBIDDEN_AUTOMATIC`, silently edit
scientific content, promote draft profiles, overwrite production profiles, reinterpret `UNKNOWN`
as `PASS`, fabricate author artifacts, or continue after failed verification. Add registry metadata,
structured run records, golden workflow tests, and adversarial stop tests. Core must remain usable
when the skill is removed.
