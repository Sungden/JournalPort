# M0 Audit — Architecture + Schemas

Date: 2026-09-29  
Milestone: M0 only  
Overall status: **PASS WITH CONDITIONS**

M0's required architecture, schemas, test strategy, public-repository skeleton, and executable
validation exist. No parser, renderer, crawler, journal profile, UI, CLI, MCP server, or Agent Skill
was implemented. Conditions below are deliberate M1/M2 work, not silently treated as complete.

## Evidence

- `python -m pytest -q`: **PASS — 5 tests, 12 subtests**.
- All six JSON documents parse and pass `Draft202012Validator.check_schema`.
- Approval-gate negative test: a semantic action labeled `AUTHOR_APPROVAL_REQUIRED` with
  `approval_required=false` and `NOT_REQUIRED` is rejected.
- `ruff check .`: **PASS**.
- Validation environment: CPython 3.14.6; isolated `.venv`; `jsonschema` 4.26.0; pytest 9.1.1;
  Ruff 0.16.9. The project itself has zero runtime dependencies at M0.

## 1. Architecture summary — PASS

The architecture is a deterministic, model-independent core with ports for formats and external
services. Canonical representation, profile resolution, compliance, plan-first transformation,
rendering, and independent file-based verification are separate boundaries. Agent, CLI, and MCP
interfaces remain optional adapters.

## 2. Schema relationships — PASS

```text
JournalProfile --contains--> ComplianceRule
       |                         |
       +----profile identity-----+----> ComplianceReport findings

CanonicalManuscript --stable IDs--> ComplianceReport affected objects
       |                              |
       +------------------------------+--> TransformationPlan actions/approvals
                                               |
input/output artifacts + versions + hashes ----+--> Manifest
```

All schemas are version `1.0.0`, use Draft 2020-12, close top-level objects, and have stable public
IDs. Cross-object uniqueness, referential integrity, aggregate counts, profile resolution, and
readiness logic intentionally require semantic validators; JSON Schema alone cannot prove them.

## 3. Unresolved architectural risks — CONDITIONAL

- Canonical JSON serialization and hash scope are not yet specified, so logical reproducibility
  across serializers is not proven.
- Schema migration/deprecation policy is only implicit in semantic versioning.
- Independent verification is architecturally separated but not yet process-isolated.
- JSON Schema can constrain records but cannot establish the truth of evidence or approvals.

Required action: define canonical serialization, typed models, migration policy, semantic
validators, and verifier test seams before M1/M2 contracts are declared stable beyond `1.0.0`.

## 4. DOCX parsing risks — CONDITIONAL

Tracked changes, fields, content controls, OMML, drawings, floating objects, comments, footnotes,
relationship targets, cross-references, embedded files, and style-derived semantics can be lost by
high-level libraries. M1 must inspect Open XML directly when abstractions are lossy, preserve raw
fragments for unsupported constructs, emit stable source locators, and block round trips containing
unpreserved scientific content.

## 5. LaTeX parsing risks — CONDITIONAL

Macro expansion, custom classes, included files, BibTeX/Biber variants, catcodes, generated
content, packages, and arbitrary execution prevent a universally safe parse. M1 must forbid shell
escape, use bounded include roots, retain source spans/raw nodes, define a supported subset, and
fail closed outside it. Compilation must not be treated as semantic preservation proof.

## 6. Reference handling risks — CONDITIONAL

Reference strings may be incomplete or ambiguous; DOI metadata can disagree with manuscripts;
numeric labels are presentation, not identity. M1/M2 should preserve raw references alongside
structured CSL JSON/BibTeX/RIS, assign stable IDs, and distinguish parsing confidence, formatting
correctness, and factual validation. External metadata lookup must be explicit and privacy-aware.

## 7. JATS adoption decision — PASS

Adopt JATS semantics selectively, not the full vocabulary as the internal model. This keeps the
canonical form practical for DOCX/LaTeX while leaving room for a tested JATS adapter. Unsupported
constructs are recorded as blocking hashed fragments rather than discarded. Revisit full mapping
only with lossless round-trip evidence.

## 8. CSL integration decision — PASS

Use an established CSL processor for reference rendering; do not implement styles from scratch.
Pin CSL processor/style versions and hashes in the manifest. Keep style conformance separate from
bibliographic factual correctness. CSL assets retain their own licenses.

