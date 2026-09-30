# Release process

JournalPort uses PEP 440 versions; the development candidate is `0.1.0rc2`. Update the single source in
`src/journalport/_version.py`, synchronize citation/release documents, run the release checklist,
build both artifacts, inspect their contents, and install each into a fresh environment.

After the owner selects a canonical repository and approves author metadata, create reviewed
commits, let hosted CI pass, prepare a signed/annotated tag command, and publish a GitHub release.
Only after that should the owner connect the repository to Zenodo and archive the release for a
DOI. Insert the real repository URL and DOI only after they exist. This document authorizes no
push, upload, account creation, tag, or DOI operation.

Canonical source repository: <https://github.com/Sungden/JournalPort>. A GitHub pre-release may be
prepared from `v0.1.0rc1` only after hosted CI passes and the user explicitly approves creation.
