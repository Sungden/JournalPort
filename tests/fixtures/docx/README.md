# DOCX fixture scenarios

The factory test suite composes deterministic packages for: `basic_article`, `tables`, `figures`,
`citations`, `footnotes`, `OMML`, `tracked_changes` (inserted text, deleted text, replacement,
multiple changes, numeric change, citation change), `fields`, `cross_references`, and
`unsupported_object`. Keeping XML source in code makes every safety-relevant node reviewable and
avoids opaque binary fixture maintenance.

