# Safety and failure policy

Fail closed on missing, stale, conflicted, or schema-invalid profiles; blocking parser content;
unknown critical rules; hash mismatch; tampering; or verification failure. Never continue a later
stage merely because an earlier artifact exists: validate its hashes and compatible versions first.
JournalPort core artifacts are the authority. Do not reproduce compliance logic in prompts.
