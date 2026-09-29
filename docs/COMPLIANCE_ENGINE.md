# Deterministic Compliance Engine

M3 consumes a `CanonicalManuscript` and an already resolved, pinned `ResolvedJournalProfile`. It is
offline, LLM-free, and read-only. It emits one explicit finding for every effective profile rule;
unknown, partial, unsupported, ambiguous, and failed evaluations are never silently skipped.

The pipeline is: policy/applicability gate -> deterministic selector -> versioned operator registry
-> template finding -> readiness derivation -> canonical report hash. Controlled section aliases are
versioned in code. Reference/citation, duplicate DOI/reference, missing figure asset, and missing
figure/table caption checks operate on canonical object identities without network metadata calls.

Supported operators are `EQ`, `NE`, `LT`, `LTE`, `GT`, `GTE`, `EXISTS`, `NOT_EXISTS`, `IN`,
`NOT_IN`, `COUNT_EQ`, `COUNT_LTE`, `COUNT_GTE`, `MATCH_REGEX`, `NOT_MATCH_REGEX`, `CONTAINS`, and
`NOT_CONTAINS`. Unsupported operators produce `EVALUATION_ERROR`. Selectors cover document metadata,
title, article type, abstract, main text, section order, references, figures/tables, supplements,
statements, and explicitly supplied submission metadata. A missing or ambiguous canonical field is
an error, not an inferred value.

The JSON report is authoritative; HTML is a static escaped presentation. Report hashes exclude only
the evaluation timestamp and hash field. The CLI exposes only `journalport audit`; no fix, rewrite,
transfer, rendering, or package command exists in M3.
