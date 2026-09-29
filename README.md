# JournalPort

Repository: [github.com/Sungden/JournalPort](https://github.com/Sungden/JournalPort)

**A provenance-aware, verifiable, content-preserving infrastructure for journal transfer and
submission compliance.**

JournalPort is an early-stage, local-first Python project. It turns pinned journal guidance into
schema-backed profiles, audits DOCX/LaTeX manuscripts, plans narrowly supported transformations,
independently verifies candidates, and builds submission packages. Four reusable Agent Skills
orchestrate these tested capabilities while keeping semantic edits and uncertain requirements
human-in-the-loop. It does not submit manuscripts and is not affiliated with any journal.

It exists because journal requirements are fragmented and ambiguous. JournalPort keeps rules tied
to evidence, uses deterministic checks where possible, and prevents a transformer from declaring
its own work correct.

```text
Official Guidelines → Journal Profiles → Manuscript Parsing → Compliance Audit
       → Safe Transformation Plan → Independent Verification → Submission Package
                 Agent Skills orchestrate the public CLI/API above this flow
```

## Quickstart

Requires Python 3.11 or newer.

Install the public release candidate directly from its verified GitHub release asset:

```bash
python -m pip install https://github.com/Sungden/JournalPort/releases/download/v0.1.0rc1/journalport-0.1.0rc1-py3-none-any.whl
journalport --version
journalport --help
```

Expected version output is `journalport 0.1.0rc1`. JournalPort is not yet published on PyPI, so
`pip install journalport` is not currently supported.

For the complete source checkout, bundled examples, and Agent Skills:

```bash
git clone https://github.com/Sungden/JournalPort.git
cd JournalPort
python -m pip install -e .
journalport audit examples/quickstart/article.tex \
  --journal nature-communications --output audit-result
```

Inspect `audit-result/compliance_report.json`. The public rc1 GitHub Actions matrix passes on Python
3.11, 3.12, and 3.13. The deterministic CLI/core and bundled profiles are included in the wheel;
the four Agent Skills are distributed in the source repository and source archive, not the wheel.

See [Agent Skills](docs/SKILLS.md), [architecture](ARCHITECTURE.md), and the reproducible
[examples](examples/skills). The deterministic core works without a model provider; the empty
`agent` extra reserves a compatibility surface without adding an SDK dependency.

## Trust model

- Rules retain official-source provenance and unknowns fail closed.
- The compliance core is offline and deterministic.
- Automatic actions are restricted to supported content-preserving operations.
- Candidate and package verification are independent of their builders.
- Semantic changes, profile verification, and missing author information require people.

These are tested engineering properties, not a guarantee of acceptance or complete journal
compliance.

## Current profile coverage

| Journal | Article type | Profile status | Last verified |
|---|---|---|---|
| Nature Communications | Article | PARTIAL | 2026-09-29 |
| Nature Computational Science | Article | PARTIAL | 2026-09-29 |
| Nature Machine Intelligence | Article | PARTIAL | 2026-09-29 |

## Benchmarks

On the M7 three-journal curated extraction benchmark: precision **100%**, recall **90.48%**, and
hallucinated-requirement rate **0%**. These numbers describe only that fixed benchmark and do not
generalize to all journals or live-provider behavior. See the
[M7 benchmark audit](docs/audits/M7_AUDIT.md).

## Development and citation

Install with `python -m pip install -e ".[dev]"`, then run `pytest`, `ruff check .`,
`ruff format --check .`, and `mypy`. Citation metadata is in [CITATION.cff](CITATION.cff); no DOI
exists yet. Apache-2.0 covers original code and documentation; third-party journal material may
have separate terms; see [third-party notices](THIRD_PARTY_NOTICES.md).

The current public release is
[JournalPort 0.1.0rc1](https://github.com/Sungden/JournalPort/releases/tag/v0.1.0rc1). Historical
engineering and release evidence is retained under [`docs/audits/`](docs/audits/).

