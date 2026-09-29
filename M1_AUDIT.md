# M1 Audit — Manuscript Parsing

Date: 2026-09-29  
Milestone: M1 only  
Status: **PASS WITH CONDITIONS**

M1 establishes a deterministic, traceable, fail-closed DOCX/LaTeX-to-canonical parsing layer. It
does not claim general format coverage. No Journal Profile, guideline retrieval, compliance engine,
transformation feature, Agent Skill, MCP server, or UI was created.

## Stable ID design

**PASS.** IDs combine object type, stable format-specific source anchor, normalized content digest,
and deterministic collision ordinal. They cover documents, sections/subsections, paragraphs,
figures/legends, tables/legends, equations, citations, references, notes, supplements, authors, and
unsupported records. Random UUIDs are not used. Moving source content can change its ID; content
fingerprints provide the separate comparison axis. See ADR-001.

## Canonical serialization design

**PASS.** UTF-8 compact JSON uses sorted keys, NFC Unicode, LF newlines, preserved list order,
explicit nulls, and rejects NaN/Infinity. Logical SHA-256 is computed over canonical bytes.
Scientific numbers remain source text. Text, numeric, citation, reference, equation, asset, and
figure/table-reference fingerprints are independent. See ADR-002.

## DOCX parser strategy

**PASS WITH CONDITIONS.** The read-only parser uses standard-library ZIP and direct Open XML rather
than relying on python-docx's lossy high-level view. It preserves document/body order, styles used
for title/headings, paragraphs, tables and cell text, images and relationship hashes, captions,
field instructions, OMML, references, footnotes/endnotes, and raw unsupported evidence. Tracked
changes never select final/original view and are blocking. Complex style semantics and many OOXML
extensions remain unsupported. See ADR-003.

## LaTeX parser strategy

**PASS WITH CONDITIONS.** The parser is a deliberately narrow, non-executing source scanner. It
supports common metadata, sectioning, abstract, paragraphs, citations, `bibitem`, figure/table and
equation environments, inline/display math, and root-confined multi-file discovery. It never
compiles, expands arbitrary macros, or executes shell commands. Unknown content-affecting macros
and environments, traversal, missing includes, cycles, and unsafe I/O are explicit. See ADR-004.

## Supported features

Stable locators, title, styled/command headings, paragraphs in the supported subset, DOCX tables,
image relationships, captions, field citations, raw OMML, LaTeX common citations, `bibitem`,
figure/table/equation environments, inline/display math, basic DOCX notes, and bounded nested
`input`/`include`. Exact status per feature is in `docs/PARSER_SUPPORT_MATRIX.md`.

## Partially supported features

Authors/affiliations, abstract detection in nonstandard DOCX, lists, table semantics, figure
placement, DOCX citation varieties, external bibliography databases, equation numbering,
cross-reference resolution, hyperlinks, complex notes, and supplementary semantics. Raw source,
locator, content text, or hashes are retained where applicable.

## Unsupported blocking features

Ambiguous DOCX tracked changes; comments; embedded objects; floating shapes; text boxes; missing
image relationships; unresolved scientific fields; unknown content-affecting LaTeX macros/custom
environments; unsafe TeX read/write/execute commands; missing/cyclic/traversing includes. Unsupported
records contain reason, severity, locator, preservation flags, raw evidence where available, and
fragment hash.

## Test fixture coverage

- DOCX synthetic generator: basic article, tables, image relationship, caption, citation field,
  footnote, endnote, OMML, tracked insertion/deletion/replacement/multiple changes including number
  and citation, unknown field, and embedded object.
- LaTeX source trees: basic article, citations, figures, tables, inline/display equations, custom
  macros, nested multi-file input, missing input, include cycle, traversal, and custom environment.
- Golden checks cover counts, stable IDs/determinism, section tree, text/numbers, citations,
  references, equations, assets, unsupported detection, schema validity, and serialize/reload
  equality.

## Preservation metrics

Metrics apply only to labeled synthetic ground truth; they are not population-level format claims.

