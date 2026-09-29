# Roadmap

Milestones are sequential acceptance gates. Expansion does not compensate for an incomplete gate.

- **M0 — Architecture + Schemas (complete):** public skeleton, six schemas, test philosophy,
  structural/meta-schema checks, and audit.
- **M1 — Manuscript Parsing (complete with conditions):** typed canonical model; DOCX and LaTeX parsers; synthetic fixtures;
  parse/render/reparse preservation tests. No transformation policy.
- **M2 — Journal Profiles:** loader, explicit inheritance, provenance and conflict validation;
  exactly three manually reviewed journal/article profiles.
- **M3 — Compliance Engine:** audit-only deterministic validators and JSON/HTML reports.
- **M4 — Safe Transformation:** plan-first safe/content-preserving operations; approval enforcement.
- **M5 — Independent Verification:** independent reparse, semantic/numeric/citation/asset/manifest
  verification.
- **M6 — Submission Package:** profile-driven package assembly and acceptance tests.
- **M7 — Guideline Extraction Agents:** official-source discovery and `PARTIAL` draft profiles only.
- **M8 — Skills:** tested workflow orchestration; no duplicated truth logic.
- **M9 — Public Release:** documentation, CI, clean install, provenance review, release/Zenodo setup.
- **M10 — JournalComplianceBench:** versioned benchmark after core maturity.

M1 should begin only after M0 schemas pass a Draft 2020-12 meta-schema validator in the supported
development environment and all audit blockers are resolved or explicitly accepted as conditions.

