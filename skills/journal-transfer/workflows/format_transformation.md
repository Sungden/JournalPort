# Format transformation

1. Select `TARGET_ONLY` or `SOURCE_TO_TARGET`; target rules always control transformation.
2. Generate `transfer_matrix.json` with KEEP, MODIFY, ADD, REMOVE, SPLIT, MANUAL, and UNKNOWN rows.
3. Ask first whether each gap is deterministically solvable without scientific meaning changes.
4. Execute only `VERIFIED` rules mapped to supported operations. Keep `PARTIAL`, `UNKNOWN`, `STALE`,
   and `CONFLICTED` rules as `PROFILE_UNCERTAIN` manual work.
5. M12 v1 supports `REORDER_ADMIN_SECTIONS`, `TITLE_PAGE_RESTRUCTURE`,
   `FIGURE_CAPTION_NORMALIZATION`, and `EXTRACT_FIGURES_TO_SEPARATE_FILES` for DOCX. Missing captions,
   arbitrary scientific heading changes, prose restructuring, reference deletion, and uncertain
   reference/citation conversion remain unsupported.
6. Preserve administrative section bodies, figure pixels/binaries, tables, equations, numbers,
   reference identities, citation mappings, metadata identities, and all untouched OpenXML parts.
7. Apply operations in dependency order and require idempotence. Fail closed for ambiguity, malformed
   relationships, duplicate identities, uncertain rules, dependency cycles, or unsupported objects.
8. Independently compare each operation's expected delta with its observed delta. Continue only for
   `VERIFIED_CANDIDATE` with empty unexpected changes and failure reasons.
9. Keep format reports free of manuscript plaintext. Package artifacts remain local and are never
   submitted automatically.

## Full DOCX format workflow

For the Nature Communications Article DOCX reference implementation, use the pinned 1.3.2 profile
and an explicit stage. First run `journalport full-format SOURCE --journal nature-communications
--stage REVISION --profile-version 1.3.2 --plan-only --output PRIVATE_PLAN`. Review the resulting
`metadata/full_format_plan.json` and report executable operations, author inputs, unsupported
targets and profile uncertainties. When execution is authorized, run the same command without
`--plan-only`, using `--reviewed-plan PRIVATE_PLAN/metadata/full_format_plan.json` and a fresh private
output directory. Core re-resolves the target and rejects a changed source/profile/plan binding.

For author-confirmed conditional availability ordering, pass `--confirm-condition availability.placement`
on both plan and execution. This author fact is hash-bound to the plan; it never creates statements.
Missing statements require author input. Do not execute a partial plan to claim complete readiness.

Generic structure/layout operations include REBUILD_MANUSCRIPT_STRUCTURE, COLLECT_FIGURE_LEGENDS,
RELOCATE_TABLES, SET_COLUMNS, SET_LINE_SPACING, SET_ALIGNMENT and SET_PAGE_NUMBERING. Explicit inline
front matter can be reordered with identity preservation; missing identities remain author inputs. The source is
never changed. Scientific edits still go through M10 proposal, scientific diff and explicit approval.

Numeric citation linkage is diagnostic. General Nature reference rendering, live citation-field
conversion, inferred author identities, automatic caption generation and uncertain targets remain
manual. Explicit single-file supplements can be supplied using `--supplement FILE`; bytes are
preserved and hashes recorded. An absent render backend yields NOT_AVAILABLE and requires manual
visual validation. VERIFIED_CANDIDATE is content preservation, not full target-format closure.
Report target-format, rendering, coverage and package readiness separately. A package with unresolved
format/visual requirements is PACKAGE_REQUIRES_MANUAL_REVIEW. Never claim NC_DOCX_CLOSED from unit
tests or extraction alone.
