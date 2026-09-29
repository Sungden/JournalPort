# Threat model

JournalPort treats manuscripts, journal webpages, profiles, plans, and packages as untrusted.

| Threat | Primary controls | Residual risk |
|---|---|---|
| Malicious DOCX ZIP/XML | member/size limits, safe parsing, no macro execution | parser-library defects |
| Malicious LaTeX | no TeX execution, traversal/include-cycle checks, unsupported-command blocking | unsupported syntax |
| Journal webpage prompt injection | authority validation, content filtering, evidence IDs, draft-only extraction | novel obfuscation |
| Malicious/tampered profile | closed schemas, provenance validation, pinned versions and hashes | compromised official source/reviewer |
| Malicious transformation plan | plan/profile/input hashes, action allowlist, approval gate | future executor expansion |
| Tampered candidate/package | independent reparse, manifests, file hashes, inventory verification | external post-verification mutation |
| Filesystem/path attack | confined output roots and traversal tests | platform-specific filesystem behavior |
| Provider secret leakage | no provider SDK in core; CI needs no secrets | user-configured future adapters |

Scientific-content preservation takes priority over automation. Unknown or unverifiable states stop
readiness. Security reports must not include confidential manuscript content.
