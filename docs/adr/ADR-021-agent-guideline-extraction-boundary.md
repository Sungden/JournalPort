# ADR-021: Agent guideline extraction boundary

Status: Accepted for M7

The agent layer discovers, reads, segments, interprets, and proposes. Deterministic core code validates schemas, authority metadata, evidence attribution, conflicts, hashes, diffs, and advancement eligibility. Extractor or reviewer output can never directly mutate a production profile or assign `VERIFIED`.

The provider interface consumes only provider-neutral EvidenceUnits and returns CandidateRules. The initial implementation is a conservative deterministic fixture/replay extractor; no API key or proprietary SDK is required.
