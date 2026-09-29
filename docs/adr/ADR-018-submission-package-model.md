# ADR-018: Submission package model

Status: Accepted for M6

Submission packaging is a three-stage process: deterministic plan, explicit build, and independent verification. The artifact taxonomy is journal-neutral; profile rules supply requirements rather than journal-specific Python branches. The package contains copied verified/author-supplied files plus deterministic JournalPort evidence and index files. It never fabricates authorial content or uploads anything.

Portable manifests use package-relative paths and record hashes, sizes, formats, requirement states, validation results, and origin. Absolute source paths exist only in the nonportable build plan.
