# JournalPort Agent Skills

The repository ships four host-neutral orchestration skills, each version 1.0.0:

- `journal-profile`: official-source discovery or offline replay into an immutable draft review bundle.
- `journal-audit`: read-only audit against a pinned profile.
- `journal-transfer`: approval-gated planning, safe application, and independent verification.
- `submission-package`: package planning/building/verification from author-supplied artifacts.

Install JournalPort with `python -m pip install .`. Copy or link the desired directory under
`skills/` into a compatible host's skill directory, or point the host at this repository. Invoke
the skill by name and provide the inputs described in its `SKILL.md`. The deterministic wrapper in
each `scripts/run.py` is also executable with Python; use `--help` for its stable arguments.

All skills require JournalPort `>=0.1.0rc1,<0.2`; compatibility and outputs are registered in
`skills/registry.yaml`. They call public CLI commands and emit `skill_run.json`, whose artifact
hashes and statuses are machine-readable. They do not contain journal-specific rules.

Safety boundaries: local-first processing, exact status preservation, draft-only profile refresh,
approval gates for semantic changes, independent verification, and no fabrication of author
materials. Missing/unknown/conflicted evidence or failed verification stops the applicable flow.
MCP, submission portals, GUI automation, and external manuscript upload are outside this release.

Reproducible command outlines using synthetic fixtures are in `examples/skills/`. Paths should be
adapted to the local checkout; generated outputs are intentionally not committed.
