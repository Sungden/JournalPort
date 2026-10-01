# JournalPort v1 capability matrix

| Layer | Capability | Status | Constraint |
|---|---|---|---|
| Core | DOCX parse/audit | Production ready | Resource-bounded OpenXML parser |
| Core | LaTeX parse/audit | Supported subset | No full transformation executor |
| Core | Audit, plan, approval, provenance | Production ready | Unknowns fail closed |
| Core | Candidate/package verification | Production ready | Strongest manuscript result is `VERIFIED_CANDIDATE` |
| M10 | `REPLACE_ABSTRACT` | Supported | Approval and scientific diff required |
| M10 | `INSERT_REQUIRED_SECTION` | Supported | Author-supplied facts only |
| M10 | `NORMALIZE_SECTION_HEADING` | Supported | Exact supported headings only |
| M10 | `SET_MANUSCRIPT_METADATA` | Supported | Approval-bound metadata only |
| M12 | `REORDER_ADMIN_SECTIONS` | Supported executor | Exact target semantics and safe anchors required |
| M12 | `TITLE_PAGE_RESTRUCTURE` | Conservative supported subset | Separate page and explicit inline identities; missing or inferred fields blocked |
| M12 | `FIGURE_CAPTION_NORMALIZATION` | Supported executor | No missing captions; VERIFIED target required |
| M12 | `EXTRACT_FIGURES_TO_SEPARATE_FILES` | Production validated | Relationships unambiguous; bytes preserved |
| Full DOCX | Structure, legends, tables | Synthetic E2E | HIGH-confidence blocks; known target placement only |
| Full DOCX | Double spacing, single column, left alignment, footer page numbers | Synthetic E2E | VERIFIED profile targets only; existing footer composition blocked |
| Full DOCX | Numeric citation linkage | Conservative subset | Brackets/ranges; live fields preserved; no general style conversion |
| Full DOCX | Explicit supplementary artifact | Supported | One supplied DOCX/PDF copied byte-identically |
| Full DOCX | Headless render backend | Availability detected | NOT_AVAILABLE is not a pass; no full closure without rendering |
| Full DOCX | NC Article 1.3.0 coverage | Partial | NC_DOCX_NOT_CLOSED; unsupported and unknown targets reported |
| Agent | Codex journal-transfer orchestration | Tested | Core `>=1.0.0rc1,<2` |
| Agent | Second host | Pending | No universal compatibility claim |

## Explicitly unsupported

- Generating missing scientific figure captions or deleting apparently uncited references
- Arbitrary scientific-section renaming, merging, or splitting
- Unrestricted scientific prose rewriting or main-text shortening
- Unsafe reference/citation conversion
- Equation, scientific-number, figure-pixel, or arbitrary table-content editing
- Full LaTeX transformation, submission-site automation, or peer-review-response automation
