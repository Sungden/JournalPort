# IEEE to Nature Communications scientific structure

`restructure` is a local DOCX editorial migration, separate from journal formatting.
It implements an author-selected recipe, not a claim that the journal mandates this layout.

```bash
journalport restructure manuscript.docx --recipe ieee-to-nature-communications \
  --plan-only --output private/structure-plan
# Inspect structure_plan.json, especially source sections, moves and editorial-review tasks.
journalport restructure manuscript.docx --recipe ieee-to-nature-communications \
  --reviewed-plan private/structure-plan/structure_plan.json --output private/structure-output
```

The command expects six uniquely identifiable, nonempty top-level sections: Introduction,
Related work, Methods, Results, Discussion and Conclusion. English aliases and Roman/Arabic
heading prefixes are recognized. Explicit Heading1/outline level 0 is required; nested headings
remain inside their parent sections. Unknown intervening headings, tracked changes, content
controls and embedded section breaks block execution. Unstyled or nonstandard manuscripts
require author-reviewed heading preparation first.

The candidate has Introduction, Results, Discussion and Methods as top-level scientific sections.
Related work becomes a subsection at the end of Introduction; Conclusion becomes a subsection
at the end of Discussion. Nested headings in these two sections are demoted by one level.
Manual numbering and all heading text remain unchanged; automatic numbering properties on demoted
headings are removed. Review section numbers and section cross-references afterward.

The source stays unchanged. Other DOCX package parts (including media, relationships and styles)
are byte-identical; paragraphs, formulas, tables and scientific text are moved without rewriting.
The output contains manuscript.docx, structure_plan.json, structure_verification.json and
EDITORIAL_REVIEW.md. Plan/source mismatch or candidate changes fail verification. Use a new output
directory for each attempt. This command deliberately does not report submission readiness or
completed scientific rewriting.

## Agent-assisted academic editing

After migration, an agent can propose integration of related-work paragraphs into the introduction,
move interpretive comparisons to discussion, merge overlapping conclusion prose, revise transitions,
and organize results around findings. Each is a semantic proposal, requiring the original/proposed
text and author review under the existing approval workflow. Preserve claims, numbers, equations,
references and figure identities. Missing experiments, facts and declarations cannot be invented.
The deterministic command itself does not call an LLM or transmit the manuscript.

Run the existing stage-specific `full-format` workflow on the resulting candidate, then render and
inspect every page. Reordered numeric citations, figure first mentions and Word section cross-references
remain editorial checks. Structure verification does not establish those orders or visual correctness.
