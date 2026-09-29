# ADR-025: Skill distribution strategy

Status: Accepted for 0.1.0rc1

## Context

Agent Skills are host-facing instructions and scripts, while the wheel is a runtime library/CLI.

## Decision

Ship Skills in the source repository and sdist, but not the Python wheel. Install them explicitly
into a compatible host. Skills depend on the stable CLI/API; core never imports Skills.

## Consequences

Wheel installs stay host-neutral and small. Skill versions can evolve independently, but users must
install or link Skills separately and compatibility remains declared in `skills/registry.yaml`.
