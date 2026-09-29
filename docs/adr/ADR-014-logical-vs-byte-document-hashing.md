# ADR-014: Logical versus byte document hashing

Status: Accepted for M4  
Date: 2026-09-29

Source and candidate byte hashes protect immutable artifacts. Canonical manuscript hashes and
scientific fingerprints protect logical content. DOCX ZIP metadata and member ordering can change
without a logical document change, so future Open XML transformations must additionally calculate a
normalized package hash over member names and uncompressed contents.

The M4 executor only performs byte-preserving copies, so its preliminary logical-package hash equals
the byte hash. This deliberately narrow equivalence must not be generalized to future DOCX editing.
M5 will independently reparse candidates and compare logical content.
