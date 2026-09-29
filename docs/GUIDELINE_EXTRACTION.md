# Provenance-aware guideline extraction

M7 converts official journal guidance into reviewable draft profiles. It discovers official URLs, retrieves minimal versioned snapshots, segments EvidenceUnits, extracts structured CandidateRules, binds every proposal to evidence IDs, detects equal-authority conflicts, validates schemas, compares the blind draft to curated rules, and writes a human review queue.

It does not treat search snippets as evidence, trust third-party guidance, fill missing rules from model memory, silently resolve conflicts, mark profiles VERIFIED, overwrite production profiles, or alter the offline M0–M6 core. External page content is always untrusted and cannot redefine extraction policy.

Source priority is: official article-type page; journal author/submission instructions; publisher-wide instructions; official portal documentation; official templates/checklists. Secondary sources may aid navigation only. Retrieval records explicit `RETRIEVED`, `PARTIAL_RETRIEVAL`, `BLOCKED`, or `NOT_FOUND` status and uses content-addressed cache files.

Candidate profiles are always `DRAFT`. A deterministic reviewer checks cited evidence existence, authority, literal values, and conflicts. Supported candidates enter `profile_review_queue.json` for maintainer review. Even reviewer-supported rules remain drafts. Production status can change only through a separate approved evidence-review workflow.

The refresh workflow is `profile discover`, followed by `profile refresh-draft` for online retrieval or `profile extract-from-snapshot` for reproducible offline replay. Each immutable run records source hashes/timestamps, extractor/provider/model and prompt versions, settings, candidate hash, reviewer version, evidence, diff, and review queue. Outputs are placed under a draft root and never under production profiles unless a maintainer explicitly performs a later migration.

The benchmark prioritizes precision over recall. UNKNOWN or omission is preferred to a plausible unsupported requirement. Current deterministic extraction handles explicit numeric limits, cover-letter presence, optional supplementary information, conditional Extended Data limits, and selected explicit statement requirements. Ambiguous prose and complex structure rules are intentionally left for review rather than guessed.
