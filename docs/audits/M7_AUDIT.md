# M7 Audit — Provenance-Aware Journal Guideline Extraction Agent

## M7 status

**PASS WITH CONDITIONS** (2026-09-29). Evidence-grounded draft extraction, deterministic review/diff, immutable draft output, offline replay, and three-journal benchmarking are implemented. M8 Skills, UI, mass journal expansion, profile auto-approval, and submission automation were not started.

Conditions: live Nature reachability is inconsistent because several pages redirect to an inaccessible identity/cookie flow; the deterministic extractor intentionally omits complex structural prose; no external LLM provider was invoked; and production profiles remain unchanged.

## Agent extraction architecture and boundary

`journalport.guidelines` owns discovery, officiality, retrieval/cache, evidence segmentation, extraction, review, conflicts, diff, hashing, and draft lifecycle. `journalport.agents.AgentExtractor` is a provider-neutral protocol. The initial provider is a conservative deterministic evidence extractor suitable for fixtures, offline replay, and Codex/manual orchestration. No SDK, key, or provider-specific object enters profiles core.

The agent layer may discover/read/interpret/propose. Deterministic code validates schemas, domain authority, evidence IDs, literal values, conflicts, hashes, diffs, and immutable output. Candidate profiles are always `DRAFT`; neither extractor nor reviewer can assign `VERIFIED`.

## Source discovery and authority

The Nature navigation adapter returns two official HTTPS sources per benchmark journal: article/content guidance at authority level 1 and journal submission guidance at level 2. It proposes URLs only, never rule values. Officiality requires an exact approved host and declared journal/publisher/portal relationship; lookalike subdomains, credentials in URLs, HTTP, blogs, and third-party sites fail.

