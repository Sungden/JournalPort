# Confidential manuscript threat model

## Security property

JournalPort treats unpublished manuscripts, author identity and contact details, scientific claims,
figures, tables, formulas, references, and approved transformation payloads as confidential assets.
The trust boundary is the user's local machine or server. Everything outside that boundary is
untrusted for manuscript-derived content.

> JournalPort core manuscript processing does not require external network access.

The parse, audit, plan, approval, apply, verify, and package path is deterministic and local. It does
not invoke HTTP clients, browsers, webhooks, remote models, conversion services, telemetry, cloud
storage, or remote logging. Guideline discovery is a separate, explicit workflow and is not called
by manuscript transformation.

## Threats and controls

| Threat | Control |
|---|---|
| Accidental network transmission | Core modules contain no network calls; an end-to-end test blocks socket creation. |
| Telemetry or analytics | No telemetry SDK or analytics dependency is present. |
| Debug/log leakage | Routine logs contain IDs, operation/status values, hashes, timestamps, and error categories—not manuscript or payload text. |
| Exception leakage | Executor errors use structural categories and never interpolate target text or XML. |
| Temporary-file leakage | DOCX temporary packages are created under the selected output directory, mode 0600 where supported, atomically renamed, and removed in `finally`. |
| Git/CI leakage | Only generated synthetic DOCX packages are used by tests; private/runtime directories and common private manuscript suffixes are ignored. |
| Path or filename leakage | Transformation logs omit paths and filenames. Plans necessarily identify the local input path and must be handled as local confidential metadata. |
| Unauthorized content changes | Content operations require an approval bound to the plan and exact payload hash; source/plan/profile/report hashes are checked before editing. |
| Stale approval or source | Any changed plan, source artifact, canonical manuscript, target state, or payload invalidates execution. |
| Package reconstruction damage | Direct OpenXML editing changes only `word/document.xml`; unrelated ZIP members are copied unchanged. Independent verification reparses the result. |
| Stale output directories | Candidate paths are confined to the selected output root; callers should use a fresh protected output directory and securely remove obsolete outputs. |
| Third-party behavior | The transformation runtime uses Python standard-library XML/ZIP/filesystem modules. `jsonschema` is used for local validation only and is not invoked by the editor. |

## Dependency and process audit

The production dependency set contains `jsonschema[format]`. It does not perform network requests
for JournalPort's bundled schemas, emit telemetry, invoke subprocesses, or write manuscript caches.
M10 OpenXML editing uses only `zipfile`, `xml.etree.ElementTree`, `tempfile`, `os`, `pathlib`, and
other standard-library modules. The runtime does not invoke office applications or document
conversion subprocesses. Development-only pytest, Ruff, mypy, and build tooling never receive real
manuscripts in hosted CI.

## Residual risks

- The operating system, filesystem backup software, endpoint security products, and user-selected
  output location are outside JournalPort's control.
- Plans contain local paths and structural hashes; approval sidecar payload files contain approved
  text and must be protected by the user.
- Python exceptions from lower-level ZIP/XML libraries are reduced to error categories by the
  executor, but callers embedding the library must avoid logging arbitrary input objects.
- Secure deletion cannot be guaranteed on copy-on-write filesystems or SSDs. JournalPort performs
  deterministic cleanup, not forensic erasure.
- Complex DOCX features marked blocking remain fail-closed rather than being edited.
