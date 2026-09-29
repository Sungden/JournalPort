# Contributing

Changes must preserve provenance, fail-closed behavior, deterministic verification, explicit
semantic approvals, and independent verification. Use a focused branch and add tests. Contributions
may add profiles, validators, synthetic fixtures, parser support, or improve Skills.

Profile changes require official evidence, explicit status and verification metadata, synthetic or
open fixtures, registry hashes, and profile-specific tests; see `docs/CONTRIBUTING_PROFILES.md`.
Skills must orchestrate public core interfaces and preserve approval/production-profile gates; see
`docs/CONTRIBUTING_SKILLS.md`. Never commit confidential manuscripts, secrets, or publisher assets
without redistribution permission.

Install and run the complete checks:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
mypy
```

