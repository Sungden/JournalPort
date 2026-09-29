# ADR-002: Canonical Serialization and Hashing

Status: Accepted for M1  
Date: 2026-09-29

## Decision

Canonical serialization is UTF-8 JSON with NFC Unicode, LF newlines, lexicographically sorted
object keys, compact separators, preserved list order, explicit nulls, and no NaN/Infinity.
Integers remain integers; finite floats use Python's deterministic JSON representation but are not
used for scientific source tokens. Scientific numeric spelling remains text.

No general whitespace collapsing occurs during serialization because whitespace can be meaningful
in equations, code, or prose. Formatting-only normalization belongs in explicitly versioned
fingerprint functions. Metadata dictionaries are key-sorted; authors and all manuscript-object
lists retain declared/source order. `logical_hash()` is SHA-256 over these canonical bytes.

Independent text, numeric, citation, reference, equation, asset, and figure/table-reference hashes
are computed from ordered normalized token lists. A whole-document hash is not a substitute.

## Compatibility

Changing any rule above requires a new serialization version and migration tests. JSON indentation,
input key order, and CRLF/LF differences cannot change the logical hash; scientific content can.

