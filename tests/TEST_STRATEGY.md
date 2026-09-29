# Test Strategy

## Safety case

Testing is organized around five claims: rules are provenance-backed; executable checks are
deterministic; scientific content survives round trips; semantic changes require approval; and
verification does not trust transformation state.

## Test layers

- **Schema:** every schema validates against Draft 2020-12; positive and negative instances cover
  required fields, enums, closed objects, references, hashes, and conditional approval rules.
- **Unit:** IDs, counts, profile resolution, operators, hashes, citations, filenames, and each
  validator are isolated and deterministic.
- **Parser/renderer:** DOCX and LaTeX fixtures exercise paragraphs, headings, numbers, symbols,
  equations, citations, references, captions, tables, cross-references, and notes.
- **Round trip:** source -> parse -> canonical -> render -> independent reparse -> semantic diff.
  Expected formatting drift is allow-listed; missing or altered science fails.
- **Integration:** profile resolution -> audit -> plan -> execute -> verify -> package.
- **Regression:** every corruption defect gains the smallest synthetic fixture.
- **Adversarial:** conflicting/stale/fake rules, ambiguous types, hallucinated requirements,
  unsupported Open XML, tracked changes, malformed BibTeX, duplicate references, and broken refs.
- **Acceptance:** one synthetic source across exactly three verified journal/article profiles; at
  least 20 labeled fixtures before MVP claims.

## Oracles and independence

Expected results are hand-authored and reviewable. Round-trip comparison uses structured tokens and
numeric/citation invariants, not the renderer's internal objects. The verifier receives files and a
manifest in a fresh workflow instance. Golden files include tool/version metadata and are changed
only with reviewed explanations.

## Current M0 checks

`test_schema_contracts.py` performs dependency-free JSON parsing, identity/reference integrity,
required vocabulary, and example-instance checks. When `jsonschema` is installed, the same suite
also validates all schemas against the official Draft 2020-12 meta-schema and validates examples.
CI in M1 must install the `dev` extra, making the optional check mandatory.

## M2 profile checks

Profile tests treat JSON as untrusted input and cover closed-schema loading, official provenance,
evidence hashes, pinned ancestry, valid and invalid overrides, equal-precedence collisions, cycles,
freshness, deterministic resolution hashes, and exact three-journal inventory. Synthetic adversarial
cases supply known ground truth; golden tests independently reload all seven immutable profile
layers and compare committed trace hashes with freshly resolved values. No test invokes an M3
manuscript-compliance decision.

## Exit criteria by risk

No release with a known silent-loss path, unapproved semantic mutation, unverifiable readiness
decision, non-provenanced effective rule, or a verifier that relies only on transformer state.
Coverage percentage is secondary to branch tests for every safety decision.

## M5 independent verification

M5 reparses persisted candidates, independently compares scientific categories, verifies allowed
and observed changes and action postconditions, reconciles plan/log/manifest evidence, reruns
compliance, and classifies deltas. Adversarial tests mutate scientific objects and integrity
evidence. A subprocess workflow runs plan, apply, and verify in distinct offline processes; three
pinned Nature profiles exercise the complete audit-to-verification chain. Timestamp variation
confirms deterministic logical report hashes.

## M6 submission package tests

M6 tests deterministic plan/build/verify boundaries, required/unknown/conditional requirement
handling, explicit bounded discovery, relative-path safety, duplicate identities, missing/modified and
undeclared files, profile/report/candidate tampering, logical-hash and ZIP reproducibility, portable
manifests, three real-profile workflows, and a fully fresh-process offline CLI pipeline. No fixture
authorizes generation of authorial or scientific content.

## M7 guideline extraction tests

M7 tests exact official-domain binding, discovery priority, explicit retrieval failures, immutable
content-addressed caching, visible-text evidence segmentation, structured evidence-only extraction,
equal-authority conflicts, reviewer independence, prompt-injection/hidden/navigation/advertising
content, UNKNOWN preservation, immutable DRAFT output, production-profile byte preservation,
offline replay, CLI operation, three-run stability, and blind comparison with the curated VERIFIED
subset for exactly three journals. High-confidence precision and zero hallucination take precedence
over recall.

