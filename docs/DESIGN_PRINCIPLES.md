# Design Principles

1. **Preserve science first.** Unknown or unsupported content blocks the workflow; it is never
   silently discarded or approximated.
2. **Evidence travels with rules.** Every executable rule cites immutable source evidence,
   retrieval time, hash, and confidence. Memory is not provenance.
3. **Determinism produces verdicts.** Agents can interpret and propose; versioned code measures and
   verifies all mechanically decidable properties.
4. **Plans precede mutations.** Every change has stable source IDs, classification, rationale,
   evidence, and approval state before execution.
5. **Semantic edits are visible.** Before/after content and authorization are durable audit data.
6. **Verification is independent.** Rendered output is reparsed and checked without trusting the
   transformer.
7. **Fail closed.** `UNKNOWN`, `CONFLICTED`, preservation uncertainty, or blocking findings cannot
   become submission-ready through fallback logic.
8. **Journal policy is data.** Registry additions require profiles, evidence, fixtures, and tests,
   not journal-name conditionals.
9. **Local first and minimal disclosure.** Do not log or upload confidential manuscript text by
   default; store only needed excerpts and hashes.
10. **Standards before invention.** Reuse JATS semantics, CSL, DOI, ORCID, ROR, Open XML, BibTeX,
    and RIS where fit is demonstrated.
11. **Reproducibility is declared.** Versions, hashes, timestamps, validators, renderers, styles,
    transformations, and approvals are recorded.
12. **Claims match evidence.** JournalPort reports represented machine checks, not acceptance or
    scientific-quality guarantees.

