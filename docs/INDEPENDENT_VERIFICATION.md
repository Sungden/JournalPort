# Independent post-transformation verification

M4 self-checks cannot establish that the bytes written to disk still parse into the intended scientific manuscript. M5 is a separate, offline verification boundary. It reloads the source, candidate, pinned profile, pre-transform report, plan, log, and manifest; reparses the candidate with M1; reconstructs a fresh canonical manuscript; recalculates hashes and fingerprints; reruns M3; and produces a verification report, post-transform compliance report, compliance delta, and static HTML report.

The deterministic preservation layer checks normalized text and numeric/statistical tokens, equations, citation identities and mappings, reference identity, figures, tables, captions, figure/table references, assets, sections, notes, represented author metadata, and the unsupported-content registry. It ignores source-locator and container metadata when those do not carry scientific meaning. Numeric detection is lexical/object-level; it recognizes numbers, percentages, and p-value-like tokens, but does not claim full statistical semantics.

Allowed changes are explicit and closed. Candidate filename isolation is nonsemantic. A planned filename normalization must meet its exact postcondition. Non-applied/manual actions may not alter scientific categories. Any observed scientific change, new blocking finding, missing/ghost/duplicate action, profile mismatch, source mutation, or manifest mismatch fails closed.

`VERIFIED_CANDIDATE` means deterministic transformation and preservation checks passed. It is not proof of general scientific semantic equivalence, editorial acceptance, or submission readiness. `compliance_readiness_status` remains a separate M3 result, and `SUBMISSION_READY` is reserved for M6.

Known limits: the logical package hash remains byte-based while M4 only copies bytes; stable parser object IDs may incorporate source locators, so M5 compares content identities independently; approved semantic execution is not available in M4 and therefore cannot be positively verified yet; parser-unrepresented content cannot receive a stronger guarantee than the unsupported-content registry affords.