| Metric | Result | Denominator / evidence |
|---|---:|---|
| Text Preservation Rate | 100% | 18/18 labeled core text units across supported bundles |
| Numeric Preservation Rate | 100% | 10/10 declared scientific numeric tokens, including percentages and p-values |
| Citation Preservation Rate | 100% | 5/5 citation commands/fields; 6/6 declared keys across basic and citation fixtures |
| Reference Preservation Rate | 100% | 5/5 inline bibliography/reference entries |
| Equation Detection/Preservation Rate | 100% | 5/5 raw OMML/LaTeX inline/display equations across tested fixtures |
| Figure/Table Preservation Rate | 100% | 6/6 expected figure/table objects across combined and specialized fixtures |
| Unsupported-Content Detection Rate | 100% | 9/9 labeled hazard categories exercised by tests |
| Silent-Loss Count | **0** | No labeled content was absent without an unsupported record |

Hash equality also passes across repeated parses and serialize/reload cycles. Asset byte hashes and
extractable table source text are retained separately.

## Known parser risks

- DOCX stable anchors can shift when earlier body nodes are inserted.
- ElementTree preserves scientific XML content but not byte-identical namespace prefixes.
- DOCX numbering/list semantics, alternate content, SmartArt, charts, custom XML, complex notes,
  comments, and external links need broader inventory tests.
- Caption/reference association is heuristic and never treated as authoritative.
- The LaTeX scanner does not implement TeX tokenization, brace-balanced macro arguments, macro
  expansion, conditional evaluation, catcodes, package semantics, or `.bib` parsing.
- Absolute LaTeX paths in locators intentionally maximize local traceability but require later
  package-relative redaction for shareable artifacts.
- Fingerprints are deterministic lexical preservation tools, not semantic-equivalence proofs.

## Dependency and license summary

The M1 runtime adds **no third-party dependency**. DOCX uses Python `zipfile` and
`xml.etree.ElementTree`; LaTeX uses a standard-library scanner. Development validation retains
pytest, jsonschema, and Ruff. ADRs evaluate python-docx (MIT), lxml (BSD-3-Clause), pylatexenc
(MIT), plasTeX (MIT), and Pandoc's GPL/executable boundary. No external code or publisher fixture
was copied; all fixtures are synthetic Apache-2.0 material.

## Security findings

**PASS WITH CONDITIONS.** LaTeX is never compiled or executed. Includes are root-confined,
cycle-detected, and missing files block. `write18`, file I/O primitives, and pipe-input patterns are
blocking. DOCX is treated as an untrusted ZIP/XML container and never executes embedded content.
Future work must add ZIP expansion/size/count limits and hardened XML resource limits before
processing hostile large files at scale.

## Schema changes from M0

**Issue:** M0 `unsupported_content.blocking` was fixed to `true`, so it could not express the
required `WARNING`; `source_locator` was an unstructured string; object locators were incomplete;
tables lacked extractable content; citation keys could not be represented without inventing a
reference ID.

**Why insufficient:** These constraints prevented honest partial/unknown provenance, structured
fail-closed reporting, and parser output validation.

**Exact change:** Canonical schema version moved from `1.0.0` to `1.1.0`; added structured
`SourceLocator`; locator requirements on traceable records; structured unsupported records with
`WARNING|BLOCKING`, preservation flags, raw evidence and hash; `citation_keys`; equation labels;
and `Asset.content_text`.

**Compatibility impact:** A 1.0.0 canonical instance does not validate as 1.1.0 without migration.
No released or registry instances exist, so no user data was broken.

**Migration impact:** A future migrator must convert locator strings to structured locators, map
`blocking=true` to `severity=BLOCKING`, preserve old kind/description fields, add explicit nulls,
and use `UNKNOWN` locator status where precision cannot be reconstructed. No guessing is allowed.

## Validation evidence

- `pytest`: **16 passed, 12 schema subtests passed**.
- Ruff check: **PASS**.
- All six schemas pass Draft 2020-12 meta-schema validation.
- Canonical DOCX and LaTeX outputs validate against schema 1.1.0.
- Deterministic parse/reparse and serialize/reload comparisons pass.
- Type checking was not run because no type-checker is configured; type annotations are present.

## Recommended M2 plan

1. Freeze a versioned profile-resolution trace and semantic validation API before adding data.
2. Implement loader, cycle detection, parent-version pinning, override collision checks, freshness,
   source completeness, and conflict reports.
3. Define official-evidence snapshot/hash policy and license-safe excerpt limits.
4. Add exactly three manually reviewed journal/article-type profiles only after validators exist.
5. Keep profiles `PARTIAL` until every critical rule has current official provenance and review.
6. Do not begin compliance-engine or transformation work during M2.

