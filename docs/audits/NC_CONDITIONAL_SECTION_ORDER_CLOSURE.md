# Conditional section ordering closure result

Scope: only the availability ordering blocker. Profile 1.3.2 and its official provenance were not changed or re-audited.

Core now supports ORDER_CONDITIONAL_SECTIONS using the verified profile's conditional_order list and separately supplied author-confirmed applicability, included in the plan hash. No Nature Communications name is used by the ordering algorithm. A missing condition never silently activates it. Only reliable, unique, HIGH-confidence headings and nonempty bounded paragraph blocks are movable. Missing statement bodies require author input; duplicate/ambiguous headings and unlocatable References fail closed.

The operation replaces only the selected block slots and preserves each heading/body node, including References. Before/after paragraph-text body hashes are recorded in execution_result.json. Independent verification compares source/candidate body hashes, reference/citation identity and scientific invariants; ordering-only verification also compares the complete expected XML node sequence. Hashes retain exact text and paragraph boundaries, not style or run segmentation. Reference rendering cannot be combined with a planned conditional move that requires unchanged References body. Existing verified structure constraints are composed with the confirmed conditional target, without changing profile provenance.

Synthetic case with supplied statements and already conforming references:

- formatting targets: 12/12; coverage 100%; unresolved formatting-critical targets 0.
- target format: FORMAT_TARGET_VERIFIED.
- content preservation: VERIFIED_CANDIDATE; unexpected_changes []; failure_reasons [].
- Data Availability, Code Availability and References before/after body hashes identical.
- repeat execution from source byte-idempotent; already-correct order is a no-op.
- render: RENDER_PASS. Three public synthetic rendered pages were inspected: correct availability order, readable text, figures/equation/legends/tables/references present, no evident clipping, overlap or unexpected blank page. Original borderless table styling remains unchanged. This is not private manuscript visual approval or a Word repair-dialog test.

Private manuscript findings and validation results are not distributed. Synthetic coverage does not
establish closure for any other manuscript. Missing statements require actual author input; no
repository, accession, URL or factual declaration may be invented. Public visual evidence uses only
synthetic pages. Real sessions, ledgers, sources and candidates remain outside the release.
