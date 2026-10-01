# JournalPort

JournalPort is an installable, agent-compatible journal-transfer system backed by a deterministic,
provenance-aware transformation and verification engine. It audits DOCX and supported LaTeX inputs,
plans narrowly scoped changes, binds author approvals, verifies candidates independently, and builds
local submission packages.

It is not a generic Word formatter, an autonomous scientific writer, a submission-portal bot, or a
guarantee of editorial acceptance.

```text
Agent Skill → JournalPort Core → deterministic transformation → independent verification
```

## Install and start

Python 3.11 or newer is required:

From a source checkout, install with `python -m pip install -e .`.
For Nature Communications Article DOCX formatting, see [the full-format guide](docs/NC_DOCX_FORMAT.md).
Pin profile `1.3.2`; select the submission stage explicitly. LibreOffice is a separate local prerequisite
for rendering. This is a conservative release candidate, not universal one-click journal compliance.

```bash
python -m pip install journalport-1.0.0rc1-py3-none-any.whl
journalport --version
journalport audit --help
journalport audit manuscript.docx --journal nature-communications \
  --article-type article --profile-version 1.2.0 --output private/audit
```

See the [Quickstart](docs/QUICKSTART.md), [private-manuscript guide](docs/security/PRIVATE_MANUSCRIPT_GUIDE.md),
and [single public synthetic example](examples/public-synthetic).

## Trust model

- Rules retain official-source provenance; uncertain rules fail closed.
- Rules and transformation targets can be submission-stage aware.
- Semantic edits require explicit author approval.
- Verification is independent of transformation execution.
- Private runtime paths are excluded from distributions.

An implemented operation is not executable for every journal. It also requires a VERIFIED target,
an applicable stage, support for the exact target, and safe input preconditions.

## Production profile coverage

| Journal | Article type | Profile | Status | Stage aware | Automation |
|---|---|---:|---|---|---|
| Nature Communications | Article | 1.3.2 | PARTIAL | Yes | Verified formatting targets; conditional ordering |
| Nature Computational Science | Article | 1.1.0 | PARTIAL | Legacy | Conservative/manual |
| Nature Machine Intelligence | Article | 1.1.0 | PARTIAL | Legacy | Conservative/manual |

`PARTIAL` does not mean complete journal compliance. Automation expands only with official evidence.

## Supported boundary

Core supports DOCX parsing, supported-subset LaTeX audit parsing, audit/planning, approval binding,
provenance, independent verification, package building, and package verification. M10 implements
`REPLACE_ABSTRACT`, `INSERT_REQUIRED_SECTION`, `NORMALIZE_SECTION_HEADING`, and
`SET_MANUSCRIPT_METADATA`. M12 implements `REORDER_ADMIN_SECTIONS`, `TITLE_PAGE_RESTRUCTURE`,
`FIGURE_CAPTION_NORMALIZATION`, and `EXTRACT_FIGURES_TO_SEPARATE_FILES`, subject to the gates above.

Unsupported behavior includes generating missing scientific captions, deleting apparently uncited
references, arbitrary scientific-section changes, unrestricted rewriting/shortening, unsafe reference
conversion, equation/number/pixel edits, arbitrary table edits, full LaTeX transformation, submission
site automation, and peer-review-response automation. See [capabilities](docs/CAPABILITY_MATRIX.md).

## Agent Skill

The wheel bundles `journal-transfer` under `journalport/data/skills/journal-transfer`. Copy that
directory to the configured personal Codex skills directory. It requires Core `>=1.0.0rc1,<2`.
Codex is tested; second-host validation is pending.

JournalPort is Apache-2.0 licensed and is not affiliated with any journal or publisher.
