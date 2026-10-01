# Nature Communications Production Profile Hardening Audit

Date: 2026-09-30
Scope: Nature Communications / Article profile rules only. No manuscript was opened, parsed,
transformed, or packaged.

## Outcome

Profile `article-type:nature-communications/article@1.2.0` is stage-aware and remains `PARTIAL`.
It is not a claim of full journal compliance. Historical profile `1.1.0` remains immutable.

The previous universal, VERIFIED 200-word abstract rule was removed from the current profile. The
official formatting PDF says 150 words, but current submission guidance allows flexibility at
initial submission and directs detailed formatting to revisions. Because the numeric source is a
dated 2021 PDF, 150 words is `PARTIAL`, applies only to `REVISION` and `FINAL_SUBMISSION`, and cannot
authorize automatic rewriting.

## Official source inventory

- <https://www.nature.com/ncomms/submit/how-to-submit>
- <https://www.nature.com/documents/ncomms-formatting-instructions.pdf>
- <https://www.nature.com/ncomms/submit/editorial-process>
- <https://www.nature.com/nature-portfolio/policies/editorial-policies>

No published article, third-party checklist, search snippet, or inferred house style was used as
normative evidence.

## Rule and operation disposition

| Area | Initial submission | Revision / final submission | Classification |
|---|---|---|---|
| General format | Flexible within reason | Detailed format applies | VERIFIED / STAGE_CONDITIONAL |
| Administrative-section order | No automatic target | Explicit order exceeds executor semantics | VERIFIED_NONEXECUTABLE |
| Title page | No automatic target | Inline title page | VERIFIED_NONEXECUTABLE |
| Figure files | Embedded/grouped allowed | Individual files required | VERIFIED_EXECUTABLE |
| Figure legends | No automatic target | Placement/order/title/350-word evidence | PARTIAL |
| Title length | Not a blocking initial rule | 15 words in dated guide | PARTIAL |
| Abstract length | Not a blocking initial rule | 150 words in dated guide | PARTIAL |
| References | Not hardened | Manual review | UNKNOWN |
| Supplements | Incomplete evidence | Manual review | UNKNOWN |
| Data/code statements | Not auto-authored | Author-controlled applicability/content | PARTIAL |

No M12 operation is authorized at `INITIAL_SUBMISSION`. At `REVISION` or `FINAL_SUBMISSION`, only
Only `EXTRACT_FIGURES_TO_SEPARATE_FILES` has both a VERIFIED stage-scoped target and executor support.
`REORDER_ADMIN_SECTIONS` is blocked because the official order includes anchors/sections outside the
executor's supported administrative subset. `TITLE_PAGE_RESTRUCTURE` is blocked because the official
target is inline while the executor implements separation. `FIGURE_CAPTION_NORMALIZATION` is blocked
because its target remains PARTIAL.

## Completeness and residual unknowns

Coverage is sufficient to fail closed for the four M12 operations, but insufficient to mark the
profile VERIFIED. Gaps include current HTML confirmation of numeric title/abstract limits, exact
table-caption formatting, complete citation/reference-style semantics, supplement naming and
organization, figure technical specifications, subject-specific reporting, and authoritative
applicability semantics for ethics/consent and code statements. Fresh official provenance is
required before automation.

Machine-readable diff: `profile_reports/nature-communications/nc_profile_hardening_diff.json`.