## 9. Journal profile inheritance design — CONDITIONAL

Publisher, journal, and article-type layers are explicit version-pinned parents with deterministic
precedence and a future resolution trace. Overrides must identify superseded rules and carry their
own provenance. Unresolved authoritative disagreement becomes `CONFLICTED`. The schema represents
composition; M2 must implement cycle, duplicate precedence, rule collision, and provenance-chain
validators before any profile can become `VERIFIED`.

## 10. Agent/core boundary — PASS

Agents may discover sources, extract candidate rules, identify ambiguity, and propose revisions.
They cannot be the sole authority for counts, cross-reference checks, content preservation,
approval, or readiness. Agent-generated profiles remain `PARTIAL` until independently reviewed and
validated. No LLM provider is a core dependency.

## 11. Likely dependencies — CONDITIONAL

| Candidate | Purpose | Typical license | Maintenance/replacement risk |
|---|---|---|---|
| `jsonschema` | Contract validation | MIT | Low / low |
| `pydantic` or `attrs` | Typed runtime models | MIT | Low / medium; choose in M1 |
| `python-docx` plus direct Open XML | DOCX access | MIT | Medium / high for edge cases |
| `lxml` | XML parsing/canonicalization | BSD-3-Clause | Low / medium |
| `pylatexenc` or parser evaluation | LaTeX tokenization | MIT | Medium / high |
| `citeproc-py` or external CSL processor | CSL rendering | BSD-2-Clause or processor-specific | Medium / medium |
| Pillow | image metadata | HPND | Low / low |

No parser/renderer dependency is selected at M0. Before adoption, verify current license,
maintenance, security, format fidelity, Python support, and replacement cost; this table is not a
license audit.

## 12. Licensing risks — CONDITIONAL

Apache-2.0 is selected for original code/docs. Publisher instructions may be copyrighted; profiles
should store minimal evidence excerpts plus hashes/locators, not copied pages. Templates, CSL
styles, journal logos, fixtures, and external metadata require per-asset attribution and license
records. The placeholder repository URL and contributor/security contacts must be corrected before
release. The included Apache notice is sufficient for M0 source but release packaging needs a
NOTICE/third-party inventory decision.

## 13. Testability assessment — PASS

Boundaries are injectable and artifacts have stable IDs, versions, evidence references, and hashes.
Schemas are machine-tested without network access after installation. The test strategy defines
unit, schema, parser, round-trip, integration, regression, adversarial, and acceptance levels with
independent oracles. M1 must add valid/invalid example instances for every schema and property-based
ID/reference tests; current tests primarily prove schema structure and meta-schema validity.

## 14. Public-release readiness gaps — CONDITIONAL

The repository has the required public-facing file set, license, citation stub, and source layout,
but is not release-ready. Gaps include real governance/security contacts, canonical repository URL,
CI, supported Python matrix, lock/reproducible environment policy, full Apache license text review,
documentation site, release automation, provenance contribution workflow, accessibility review,
SBOM/third-party notices, signed releases, Zenodo setup, examples, and implemented software.

## Core-principle impact report

No core principle was weakened. Specifically:

- provenance-backed rules require at least one evidence source and rule source references;
- deterministic verification is a core-only responsibility;
- unsupported manuscript content is explicitly blocking in the canonical schema;
- manifest verification requires `independent=true`;
- semantic actions cannot bypass approval, and forbidden automatic actions cannot be approved for
  automatic execution.

The main residual limitation is that schema conformance cannot prove evidence authenticity,
scientific equivalence, or actual independence. Those are explicit deterministic M1–M5 gates.

## Recommended M1 plan

1. Select typed-model and parser dependencies after license/fidelity spikes; record ADRs.
2. Implement stable ID generation, source locators, canonical serialization, and semantic
   integrity validators before format parsers.
3. Build minimal synthetic DOCX and LaTeX fixtures for every canonical object class, including
   equations, citations, tables, notes, tracked changes, and unsupported constructs.
4. Implement read-only DOCX and LaTeX parsers behind identical ports; preserve raw/source spans.
5. Add a deliberately simple diagnostic renderer only as needed for round-trip testing, not journal
   formatting.
6. Run independent reparse comparisons for text, numbers, equations, citations, references,
   captions, cross-references, and assets; fail on loss or uncertainty.
7. Do not begin M2 or claim journal support until M1 round-trip acceptance gates pass.

