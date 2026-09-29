# ADR-008: Compliance counting semantics

Status: Accepted for M3  
Date: 2026-09-29

JournalPort counts Unicode-normalized NFC text. A word is a Unicode alphanumeric word run that may
contain an internal ASCII hyphen, apostrophe, or right single quotation mark. Underscores and
standalone punctuation are not words. Hyphenated compounds count once. Numeric runs count once.
Character counts are Python Unicode code-point counts after NFC normalization, not bytes or visual
grapheme clusters.

Abstract counts include paragraph text inside canonical abstract sections. Main-text counts include
canonical `main_body` paragraph text and exclude separate `methods`, references, captions, tables,
and supplementary objects. A profile rule must explicitly match this scope; PARTIAL or ambiguous
scope is reported UNKNOWN rather than approximated. Specific-section counting uses the same token
rule. Reference, figure, table, keyword, and author counts use canonical object-list lengths.

Citations/equations embedded as parser text can affect word counts; structured citation/equation
objects alone do not. This deliberately may differ from Microsoft Word, Google Docs, or publisher
portals. The evaluator method/version exposes the convention and changes require a version bump.
