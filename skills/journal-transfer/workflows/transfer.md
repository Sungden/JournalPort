# Complete transfer workflow

1. Create a local `TransferSession`, hash the source, select privacy mode, and tell the user what may
   be processed remotely. Never copy a real manuscript into the repository.
2. Resolve the pinned target profile and distinguish verified, partial, stale, conflicted, and unknown
   rules. Do not mutate production profiles.
3. Run Core audit and plan. Interpret each finding as deterministic, proposal-allowed, author-input,
   manual, forbidden, or profile-uncertain. Surface parser/agent disagreements.
4. For proposals disclose only required objects, record the disclosure metadata, and run the relevant
   workflow. Pause for factual author input or explicit proposal approval.
5. Store approved payload privately and invoke `journalport approve`; the approval must bind the M10
   action, plan hash, and payload hash. Invoke `journalport apply`—never patch the authoritative file.
6. Follow verification.md. Only a verified candidate may enter packaging.md. Re-audit once, classify
   remaining work, and avoid regeneration loops.
7. Report source/target KEEP, MODIFY, REMOVE, ADD, SPLIT_ARTIFACT, MANUAL_REVIEW, and UNKNOWN items,
   exact hashes/statuses, disclosure count, and limitations.
