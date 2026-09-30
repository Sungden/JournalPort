# M10 confidential transformation executor audit

## 1. Implementation status

**M10 = PASS.** JournalPort `0.1.0rc3` performs deterministic local DOCX modifications for explicitly
approved content operations. The synthetic acceptance workflow completed parse → audit → plan →
explicit approval → apply → verify → package plan → package build → package verify. No private user
manuscript was accessed or added to the repository.

## 2. Supported operations

- `REPLACE_ABSTRACT`: replaces only the located Abstract body with author-supplied approved text.
- `INSERT_REQUIRED_SECTION`: inserts approved Author Contributions, Competing Interests, Data
  Availability, or Code Availability immediately before one unambiguous References section.
- `SET_MANUSCRIPT_METADATA`: binds `article_type` to resolved submission context without inserting
  visible prose into the manuscript.
- `NORMALIZE_SECTION_HEADING`: normalizes only controlled administrative heading aliases.
- `NORMALIZE_OUTPUT_FILENAME`: retained safe container-name operation.

`MOVE_EXISTING_ADMIN_SECTION` remains optional and is not implemented in v1.

## 3. Unsupported operations

Scientific rewriting/generation, title rewriting, arbitrary section renaming, references, citations,
equations, figures, tables, tracked changes, comments, layout reconstruction, style overhaul, and
image conversion remain manual or forbidden automatic operations. Unsupported/blocking DOCX
content prevents editing.

## 4. Approval model

Content operations require an explicit approval artifact plus a separately supplied local payload.
The approval hashes an envelope containing the operation, parameters, target state, target object
IDs, and exact UTF-8 payload hash. Its `plan_hash` binds the source artifact hash, canonical source,
profile, compliance report, target IDs, and precondition state. A changed payload, action, plan,
source, profile, report, or canonical manuscript invalidates execution. Running `apply` alone is not
approval.

## 5. Authorized-delta verification

The independent verifier derives allowed changes only from action logs whose status is `APPLIED`.
It masks exactly those Abstract or administrative-statement regions, then compares all remaining
scientific snapshots. Observed semantic deltas are compared with the allowed set; unexpected title,
body, number, equation, citation, reference, figure, table, asset, unsupported-content, or statement
changes fail verification.

## 6. DOCX editing strategy

The executor uses standard-library ZIP and ElementTree processing. It modifies only
`word/document.xml`, copies every unrelated ZIP member, reparses the candidate, and leaves the
source untouched. Abstract replacement uses exact parser locators. Administrative insertions require
one References locator and reuse its paragraph properties for the heading. Duplicate or ambiguous
targets block.

## 7. Original-file preservation

The source hash is checked before planning, immediately before execution, and after execution. The
candidate is always a separate path. In the acceptance run the source remained byte-identical.

## 8–11. Privacy, network, logging, and temporary files

Core processing is local-only and contains no telemetry or network client. A socket-blocked complete
workflow passes. Logs contain action/rule/object IDs, operation/status, source/candidate/payload and
approval hashes, timestamps, executor version, and structural error categories; they exclude payload
and manuscript text, emails, XML, captions, references, and paths. Temporary DOCX packages live
under the selected output directory, use mode 0600 where supported, are atomically renamed, and are
removed on success or failure. The threat model is documented in
`docs/security/CONFIDENTIAL_MANUSCRIPT_THREAT_MODEL.md`.

## 12. Dependency audit

M10 editing adds no dependency. It uses `zipfile`, `xml.etree.ElementTree`, `tempfile`, `os`, and
`pathlib`. These standard-library modules do not perform network access or telemetry. The sole
production dependency, local schema validator `jsonschema[format]`, is not invoked by DOCX editing,
does not receive manuscript content through this workflow, and does not require network access.
No office application, subprocess, browser, SaaS converter, or model provider is invoked.

## 13. Security tests

Synthetic tests block socket creation across the complete workflow, scan log/manifest metadata for a
secret marker, verify output remains outside repository source directories, check original SHA-256,
verify wrong/missing approval behavior, and assert successful and failed runs leave no temporary
manuscript files. Hosted CI needs only generated synthetic fixtures.

## 14–15. Synthetic result and quality gates

- Source SHA-256: `sha256:376464a578f42a04beb8e2a5059145fb705d5675e57b8a1e46a2dda25cd5db15`
- Candidate SHA-256: `sha256:7bc3ecdbc6751261d0a18928e35ef2eaae24afda115575b5465f9cc0f16777a0`
- Source unchanged: **yes**
- Candidate changed: **yes**
- Authorized delta count: **4**
- Unexpected delta count: **0**
- Network access required: **no**
- Confidential content present in logs: **no**
- Temporary content cleaned: **yes**
- Verification status: **VERIFIED_CANDIDATE**
- Package integrity verification: **passed** (profile-level unknowns may still require manual review)
- Test suite: **195 tests plus 60 subtests passed**
- Ruff lint/format, mypy strict scope, compileall, and `git diff --check`: **passed**

Hashes identify one deterministic synthetic acceptance artifact pair generated during this audit;
they do not identify or derive from any user manuscript.

## 16. Remaining risks

The XML serializer may normalize namespace presentation inside the edited XML part, although semantic
objects are independently reparsed and verified. Complex blocking DOCX constructs remain uneditable.
Approval sidecar payloads are confidential local files managed by the user. Secure erasure and host
backup behavior are outside the process boundary. Administrative placement currently requires one
unambiguous References section. Approved replacement text is accepted verbatim and is never
scientifically generated or reviewed by JournalPort.

## 17. Exact release readiness

The M10 implementation satisfies the confidential local executor gate and is ready for review as
development version `0.1.0rc3`. It is not tagged, released, or published. `v0.1.0rc1` remains
unchanged. A private manuscript rerun must be initiated separately by the user on their own machine
or server.
