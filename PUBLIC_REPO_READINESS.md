# Public repository readiness — 0.1.0rc1

## Engineering readiness

**RELEASE_CANDIDATE_READY.** Full tests and quality gates pass. Wheel and sdist build, content
inspection, fresh installation, bundled-resource lookup, benchmark reproduction, and installed
parse→audit→plan→apply→verify→package workflow pass.

## Documentation readiness

README, API/CLI contracts, architecture/ADR index, profiles/Skills contribution guides, examples,
privacy/threat model, release procedure, release notes, and checklist are present. Historical audits
remain at the root for rc1; migration to `docs/audits/` is intentionally deferred.

## Packaging and testing readiness

Version is `0.1.0rc1` from one Python source. Wheel bundles schemas, the pinned profile registry,
and benchmark snapshot; Skills are repository/sdist artifacts by ADR-025. CI requires no secrets
and its hosted Python 3.11–3.13 matrix passes all required gates.

## Security, licensing, and data readiness

Apache-2.0 scope and third-party boundaries are documented. Guideline evidence uses URLs, hashes,
metadata, and short excerpts rather than copied pages. Secret and machine-path scans pass; the sole
email-pattern hit is synthetic URL userinfo in a security test. No private manuscript was found.

## Citation and benchmark readiness

`CITATION.cff` is structurally checked, names `Sungden` as the provisional software author, uses
the user-confirmed repository URL, and does not publish the Git email, invent ORCID/DOI, or claim a
release date. Formal
author form remains subject to user approval. The versioned three-journal benchmark is reproducible
with `journalport benchmark guideline-extraction` and retains its narrow-scope disclaimer.

## Git provenance and hosting readiness

Repository-local commit identity is configured as user-supplied `Sungden` identity; its email is
intentionally omitted from public documentation.
Reviewed logical initial commits and their history are recorded in `M9_AUDIT.md`; hosting evidence
is recorded in `M9_5_HOSTING_AUDIT.md`. The reviewed history is pushed to the canonical remote and
hosted CI passes. No tag, GitHub Release, PyPI upload, or Zenodo action was performed.

Canonical hosting is <https://github.com/Sungden/JournalPort>. Remaining user-controlled gates are
approval of final citation author representation and whether any email/ORCID is public, provision
of a private security contact, and approval of a release tag/pre-release.

## Release recommendation

The hosted release candidate is ready for review. Creating a public pre-release remains blocked
until the user-controlled metadata and tag/release gates above are approved.
