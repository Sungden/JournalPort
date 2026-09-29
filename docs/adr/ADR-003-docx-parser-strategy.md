# ADR-003: DOCX Parser Strategy

Status: Accepted for M1  
Date: 2026-09-29

## Options evaluated

| Capability | python-docx | zipfile + XML | Hybrid |
|---|---|---|---|
| Paragraphs/styles/tables | Convenient | Complete but verbose | Convenient where lossless |
| Images/relationships | Partial abstraction | Explicit and traceable | Strong |
| Fields/cross-references | Incomplete | Raw instructions available | Strong |
| OMML | Raw XML needed | Preservable | Strong |
| Tracked changes | Commonly hidden/flattened | Both views visible | Strong |
| Footnotes/endnotes | Limited | Parts directly accessible | Strong |
| Custom XML/objects/text boxes | Limited | Detectable/preservable | Strong |
| Maintenance burden | Low | High | Medium-high |

`python-docx` is MIT licensed and actively used, but its public API cannot provide the required
loss accounting. Python `zipfile` and `xml.etree.ElementTree` are standard-library components.
`lxml` (BSD-3-Clause) remains a later option for namespace/canonicalization performance.

## Decision

M1 uses a low-level Open XML parser with no runtime dependency. It reads ZIP parts, relationships,
body order, fields, OMML, tracked changes, notes, and raw fragments directly. A future hybrid may
use python-docx only for high-level convenience after raw XML inventory establishes that no nodes
were lost. Low-level inspection remains authoritative for unsupported detection.

DOCX is never modified. Malformed packages fail. Ambiguous tracked changes, missing relationships,
embedded objects, and unresolved scientific fields are blocking and preserve raw evidence.

