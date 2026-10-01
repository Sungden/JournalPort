# Nature Communications DOCX full-format closure audit

Date: 2026-10-01. Scope: Nature Communications / Article / DOCX only.

## Readiness conclusion

**NC_DOCX_NOT_CLOSED**

The generic workflow now executes supported verified structure/layout rules and produces an
independently verified candidate, assets, coverage and a checksum-verified local package. Closure
criteria remain unmet: no supported rendering environment was available for a real render, complete
Nature bibliographic rendering is not executable, and several profile targets remain uncertain.
Neither a clean unit suite nor a content-preservation result establishes full-format closure.

## Official sources and profile completeness

- [Nature Communications submission instructions](https://www.nature.com/ncomms/submit/how-to-submit)
  were retrieved through the indexed official page on 2026-10-01. Direct fetching encountered Nature's
  identity redirect. The evidence snapshot explicitly retains its EVIDENCE_EXTRACT scope and hashes;
  it does not claim a full-page archived snapshot.
- [Nature formatting guide](https://www.nature.com/nature/for-authors/formatting-guide) was consulted
  for comparison, not used to substitute Nature's section order for NC's order.
- Existing publisher-level authorship, competing-interest and availability provenance remains pinned
  to its original official policy sources. Article-specific uncertain availability overrides remain
  uncertain. The dated NC guide has not been promoted into current VERIFIED evidence.

Article profile 1.3.0 is PARTIAL. Its resolved document target contains 24 applicable fields in
REVISION and FINAL_SUBMISSION. Unknown margin, page-size, font-family and font-size fields never
produce automatic settings. The known Nature reference family is VERIFIED_NONEXECUTABLE: knowing
the family does not prove a safe general rendering implementation.

## Inheritance and stage resolution

The existing pinned ProfileRegistry and ResolvedJournalProfile are reused:

publisher:nature-portfolio 1.2.0 → journal:nature-communications 1.3.0 →
article-type:nature-communications/article 1.3.0 → explicit stage selection → ResolvedDocumentFormat.

Publisher targets represent shared declarations. NC structure and Word format targets remain
article/journal-specific; typography is not assumed common to all Nature journals. Existing 1.0.0,
1.1.0 and 1.2.0 profiles are retained. Stage applicability is carried per target field and resolved
before execution. INITIAL_SUBMISSION produces no forced revision formatting. ACCEPTED remains
explicitly unresolved rather than silently reusing revision requirements. Explicit overrides,
conflicts, stale profiles, missing/non-official provenance and mismatched evidence hashes fail closed.

No NCS/NMI closure or additional publisher transformation was implemented.

## Supported transformations

The new generic operations route through M12 Core and its existing plan/result/verifier contracts:

- REBUILD_MANUSCRIPT_STRUCTURE preserves scientific-block order and reorders known tail blocks.
- TITLE_PAGE_RESTRUCTURE supports ordering explicitly identified inline title/author/affiliation/
  correspondence paragraphs; separate-page support remains in the existing engine.
- COLLECT_FIGURE_LEGENDS moves reliable existing captions without changing their bodies.
- RELOCATE_TABLES moves unambiguous title/table pairs, preserving cells and merged-cell XML.
- SET_COLUMNS, SET_LINE_SPACING, SET_ALIGNMENT and SET_PAGE_NUMBERING apply resolved verified values.
- EXTRACT_FIGURES_TO_SEPARATE_FILES copies embedded binaries without re-encoding.
- Explicit supplementary DOCX/PDF inventory is renamed/copied/packaged byte-identically.

The authoritative full_format_plan.json contains source/profile/target binding, target provenance,
stage, dependencies, expected deltas, semantic roles and unresolved requirements. Core regenerates
and compares a reviewed plan before execution. TransferSession is reused and persisted locally.
Automatic approval state is used only when every operation says NOT_REQUIRED; scientific edits
continue to require M10 approval-bound payloads.

## Structure, title page and styles

Blocks carry HIGH/MEDIUM/LOW confidence and explicit detection evidence. Style/outline or bold
formatting combined with known labels supports automatic block movement. Canonical-label-only
boundaries stay MEDIUM. Duplicate headings, unsupported wrappers and undefined target positions
block structural movement. Front matter requires explicit labels or semantic styles and factual
identity/contact fields. Author sequence alone never supplies identity or affiliation information.

Role detection is independent of arbitrary source style names. Direct paragraph/section properties
implement only verified targets. Existing styles are preserved; a generated administrative heading
style carries semantic outline information without invented typography. Word property ordering and
namespace prefixes are preserved. Existing footer composition is manual, as replacing it could
discard content. General arbitrary title-page reconstruction, missing author identity completion,
Methods reshuffling and uncertain availability placement remain unsupported.

## Figures, captions, tables and supplements

Caption mapping uses explicit numbered text plus adjacent embedded relationship evidence. Existing
dedicated legend blocks and uncertain caption relationships remain conservative. No captions are
written from scratch. Figure numbering and caption-body text remain unchanged. Caption-prefix syntax
is still PARTIAL, so wrapper normalization is not activated for NC.

Table titles must map unambiguously. All cell text, numeric values, formulas and merge structures
are compared independently of allowed paragraph layout properties. The stress corpus includes six
figures, two tables and merged cells. Extraction reports record embedded object, relationship,
filename, file type and checksum.

Read-only PNG/JPEG dimensions and available DPI/color metadata are reported. They are not a complete
TIFF/vector production validator. Figure type and applicable production requirements still need
manual judgment; no pixels are altered. Embedded OLE supplements and author-provided multi-file
combination remain manual. An explicit single supplement has a source hash, target name and role.

## Citation/reference coverage

Plain numeric citations and ranges are now represented in CanonicalManuscript and linked to numbered
reference identities, with uncertain/unresolved markers retaining PARTIAL locators. The citation-heavy
fixture has 30 references and reliably links [1, 3–5]. Live reference-manager fields remain intact and
are identified as requiring manual review.

CanonicalReference and CitationOccurrence records provide diagnostic identities. A deliberately
narrow lossless reference renderer can reparse and prove identity within its supported syntax.
General Nature author-list abbreviation, arbitrary title/journal parsing, superscript conversion and
live-field conversion are not automatic. No metadata is fetched to fill gaps, and no uncited
reference is deleted. Citation/reference preservation compares identities and raw markers rather
than paragraph-position IDs. Full reference-style closure is a remaining blocker.

## Scientific preservation and idempotence

Operation-aware verification checks source bytes, execution hashes, original runs, equations,
scientific numbers, table contents, references, citation mappings, figure binaries, namespaces,
administrative text, front-matter identities, untouched parts and original styles. Clean results
require VERIFIED_CANDIDATE and empty unexpected_changes/failure_reasons. Mutation/tamper tests
prove the verifier rejects a changed scientific number.

Repetition from the original is byte-idempotent; replanning an already transformed candidate is
also tested. Added ZIP parts have deterministic timestamps. Extraction-only candidates remain
byte-identical to source. Source always remains untouched.

## Rendering validation

RenderBackend and LibreOfficeRenderBackend are implemented. The backend uses an isolated profile and
fresh PDF conversion directory, preventing stale PDFs from satisfying a failed conversion. It
checks pages, headings, image occurrences, table-cell text and empty pages. Word repair dialogs and
table appearance cannot be proven by headless PDF text extraction alone and remain explicit warnings.

Local availability: **NOT_AVAILABLE**. No LibreOffice binary was found. No PDF or page visual pass is
claimed. The required real headless-render integration test in an environment with LibreOffice is
not yet passed. This prevents visual/full-format closure.

## Synthetic corpus and installed E2E

The public generator examples/public-synthetic/nc_docx_corpus.py contains only invented content.

| Case | Stress condition | Applied operations | Scientific preservation | Target format |
|---|---|---:|---|---|
| SYN-NC-001 | Simple manuscript | 8 | VERIFIED_CANDIDATE | PARTIAL |
| SYN-NC-002 | Messy styles and reordered front matter | 9 | VERIFIED_CANDIDATE | PARTIAL |
| SYN-NC-003 | 30 references and numeric ranges | 8 | VERIFIED_CANDIDATE | PARTIAL |
| SYN-NC-004 | Six figures, two tables, equation and merged cells | 8 | VERIFIED_CANDIDATE | PARTIAL |
| SYN-NC-005 | Live fields and tracked changes | 0 | Byte-identical candidate | BLOCKED |

All five installed workflows use an isolated venv, `python -I`, bundled installed profiles and a
working directory outside the source checkout. pip check passes. Dependencies were installed from
offline QA wheels exported from existing third-party distributions; the JournalPort wheel itself
was built from the current source. This is an isolated install test, not an independent package-index
dependency-download test. Every synthetic package has integrity PASS and remains
PACKAGE_REQUIRES_MANUAL_REVIEW.

Representative coverage: 24 applicable targets, 14 applied/already-satisfied rules (58.33%).
There are 16 VERIFIED fields, 10 executable fields, 8 uncertain fields and 2 known non-executable
requirements in the representative resolved target. Simple cases apply 8 rules and satisfy 6
without change; the messy-front-matter case applies 9 and satisfies 5 without change.
The profile upgrade recognizes the reference family as verified but non-executable; incomplete
fields and image production validation remain unresolved. Reports carry exact counts per run.
Coverage includes unknown/non-executable fields in its denominator and is not a publisher acceptance
score. Source hashes and differing candidate hashes are recorded locally.

## Real manuscript and privacy

No unpublished manuscript was opened or used in this phase. No real text appears in this audit,
fixtures, examples, tests or distributions. Real validation is deferred until synthetic closure
gates and explicit user approval, as requested. The disclosure ledger records no model-processed
manuscript objects and no full-text exposure for deterministic runs. Runtime output is ignored.

Wheel and sdist scans reject private directories and manuscript identifiers. The recorded archive
scan found zero violations. No commits, tags, releases, pushes, issues or public submissions were
created. The working tree includes pre-existing uncommitted work plus this implementation.

## Quality gates and remaining blockers

pytest, ruff check, ruff format --check, mypy --no-incremental, compileall and git diff --check are
required and are recorded with final execution results. Synthetic structural E2E, clean wheel
installation, installed E2E, package integrity and privacy scans pass within the described boundaries.
The full suite passes 234 tests and 80 subtests. Ruff checks/format checks, strict mypy across 85
source files, compileall and diff whitespace checks pass. The LibreOffice environment gate is
NOT_AVAILABLE, not PASS.

Required closure blockers remain:

1. Run the real rendering integration in a supported LibreOffice environment and inspect output.
2. Implement and prove the complete supported Nature reference/citation renderer before enabling it.
3. Resolve remaining applicability/placement/profile uncertainties from official provenance.
4. Extend image production validation and title/block recognition for additional reasonable DOCX
   layouts while preserving fail-closed behavior.
5. Obtain separate approval for private real-world full-format validation after synthetic gates.

Exact readiness: **NC_DOCX_NOT_CLOSED**. Do not start another journal or claim universal one-click
Nature Communications formatting from this result.
# A B C validation checkpoint — 2026-10-01

Conclusion: NC_DOCX_NOT_CLOSED.

Scope was restricted to independent closure-critical formatting coverage, HIGH-confidence
reference rendering/numeric citation identity, and real LibreOffice rendering/page visual QA.
No new journals, LaTeX, UI, cover-letter or agent features were added.

## Current closure measurements

For SYN-NC-004 after the hash-bound three-page visual receipt:

| Gate | Observed result |
|---|---|
| unresolved_closure_critical_blockers | 1 |
| formatting_target_coverage | 11/12 = 91.6667% |
| overall_profile_coverage | 15/24 = 62.5% |
| content preservation | VERIFIED_CANDIDATE; no unexpected changes/failure reasons |
| target format | FORMAT_TARGET_PARTIAL |
| references/citations | Supported HIGH subset identity roundtrip passes |
| render | RENDER_PASS |
| visual | VISUAL_PASS_WITH_NOTES, synthetic three-page rendered-image review only |
| package integrity | PASS; readiness remains PACKAGE_REQUIRES_MANUAL_REVIEW |

The remaining formatting-critical target is `availability.placement` (UNKNOWN). It was not
promoted, removed from the denominator, or satisfied by invented statements. Non-formatting
declaration/content policies and unspecified font/margin recommendations have separate categories.
An unknown newly introduced target defaults to critical, not excluded. Package-only figure and
supplement targets are tracked as separate critical blockers rather than mixed into formatting
coverage. `formatting_target_coverage` is a percentage; the legacy `supported_target_coverage`
fraction is retained only for compatibility and is not the closure criterion.

## Reference and citation implementation

Immutable NC Article profile 1.3.1 adds verified presentation attributes, leaving 1.3.0 intact.
Official evidence: https://www.nature.com/ncomms/submit/how-to-submit (References section,
checked 2026-10-01 via the official indexed page; direct fetch redirects through Nature IDP).
The generic ReferenceStyleTarget/ReferenceRenderer constructs canonical fields into typed
Roman/italic/bold runs; it does not perform arbitrary prose substitutions. Reference identities
and stable IDs are reparsed and compared; citation markers keep their existing numeric
representation and linked identities. The scientific-number/run verification permits only the
exact expected reference-run delta, preserving all other scientific runs. DOI tampering fails.

Supported subset: explicit surname/initial authors, unambiguous journal article title, source,
volume, page range/article number, year, optional DOI; up to five full authors. Issue metadata
is parsed/preserved canonically but automatic issue presentation is blocked because its exact
target styling is not verified. DOI URL/prefix and trailing punctuation are preserved exactly.
Journal abbreviation text is preserved, not enriched. The engine does not prove that an existing
abbreviation is bibliographically correct; this remains author/manual review. Six or more authors
are blocked because et-al elision would violate full-author identity roundtrip. Preprints,
books/chapters, malformed/ambiguous records, unavailable abbreviation mappings and live fields
remain manual; no metadata queries, deleted references, or flattened fields occur. Mixed/unsafe
linkage blocks the operation rather than partially rewriting an unreliable list.

## Actual rendering and visual QA

With explicit user permission, winget installed TheDocumentFoundation.LibreOffice 26.8.0.3
from download.documentfoundation.org after installer SHA-256 validation. Windows uses the
console sibling `soffice.com` for reliable version/exit output; GUI `.exe` can detach/hang.
All five synthetic runs actually converted to PDF. Checks cover title, headings, media
relationships, actual image drawing occurrences, table cell text and non-empty pages.
Input/PDF hashes, backend version and conversion exit code are recorded locally.

The packaged documents renderer produced all three SYN-NC-004 page PNGs. Every page was
visually inspected: six images, equation, five formatted references, legends and both tables
are visible and unclipped; no unexpected blank pages or overlap was observed. Notes: captions
are collected separately while original embedded images remain; original borderless tables
are preserved. This is rendered-page QA, NOT an observation of an interactive Word repair dialog.
PNG SHA-256 values match the final candidate's render byte-for-byte. The visual receipt is
bound to candidate/PDF/page hashes and validated through Core's finalization gate.

No real unpublished manuscript was processed. Its end-to-end visual validation is still deferred
because synthetic FORMAT_TARGET_VERIFIED / 100% coverage has not passed. Therefore this checkpoint
cannot satisfy the earlier overall release criterion requiring an authorized real visual pass.
Overall release unresolved critical blockers = 2: (1) UNKNOWN availability placement,
(2) authorized real-manuscript visual E2E not evaluated. The per-synthetic-candidate count of 1
must not be confused with this broader release count.
Only public synthetic page images were disclosed to the model for QA; no private full text was
exposed. Deterministic manuscript processing stayed local. The post-visual synthetic ledger
explicitly records all three model-viewed page objects and full synthetic-text exposure.

## Synthetic rerun

| Case | Operations | References rendered | Numeric citation occurrences | Render | Format coverage |
|---|---:|---:|---:|---|---:|
| SYN-NC-001 | 9 | 5 | 4 | RENDER_PASS | 91.6667% |
| SYN-NC-002 | 10 | 5 | 4 | RENDER_PASS | 91.6667% |
| SYN-NC-003 | 9 | 30 | 4 | RENDER_PASS | 91.6667% |
| SYN-NC-004 | 9 | 5 | 4 | RENDER_PASS | 91.6667% |
| SYN-NC-005 | 0 | 0 | 4, LOW/live-field linkage | RENDER_PASS | 8.3333% |

All five preserve source bytes and pass candidate preservation/package integrity. Case 5 stays
byte-identical and unsupported; PDF conversion success does not make its target format verified.
The 30-reference case preserves all canonical reference IDs through rendering and numeric ranges.

Current local evidence: `.test-tmp/nc-abc-final-*`, `.test-tmp/nc-abc-synthetic-summary.json`.
Runtime outputs are Git-ignored. The earlier flat 58.33% results below are historical.

Quality at this checkpoint: 253 tests and 80 subtests pass; ruff check/format, strict mypy
across 86 source files, compileall and diff checks pass. Isolated wheel/sdist builds use
fresh build environments with offline third-party hatchling wheels, not --no-isolation.
Both distributions install into clean venvs; wheel runs all five synthetic cases and sdist
runs the complex six-figure case with `python -I`, installed profiles and no checkout fallback.
pip check passes. Installed candidate hashes reproduce source-run candidate hashes. The wheel
visual receipt is validated against newly rendered PNGs whose hashes match the inspected pages.
Release scans cover 180 wheel members and 391 sdist members: zero private-path/private-identifier
or API-key-pattern violations. No public upload, commit, push, tag or release occurred.

# Prior final-blocker checkpoint — 2026-10-01

Conclusion: NC_DOCX_NOT_CLOSED.

This checkpoint adds Windows/common-path and `JOURNALPORT_LIBREOFFICE_PATH` discovery,
explicit-path fail-closed precedence, and backend version/input/PDF hash/conversion exit
code fields. PATH and both standard Program Files installation paths were checked locally;
no LibreOffice executable was available. No actual render or visual PASS is claimed.
Install prerequisite is documented in `docs/NC_DOCX_FORMAT.md`.

The complete Nature ReferenceRenderer/CitationRenderer, separated formatting coverage,
closure-critical blocker inventory, new isolated distribution validation, and real visual
E2E remain unfinished. The prior 58.33% metric is a mixed overall target metric, NOT a
closure-critical formatting coverage claim. Previous installed synthetic results below
are historical and must not be presented as a rerun of this checkpoint.

No private manuscript was opened or transformed in this checkpoint. No package, commit,
tag, release or upload was performed. Missing actual rendering is an external blocker;
the other listed blockers are implementation work, not irreducible external conditions.
