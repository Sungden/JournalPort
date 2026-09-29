# Privacy

Manuscripts may be unpublished and confidential. Parsing, audit, planning, transformation,
verification, and packaging (M0–M6) operate locally and can run offline. They do not require an
agent provider or transmit manuscript text.

Guideline discovery/retrieval (M7) uses the network only when explicitly invoked. Retrieved pages
are untrusted and may contain prompt injection. Offline snapshot replay is available. Agent Skills
pass local paths to JournalPort and should expose only structured findings, minimal evidence, and
hashes to their host.

Never send manuscript text, author data, credentials, or generated packages to an external
provider without separate, purpose-specific user authorization. Logs and `skill_run.json` contain
actions, paths, statuses, and hashes—not private model reasoning. Users remain responsible for
access controls, backups, secure deletion, and the policies of any future external service.
