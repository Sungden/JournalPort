# ADR-015: Independent verification boundary

Status: Accepted for M5

M4 execution success is evidence, not proof. M5 therefore reads both artifacts again, reparses the candidate through the M1 parser, reconstructs its canonical model, recalculates hashes and scientific fingerprints, reruns M3 with the pinned resolved profile, and reconciles persisted plan/log/manifest records. The verifier imports stable models and public parser/compliance APIs but never calls executor internals.

Candidate parse failure, source/profile/plan mismatch, and unexplained scientific-object changes fail closed. Verification is offline and deterministic apart from recorded timestamps, which are excluded from the logical report hash.
