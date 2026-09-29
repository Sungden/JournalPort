# ADR-012: LaTeX transformation strategy

Status: Accepted for M4  
Date: 2026-09-29

LaTeX parse is not compile. M4 preserves the source tree and permits only lossless copying and safe
candidate filename normalization. Future source edits require exact source locators, old-content
hashes, explicit patches, and postconditions; fuzzy replacement and whole-document regeneration are
forbidden. Custom macros, comments, include structure, labels, citations, and equations must remain
untouched unless a narrowly scoped action explicitly covers them.

Compilation, visual validation, semantic rewriting, and template conversion are outside M4. An
unreliable locator blocks an action.
