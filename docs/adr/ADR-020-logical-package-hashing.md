# ADR-020: Logical package hashing and reproducible ZIP

Status: Accepted for M6

Logical package identity hashes canonical manifest content: relative artifact paths and hashes, pinned profile identity, candidate identity, and verification/compliance evidence. It excludes timestamps, absolute paths, and filesystem enumeration order.

ZIP output additionally uses sorted paths, a fixed 1980 timestamp, fixed permissions, and fixed deflate settings. Identical logical inputs and the same rendered metadata produce byte-identical ZIP files. Logical identity remains authoritative when nonsemantic generated timestamps differ.
