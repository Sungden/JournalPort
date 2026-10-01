# JournalPort 1.0.0rc1 release candidate notes

This candidate freezes an installable journal-transfer Skill backed by deterministic audit/planning,
approval-bound M10 transformations, content-preserving M12 operations, independent verification, and
local package verification.

Production profiles are Nature Communications Article 1.2.0, Nature Computational Science Article
1.1.0, and Nature Machine Intelligence Article 1.1.0. All are `PARTIAL`; automation is conservative.

Codex is the tested host. The wheel bundles the portable Skill and requires Core `>=1.0.0rc1,<2`.
Second-host validation is pending. Install with
`python -m pip install journalport-1.0.0rc1-py3-none-any.whl`.

Users upgrading from 0.1 RC builds should create new plans because profile/plan semantics gained
submission-stage support. Historical plans and profiles remain audit evidence. Known limitations are
listed in `docs/CAPABILITY_MATRIX.md`. No tag, registry publication, or release is created by this
preparation step.
