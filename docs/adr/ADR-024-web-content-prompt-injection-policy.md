# ADR-024: Web-content prompt-injection policy

Status: Accepted for M7

Retrieved pages are untrusted data. Script, style, hidden, navigation, aside, and similar non-content regions are removed before evidence segmentation. Text that attempts to issue instructions has no authority to change extraction policy. The versioned prompt tells providers to use only supplied evidence, preserve unknowns, cite evidence IDs, and never fill from model memory.

Authority metadata is validated independently of content. A persuasive rule on a third-party or redirected domain is rejected.
