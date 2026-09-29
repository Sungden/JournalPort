# M9.6 release audit — JournalPort 0.1.0rc1

## Status

**PASS.** JournalPort `0.1.0rc1` is published as a public GitHub pre-release. PyPI and Zenodo
remain unpublished, and no MCP, UI, journal expansion, or scientific-profile change was made.

## Release provenance

- Release version: `0.1.0rc1`
- Release source commit: `0cedf50e2d5b7954f757c13df5bfa523fdc23a27`
- Annotated tag: `v0.1.0rc1`
- Tag object: `3861dec7568a38bf5b1d3c1b87fe2ec1f5fe68d2`
- Tag target: `0cedf50e2d5b7954f757c13df5bfa523fdc23a27`
- GitHub release: <https://github.com/Sungden/JournalPort/releases/tag/v0.1.0rc1>
- Public: yes
- Pre-release: yes
- Draft: no

The final pre-tag hosted CI run was
[36576683689](https://github.com/Sungden/JournalPort/actions/runs/36576683689). It completed
successfully at the release source commit for Python 3.11, 3.12, and 3.13.

## Release tests and builds

- pytest: 156 passed
- Ruff check and format check: passed
- mypy strict configured scope: 69 source files passed
- compileall, `git diff --check`, CLI version, and guideline-extraction benchmark: passed
- Wheel and sdist rebuilt from the clean release source: passed
- Fresh wheel install, CLI, benchmark, schema/profile/benchmark resource lookup: passed
- Fresh sdist package build/install, version, and resource lookup: passed
- Public download and post-upload hash verification: passed

Release assets:

| Asset | SHA-256 |
|---|---|
| `journalport-0.1.0rc1-py3-none-any.whl` | `e93acd166f3df453e270399bed3b620fd69c2e614e8372ba85ddf5e4014ff58f` |
| `journalport-0.1.0rc1.tar.gz` | `93ab280725f411e4a1f89b6b586e276648b066004358707d443ca65876f810ac` |

Both assets were built from the exact working tree committed as the release source before the tag
was created. Downloaded public assets reproduced these hashes.

## Scientific and public metadata

The initial curated production profiles remain unchanged and explicitly `PARTIAL`:

- Nature Communications — Article — `PARTIAL`
- Nature Computational Science — Article — `PARTIAL`
- Nature Machine Intelligence — Article — `PARTIAL`

The frozen initial three-journal guideline-extraction benchmark reports precision 100%, recall
90.48%, F1 95.00%, and hallucinated-requirement rate 0%. These results are limited to this initial
curated benchmark and are not generalized to arbitrary journals or publishers.

`CITATION.cff` records author `Sungden`, version `0.1.0rc1`, release date `2026-09-29`, Apache-2.0,
and the canonical repository. It publishes no email, ORCID, or DOI. Git identity remains separate
from citation identity.

`SECURITY_CONTACT_PENDING` remains because no public security address was authorized. The release
does not claim a complete production security-response infrastructure. Scans found no credentials,
provider tokens, machine-specific paths, tracked caches/build products, or private manuscripts;
manuscript-like tracked files are synthetic test fixtures.

## Post-release state and limitations

This file is a post-release documentation record. The release tag intentionally remains on the
reviewed source commit rather than this later audit-only commit and must not be moved.

Remaining limitations include three initial profiles only, all production profiles being PARTIAL,
unsupported complex DOCX/LaTeX structures, no automatic semantic rewriting, mandatory human review
for conditional/unknown requirements, a small benchmark, no real-provider variability benchmark,
no submission-portal automation, no PyPI/Zenodo publication, and no MCP implementation. Recommended
repository settings remain protection of `master`, required CI, and blocked force pushes.
