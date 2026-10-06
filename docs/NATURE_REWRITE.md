# Full scientific rewriting into a Nature-oriented Article draft

`nature-rewrite` goes beyond deterministic `restructure`: it uses a model to rewrite scientific
prose and reorganize evidence from the manuscript. It supports Nature Communications, Nature
Computational Science and Nature Machine Intelligence as research Article targets. This shared
editorial template is not a guarantee that these journals require identical structures. Reviews,
Letters, Perspectives and other Nature titles need separate recipes before they can be supported.

Input can be DOCX, Markdown, plain text, self-contained LaTeX or text-based PDF. Install
`pip install ".[rewrite]"` for conversion. DOCX requires explicit section heading styles. It need not have the six IEEE section names:
the model receives source-section labels and can map other scientific structures. Existing
front matter, reference list and factual declarations are preserved. PDF extraction is text-only and rejects scanned pages; retain and inspect original figures, equations
and two-column reading order. Markdown/LaTeX use local sandboxed Pandoc conversion, with fidelity
warnings and an archived original. Text inputs recognize common scientific headings. Tracked changes, ambiguous section
boundaries and embedded section breaks are rejected rather than silently misinterpreted.

## One-command draft generation

Configure an OpenAI-compatible chat/completions endpoint. It must support JSON object responses.
For a locally served model:

```bash
journalport nature-rewrite private/manuscript.docx \
  --journal nature-communications \
  --base-url http://127.0.0.1:8000/v1 --model YOUR_LOCAL_MODEL \
  --output private/nature-rewrite
```

For a remote provider, use its HTTPS base URL and explicitly add `--allow-remote`; this sends
scientific manuscript paragraphs to that provider. Set the key in an environment variable
(default OPENAI_API_KEY, configurable with --api-key-env). Never pass keys in command arguments.
The provider's privacy/retention policy applies. `--review-model` can select a different reviewer
model; without it, a fresh review call uses the writer model. Neither case guarantees independent
model errors. No remote calls are made during tests with synthetic model adapters.

## Existing Codex login

Select the Codex backend explicitly to use the CLI's existing account authentication:

```bash
journalport nature-rewrite manuscript.md --journal nature-communications \
  --backend codex --output private/nature-rewrite
```

Use `--codex-executable /absolute/path/to/codex` if it is not on PATH. Choosing this backend
transmits manuscript text to the Codex service. Calls are ephemeral, use a temporary read-only
workspace and ignore user configuration. Local/remote HTTP remains available as above.

## What happens

1. Extract source objects and headings, preserving tables, fields, formulas, images and links.
2. Ask the writer to construct Abstract / Introduction / Results / Discussion / Methods, integrating
   related work and conclusions, revising transitions and organizing findings without new facts.
3. Require every source scientific object to be mapped once. Protected non-plain objects must be
   copied unchanged. Check numeric and bracketed numeric citation tokens within each mapped block.
4. Ask a separate review call to compare claims, methods, limitations and attribution against source.
   Missing author input or failed checks prevent candidate publication.
5. Retry rejected proposals with their validation/review feedback up to `--max-attempts` (default 3).
6. Write nature-draft.docx and source inventory, proposal, semantic review, disclosure and status JSON.
   Original DOCX stays unchanged; non-document package parts remain byte-identical. Reparse and check
   the written DOCX against the reviewed proposal. Produce a Markdown reading copy and apply
   single-column, double-spaced draft layout. Render with LibreOffice when available; an unavailable
   or failed render remains explicit in render_report.json.

The draft has state DRAFT_REQUIRES_AUTHOR_REVIEW, never submission_ready. Digit-token checks do not
prove preservation of units, p-value meanings or factual claims; model semantic review is fallible.
Sources with author-year citations or cross-references need special author scrutiny because automatic
citation protection here covers bracketed numeric markers. New subsection design, citation renumbering,
figure order, word limits and title rewriting require editorial review. An empty/missing scientific
section blocks output; the system does not manufacture data. Model context and response limits may
block long manuscripts; chunked cross-section rewriting is not yet implemented.

After author review, use the existing stage-specific `full-format` command, render every page and
verify the submission package. The writing workflow does not itself certify journal compliance or
submit anything. This is an opt-in draft workflow; the original approval-bound M10 execution contract
remains unchanged for authoritative semantic edits and submission-ready candidate verification.
