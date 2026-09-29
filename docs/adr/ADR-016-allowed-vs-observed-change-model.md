# ADR-016: Allowed versus observed changes

Status: Accepted for M5

The verifier derives an `AllowedChangeSet` from the candidate-container contract and explicit plan actions, independently computes an `ObservedChangeSet`, and rejects their difference. Candidate filename isolation is a nonsemantic container-level allowance; an explicit filename action additionally has an exact-name postcondition. Scientific categories are never implicitly allowed.

Comparisons use category and object-content fingerprints rather than a whole-document ordered-text hash. This permits future explicitly planned relocation while still distinguishing content changes. Current M4 has no relocation operation, so all scientific object categories must be identical.
