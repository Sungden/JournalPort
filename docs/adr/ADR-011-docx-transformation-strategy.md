# ADR-011: DOCX transformation strategy

Status: Accepted for M4  
Date: 2026-09-29

M4 uses a hybrid, minimal-patch strategy. Byte-preserving copy and safe filename changes are the only
implemented DOCX operations. Future style or structure work must edit the smallest Open XML parts
directly while copying every untouched ZIP member and relationship. A high-level library must not
round-trip the entire package because it can discard fields, equations, drawings, comments, tracked
changes, custom XML, or unknown extensions.

Any transformation touching an area with M1 `UNSUPPORTED_BLOCKING` content is blocked. Tracked
changes, comments, embedded objects, floating shapes, text boxes, relationship changes, image
conversion, and section relocation are unsupported in this M4 implementation. Execution success is
only candidate generation; M5 must independently reparse and verify it.
