# Submission packaging

M6 turns an independently verified candidate and explicitly supplied artifacts into a local, auditable package. It guarantees deterministic planning, bounded discovery, source-hash checks, portable manifests, reproducible logical identity, independent file enumeration, and deterministic readiness decisions. It does not create cover letters, highlights, graphical abstracts, declarations, or other authorial content; submit files to a portal; validate scientific accessibility of data/code; or guarantee editorial acceptance.

The workflow is:

```text
journalport package plan ...
journalport package build submission_package_plan.json --output submission_package/
journalport package verify submission_package/
```

Planning reads a `VERIFIED_CANDIDATE`, its M5 report, its post-transform compliance report, the pinned profile, and only explicitly named auxiliary paths. It emits required, found, missing, conditional, and unknown requirements before any package is built. Missing known required artifacts block building. Unknown and unresolved conditional requirements remain manual-review items.

The deterministic layout separates manuscript, figures, tables, supplementary files, declarations, checklists, other files, and metadata. The manifest uses only relative paths and records artifact identity, hash, size, format, origin, requirement state, and validation result. `PACKAGE_INDEX.md` contains no manuscript text.

Package verification reloads the manifest, enumerates the package again, recomputes every file hash and size, detects missing or undeclared files, checks duplicate identities and unsafe paths, and rechecks the pinned profile and M5 report. It does not trust builder success.

`VERIFIED_CANDIDATE` means the transformation was independently verified. `PACKAGE_READY` additionally means known package requirements and integrity checks pass under a sufficiently complete profile. Current Nature profiles are partial, so a complete known-artifact package normally remains `PACKAGE_REQUIRES_MANUAL_REVIEW`. This is intentional and does not claim official Nature certification or acceptance.
