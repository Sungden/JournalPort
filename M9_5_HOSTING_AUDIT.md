# M9.5 hosting audit — 0.1.0rc1

## Status

**PASS.** The release-candidate source is hosted at
<https://github.com/Sungden/JournalPort> on the `master` branch. No tag, GitHub Release, PyPI
upload, or Zenodo action was performed.

## Repository and provenance

- Canonical remote: `https://github.com/Sungden/JournalPort.git`
- Reviewed hosting-validation commit: `9aaf13b6367718896c13eeca67cb1a50e17bdc6d`
- Repository-local Git identity: user-supplied name `Sungden`; email retained only in Git metadata
- History: nine reviewed commits from deterministic compliance core through hosting portability fixes
- The initial remote was empty; local reviewed history was pushed without rebasing or rewriting it

The Git commit identity is not treated as citation-author authority. `CITATION.cff` retains the
provisional author name `Sungden`, publishes no email or ORCID, and uses only the user-confirmed
canonical repository URL.

## Validation

Local validation on the hosting-validation source:

- pytest: 156 passed
- Ruff check and format check: passed
- mypy strict configured scope: 69 source files passed
- compileall and guideline-extraction benchmark: passed
- `git diff --check`: passed
- prior M9 wheel/sdist builds, clean installs, content inspection, and installed full workflow: passed

Earlier hosting-validation run
[36573324369](https://github.com/Sungden/JournalPort/actions/runs/36573324369) passed for Python
3.11, 3.12, and 3.13, including tests, Ruff, mypy, compileall, and benchmark reproduction. Final
HEAD validation run
[36574145167](https://github.com/Sungden/JournalPort/actions/runs/36574145167) passed the same matrix
at commit `d563cfc13f7384e8b913ed7813ef66e50ae72a8b` and is the authoritative M9.5 hosted-CI result.

Two earlier hosted failures were resolved rather than waived: test-package imports were made
checkout-portable; profile hashes now use declared canonical JSON hashing independent of line
endings; and dataclass instance narrowing is portable under Linux mypy. These changes do not alter
journal-rule provenance, profile status, scientific content, or verification semantics.

## Public surface audit

- README and project metadata use the confirmed repository URL.
- `CITATION.cff` does not publish an email, ORCID, DOI, or unapproved release date.
- `SECURITY.md` keeps `SECURITY_CONTACT_PENDING`; no contact was invented.
- Source-tree scans found no machine-specific path or credential material.
- Journal profiles remain `PARTIAL`; the README does not claim complete journal compliance.

## Remaining release gates

M9.5 establishes hosting and a passing release-candidate CI baseline. A GitHub pre-release is
technically ready but remains uncreated pending explicit approval of the release tag and release
action. Formal citation-author representation, optional public email/ORCID, a private security
contact, branch-protection settings, and later PyPI/Zenodo publication remain user-controlled.
