# ADR-010: Readiness criticality policy

Status: Accepted for M2.5/M3.1  
Date: 2026-09-29

Criticality is JournalPort operational policy, not publisher wording. It is assigned uniformly across
journals after preserving the publisher fact and its provenance.

`critical_for_readiness=true` applies to an explicit mandatory article identity, hard numeric maximum,
required manuscript component, required declaration, or required submission file. It does not mean
editorial importance. `false` applies to recommendations, preferences, permissions, unresolved
applicability, and omissions that do not deterministically establish package noncompliance.

A PARTIAL recommendation is never promoted to critical merely because it is numeric. CONDITIONAL
hard requirements may remain critical, but unresolved applicability yields UNKNOWN, not BLOCKED.
UNKNOWN rules default non-critical until evidence supports both applicability and operational form.
Severity is preserved from the profile and is not used to infer criticality.

Executable metadata (`operator`, `scope`, `machine_checkable`, `critical_for_readiness`) is explicitly
JournalPort's interpretation of cited publisher facts. Migration reports record each decision and do
not attribute this policy language to publishers.