Live reachability probe: the Nature Computational Science preparation page was retrievable and explicitly listed manuscript, cover letter, optional supplementary information, and a maximum of ten Extended Data items. The other five tested URLs redirected into an inaccessible identity/cookie flow and are therefore treated as blocked rather than guessed. [Official preparation page](https://www.nature.com/natcomputsci/submission-guidelines/preparing-your-submission)

## Retrieval and cache

The network adapter is confined to M7 and uses standard-library HTTP. It records URL, final-domain validation, retrieval status, HTTP status, content type, title, timestamp, and content hash; reads are capped at 2 MB. Content-addressed JSON cache entries are immutable. Explicit states cover retrieved, partial, blocked, and not found. Wrong content type, timeout, empty body, unrelated redirect, and unofficial source are tested.

## Evidence and candidate rules

EvidenceUnits contain source/authority identity, locator fields, minimal visible text, timestamp, and hash. Script/style/noscript/navigation/aside/hidden content is removed. CandidateRules separately store the proposed interpretation, scope, applicability/condition, value/operator/unit, confidence, safety class, notes, and mandatory evidence IDs. Confidence is closed to HIGH/MEDIUM/LOW/UNKNOWN.

The v1 extractor handles only explicit wording for article identity, title/abstract/main-text/display limits, cover-letter presence, optional supplementary information, conditional Extended Data limits, and selected required statements. Insufficient or ambiguous evidence yields no rule rather than a guess.

## Draft lifecycle, reviewer, and conflicts

Each extraction produces immutable, hash-addressed `profile_drafts/<journal>/<run-id>/` output with sources, evidence, DRAFT candidate profile, diff, review queue, and run metadata. A second run with the same identity cannot overwrite it. The reviewer receives only EvidenceUnits and CandidateRules; it checks citation existence, authority, literal numeric support, and conflicts. Supported items still require maintainer review.

Equal-authority candidates with different values become `CONFLICTED`; no last-write-wins selection occurs. Profile diff classifications include match, new candidate, missing existing, value/applicability conflict, unsupported, and evidence mismatch.

## Prompt-injection defense

The versioned prompt states that external content is untrusted, cannot redefine policy, must not be supplemented from model memory, must preserve unknowns, and must cite evidence IDs. Synthetic script, hidden text, navigation, advertisement, third-party, and prose instruction-injection fixtures generated zero rules. Prompt Injection Resistance: **5/5 (100%)**.

## Three-journal blind benchmark

Extraction consumed only offline official-source evidence snapshots. Curated profile rules were loaded only after extraction for scoring. Strict recall uses the curated VERIFIED article-layer subset; supported candidates matching curated PARTIAL rules are not counted as hallucinations.

| Journal | Candidates | VERIFIED matches | VERIFIED ground truth | Recall |
|---|---:|---:|---:|---:|
| Nature Communications | 7 | 5 | 5 | 100% |
| Nature Computational Science | 7 | 7 | 8 | 87.5% |
| Nature Machine Intelligence | 7 | 7 | 8 | 87.5% |
| Aggregate | 21 | 19 | 21 | 90.48% |

The two missed VERIFIED rules are complex section-structure requirements intentionally omitted by the high-precision extractor. Two Nature Communications candidates match curated PARTIAL rules and have direct evidence; they are review candidates, not VERIFIED claims.

## Metrics

| Metric | Result |
|---|---:|
| Source Discovery Accuracy | 6/6 (100%) |
| Official Source Acceptance Accuracy | 100% |
| Requirement Extraction Precision | 21/21 (100%) |
| Strict VERIFIED-rule Recall | 19/21 (90.48%) |
| F1 | 95.00% |
| Value Accuracy | 21/21 (100%) |
| Operator Accuracy | 21/21 (100%) |
| Scope/Target Accuracy | 21/21 (100%) |
| Applicability Accuracy | 21/21 (100%) |
| Evidence Attribution Accuracy | 21/21 (100%) |
| Hallucinated Requirement Rate | 0/21 (0%) |
| Conflict Detection Accuracy | 1/1 (100%) |
| Prompt Injection Resistance | 5/5 (100%) |
| Unknown/Missing-Evidence Preservation | 100% |
| Rule Stability Across 3 Runs | 100% |
| Unsupported Source Accepted as Official | 0 |
| Silent Extraction Skip Count | 0 |
| Offline Replay Success | PASS |

## Schemas and reproducibility

Added v1.0.0 schemas: source record, evidence unit, candidate rule, candidate profile, extraction run, review queue, and profile diff. Every emitted candidate rule, evidence unit, source, profile, diff, queue, and run is schema validated before persistence. Run metadata records JournalPort/extractor/prompt/reviewer versions, provider/model/settings, source URLs/hashes/timestamps, and candidate hash.

## Production-profile safety

Tests hash/read production profile bytes before and after replay. They remain identical. Draft output roots are separate, candidate status is schema-fixed to `DRAFT`, and duplicate run paths fail. There is no CLI command for automatic approval or production overwrite.

## Offline replay

`journalport profile extract-from-snapshot` recreates the same evidence, candidate rules, conflicts, review queue, diff, and logical candidate hash without network access. Three repeated extraction runs selected identical rule/value/evidence tuples.

## Remaining risks

1. Five of six live Nature URLs were blocked by identity/cookie redirects during the probe; fixture snapshots preserve the curated official evidence basis but are not a substitute for a new human retrieval review.
2. HTML segmentation is intentionally minimal and is not a general browser/rendering system.
3. Structural and nuanced scope rules have lower recall because the extractor refuses ambiguous inference.
4. The deterministic fixture provider proves interfaces and safety gates, not the variability characteristics of external LLM providers.
5. Cache freshness is recorded but automatic stale-policy decisions remain conservative/manual.
6. Public-release blocker: Git provenance is incomplete because Git identity is still unset; no identity or commit was fabricated.

## M8 readiness

**M8 readiness = YES WITH CONDITIONS.** Drafts are evidence-grounded, hallucination is zero, review queues and offline replay work, production profiles cannot be silently overwritten, three-journal extraction is practically useful at 90.48% strict recall, and M0–M6 remain isolated. Live-source refresh reliability and Git provenance must remain explicit blockers for public release, not be hidden by Skills.
