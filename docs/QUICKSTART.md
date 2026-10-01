# JournalPort quickstart

Create a Python 3.11+ virtual environment and install the wheel:

If you cloned this repository, install directly with `python -m pip install -e .`.
For formatting rather than audit alone, follow [NC DOCX formatting](NC_DOCX_FORMAT.md).

```bash
python -m venv journalport-env
journalport-env/Scripts/python -m pip install journalport-1.0.0rc1-py3-none-any.whl
journalport-env/Scripts/journalport --version
```

Keep unpublished manuscripts outside Git or in an ignored private directory, then run:

```bash
journalport audit private/manuscript.docx --journal nature-communications \
  --article-type article --profile-version 1.2.0 --output private/audit
```

Review `compliance_report.json`; `PARTIAL` or `UNKNOWN` means manual review, not permission to edit.

For agent mode, copy the installed package's `journalport/data/skills/journal-transfer` directory to
your personal Codex skills directory, refresh skill discovery, and ask: “Transfer this private
manuscript to Nature Communications as an Article at REVISION stage.” The Skill audits and plans
first, obtains author facts/approval, delegates edits to Core, and packages only verified candidates.
