# NC availability placement audit — 2026-10-01

Result: NC_DOCX_NOT_CLOSED. A does not pass; B is not authorized to proceed under its conditional gate.

## Current official evidence

Source: https://www.nature.com/ncomms/editorial-policies/reporting-standards

The Data availability policy requires a statement for original research manuscripts. This is a conditional content/policy requirement, not an exact formatting location. The data-policy section alone does not prescribe an exact standalone statement location. This scoped absence does not establish that every availability placement requirement is absent.

The computer-code policy explicitly prescribes a separate Code availability section after Data availability and before References for studies using custom code or mathematical algorithms central to their conclusions. This is a conditional, closure-critical ordering requirement. Its wording is not restricted to REVISION alone; the current formatting target conservatively remains scoped to REVISION and FINAL_SUBMISSION. Applicability to a conceptual manuscript must not be inferred from article-type selection or the absence of a code statement.

Immutable article profile 1.3.2 retains parent journal 1.3.0 and all previous files. Current official evidence upgrades statement required rules to VERIFIED while preserving conditional applicability. The availability target records standalone data placement NOT_SPECIFIED / NOT_APPLICABLE_TO_FORMAT separately from the verified conditional Data availability → Code availability → References order.

The existing executor does not support this conditional target: VERIFIED_NONEXECUTABLE, manual review required. No executor or other feature was added. No UNKNOWN target was silently excluded from the denominator.

## Recalculation and limits

The new profile was loaded and planned against public synthetic SYN-NC-004 only. The planner reports availability.placement as executor_not_supported. Re-evaluating the latest matrix against the previously verified synthetic applied-rule set gives 11/12 formatting targets, 91.66666666666667%, one unresolved format-critical target, FORMAT_TARGET_PARTIAL. This is an audit reconciliation of existing public synthetic evidence, not a new candidate verification or a real-manuscript E2E result. Independent real render/visual/package gates remain unperformed in this turn.

The remaining target blocker is availability.placement. To safely resolve it without extending the executor, an author must establish that the custom-code/algorithm policy is inapplicable, or manual placement must be validated if applicable. No not-applicable result has been asserted for the private source.

## Disclosure and stop

No private manuscript object, full text, page image, source bytes or candidate was accessed in this turn. Only project code, public profiles, public synthetic metadata and official policies were processed. The private source was not modified; no real candidate, real render, real package, commit, push, tag or release was generated. B stopped before parse because A did not pass.
