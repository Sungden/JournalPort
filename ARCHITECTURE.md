# JournalPort Architecture

## Scope and invariants

M0 freezes contracts, not implementations. JournalPort's deterministic core must operate without
an LLM. The precedence order is scientific content preservation, rule provenance, deterministic
verification, reproducibility, automation convenience, then UI polish.

The non-negotiable invariants are:

1. A mechanically checkable requirement is checked by code.
2. Unverified values remain `UNKNOWN`; conflicting official evidence remains `CONFLICTED`.
3. No content-sensitive edit is applied without an explicit, recorded approval.
4. Transformation and final verification are separate stages and implementations.
5. A blocking or unverifiable preservation result prevents `SUBMISSION_READY`.

## Layered architecture

```text
Agent/CLI/MCP adapters (later; orchestration only)
                    |
Application workflows and typed ports
                    |
  +-----------------+-------------------+
  |                 |                   |
Canonical model  Profile resolver   Compliance engine
  |                 |                   |
Parser ports     Provenance store    Validator registry
  +-----------------+-------------------+
                    |
Transformation plan -> executor -> renderer
                    |
Independent reparse + semantic/compliance/package verification
                    |
Auditable submission package + manifest
```

Dependencies point inward. Formats, network retrieval, agent hosts, CLI, and MCP are adapters.
Journal-specific policy is data, not branching core code.

## Core contracts

- `CanonicalManuscript` is the versioned, format-neutral source of truth. Stable object IDs are
  unique within a document and support audit and semantic comparison.
- `JournalProfile` is a versioned composition descriptor. It contains ordered, immutable parent
  references and local rules. Resolution emits a trace; it never silently overwrites conflicting
  values.
- `ComplianceRule` is an executable assertion with provenance references, severity,
  machine-checkability, and autofix classification.
- `ComplianceReport` contains deterministic findings tied to rule, evidence, and affected IDs.
- `TransformationPlan` is approval-gated. Executors may apply only approved actions allowed by
  classification.
- `Manifest` binds inputs, outputs, software/profile/validator versions, approvals, and hashes.

Schemas use JSON Schema Draft 2020-12, closed objects by default, semantic version strings, UTC
timestamps, SHA-256 digests, URI references, and explicit enums. JSON is canonical interchange;
YAML may be accepted later only after parsing into the same model. Schema validity does not imply
scientific validity: cross-document references, inheritance conflicts, stable-ID uniqueness, and
approval policies require deterministic semantic validators in later milestones.

## Journal profile inheritance

Composition is explicit: publisher base, journal override, then article-type override. A child
lists parent profile IDs and pinned versions in precedence order. Resolution is deterministic and
produces each effective rule's origin chain. Duplicate `rule_id` entries are legal only when an
override explicitly declares the superseded rule and provides provenance. Competing authoritative
values without an explicit precedence statement yield `CONFLICTED`.

## Agent/core boundary

Agents may find sources, extract candidate values, identify ambiguity, and propose edits. Candidate
rules remain non-verified until evidence and deterministic validation pass. Agents do not count,
match citations, decide preservation, execute unapproved semantic edits, or issue readiness status.

## Independent verification boundary

The verifier consumes rendered artifacts, reparses them through the public parser interface, and
does not trust executor state. It reruns compliance and preservation checks and validates hashes
and package contents. Separate modules and test fixtures are mandatory; process/service isolation
is a later deployment choice.

## Planned package boundaries

`manuscript`, `profiles`, `compliance`, `transform`, `renderers`, `bibliography`, `figures`,
`verify`, and `package` will be small typed modules under `src/journalport/`. Empty placeholder
modules are intentionally not implemented in M0.

## Architecture decisions

- **ADR-0001:** Practical JATS-inspired canonical model, not full JATS. Preserve source fragments
  for unsupported constructs and fail closed on loss; evaluate a lossless JATS mapping later.
- **ADR-0002:** CSL is the rendering standard. Formatting correctness is separate from factual
  metadata correctness; JournalPort will not create a citation style engine.
- **ADR-0003:** JSON Schema is the public wire contract; future Python models must conform to it.
- **ADR-0004:** Local-first, adapter-based external services. No provider or MCP is core-required.
- **ADR-0005:** Content hashes cover raw bytes; reproducible logical output additionally requires
  a future canonical JSON serialization specification.

