# M12 Journal Format Transformation Engine Audit

## Scope and architecture

M12 adds an explicit, journal-agnostic format-transformation layer while preserving the M10/M11
`audit → plan → approve → apply → verify → package` contracts. The layer models verified target rules
as `FormatRuleTarget`, emits `TransferMatrixRow` and dependency-aware `FormatOperation` records, applies
surgical DOCX changes, and independently verifies expected versus observed deltas.

Source journal context is optional. `TARGET_ONLY` compares the current manuscript with the target;
`SOURCE_TO_TARGET` records source context but still lets target rules control execution. Central
`RULE_OPERATIONS` mapping prevents journal-specific executor conditionals.

## Supported operations

| Operation | Safety class | Effect | Verification |
|---|---|---|---|
| `REORDER_ADMIN_SECTIONS` | `CONTENT_PRESERVING_AUTOMATIC` | Moves existing known administrative section blocks before References in verified target order | Statement text identity and target order |
| `TITLE_PAGE_RESTRUCTURE` | `CONTENT_PRESERVING_AUTOMATIC` | Generates a separate title-page DOCX from existing canonical title, author and affiliation data | File existence and title identity |
| `FIGURE_CAPTION_NORMALIZATION` | `SAFE_FORMAT_AUTOMATIC` | Normalizes only figure prefix, number delimiter and punctuation | Caption target form and embedded figure identity |
| `EXTRACT_FIGURES_TO_SEPARATE_FILES` | `CONTENT_PRESERVING_AUTOMATIC` | Extracts embedded assets as deterministic `Figure_N.ext` files without recompression | Figure count and byte checksum |

All operations are idempotent. Re-running the same plan against the same source produces identical
candidate and artifact hashes. Administrative bodies, missing captions, scientific prose, pixels and
bibliographic facts are never generated or inferred.

## Transfer matrix and planner semantics

`transfer_matrix.json` records source, current and target states; KEEP/MODIFY/SPLIT/MANUAL/UNKNOWN;
executor support; safety class; approval; profile status; confidence; and provenance. The companion
`format_transformation_plan.json` records operation preconditions, expected deltas, `depends_on`,
`conflicts_with`, and a deterministic topological execution order.

Only `VERIFIED` target rules enter execution. `PARTIAL`, `UNKNOWN`, `STALE`, and `CONFLICTED` rows are
`PROFILE_UNCERTAIN`, `BLOCKED`, and absent from the executable graph. Unknown mappings remain explicit
manual/unsupported work. Dependency cycles fail closed.

## DOCX preservation strategy

The executor directly edits `word/document.xml` and copies every untouched ZIP member byte-for-byte.
It does not reconstruct the manuscript with `python-docx`. Figure extraction reads the original media
member and writes its original bytes. Separate title pages are package artifacts and do not remove or
rewrite the manuscript title page.

Execution fails closed for ambiguous References locations, duplicate administrative sections, duplicate
figure numbering/relationships, missing caption bodies, malformed relationships, missing media,
unsupported title-page modes, changed source hashes, uncertain rules, and mismatched execution graphs.

## Operation-aware verification

The verifier reparses source and candidate independently and checks:

- source byte identity;
- equations and scientific numbers outside authorized caption prefixes;
- table content;
- reference identity and citation mappings;
- untouched OpenXML-part hashes;
- administrative text identity and ordering;
- title identity;
- caption format and embedded figure identity;
- extracted figure count and byte hashes.

Only empty failure reasons and unexpected changes yield `VERIFIED_CANDIDATE`. Reports contain hashes,
operation status, artifact metadata, preservation checks and remaining requirements, but no manuscript
plaintext. Both JSON and HTML reports are generated.

## Synthetic source-to-target E2E

The regression fixture is generated in a temporary directory and contains a 280-word abstract,
scientific sections, equations, numerical results, three embedded figures with mixed caption styles, a
table, 25 references, numeric citations and existing administrative sections in a source-specific order.
The target requires reordered administrative sections, `Figure N |` captions, separate figures and a
separate title page.

The E2E covers planning, transfer-matrix generation, four transformations, repeat execution,
independent verification and report creation. It asserts source byte identity, deterministic candidate
and artifact hashes, exact extracted image bytes, empty unexpected changes and
`VERIFIED_CANDIDATE`. The verified candidate and artifacts then pass the M12 package adapter with
`package_integrity = PASS` and `package_status = PACKAGE_READY`.

One local synthetic run measured approximately 23.32 ms parse, 0.18 ms plan, 43.02 ms apply, 18.04 ms
verify and 14.32 ms package/verification. These are diagnostic values, not performance guarantees.

## Unsupported operations and limitations

M12 v1 does not claim support for arbitrary section renaming, scientific section merging/splitting,
missing-caption generation, reference deletion, author-year/numeric citation conversion, uncertain
reference reformatting, broad journal style beautification, supplement content rewriting, or LaTeX
execution. Reference and citation transformations remain manual until canonical identity and linkage can
be verified reliably. Profile files must supply explicit verified transformation targets before the four
operations can be enabled for a real journal.

## Privacy

All formatting work is deterministic and local. Tests use synthetic DOCX only. Real unpublished
manuscripts are excluded from tests, reports, Git, CI and public documentation. Format reports never
include manuscript plaintext.

## Quality gates

- `pytest`: 215 passed, 74 subtests passed.
- `ruff check .`: passed.
- `ruff format --check .`: passed.
- `mypy --no-incremental`: passed in strict mode.
- `python -m compileall -q src`: passed.
- `git diff --check`: passed (Windows line-ending notices only).
