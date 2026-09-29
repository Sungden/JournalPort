# ADR-004: LaTeX Parser Strategy

Status: Accepted for M1  
Date: 2026-09-29

## Options evaluated

| Option | Strength | Limitation |
|---|---|---|
| pylatexenc (MIT) | Good token/node parsing; lightweight | No full TeX expansion; provenance needs work |
| plasTeX (MIT) | Rich document model and macro system | Larger execution surface and normalization drift |
| Pandoc AST (GPL executable) | Broad conversion ecosystem | External binary, lossy source mapping, licensing/distribution boundary |
| Custom scanner | Exact source spans and strict safety | Deliberately narrow grammar |
| Hybrid | Token parser plus raw-source inventory | More complexity, best long-term fidelity |

## Decision

M1 uses a non-executing standard-library scanner for a documented subset: metadata, sectioning,
common citations/references, figure/table/equation environments, labels/refs, and bounded
`input`/`include`. It preserves exact source spans and blocks unknown content-affecting constructs.
This is a safety baseline, not a claim of general TeX parsing.

M2-independent future parser work may adopt pylatexenc behind the same interface, with a raw-source
inventory to detect dropped commands. The parser never compiles, expands arbitrary macros, runs
shell escape, or reads outside the declared root. Include cycles, missing files, traversal, unsafe
I/O commands, and unknown content-affecting macros are explicit blocking records.

