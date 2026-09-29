# Command-line contract — 0.1 release line

Stable commands are `audit`, `plan`, `apply`, `verify`, `package plan`, `package build`,
`package verify`, `profile discover`, `profile refresh-draft`, and
`profile extract-from-snapshot`. `benchmark guideline-extraction` is a reproducibility helper.
Argument names shown by `--help` are stable within the 0.1 release line.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Operation completed and its command-specific success condition was met |
| 2 | Argument parsing failure, manual-review outcome, or verification/readiness failure |
| 3 | Input, missing artifact, malformed JSON, profile, or schema error |
| 4 | Reserved for a future distinct blocked-operation category |
| 70 | Reserved for normalized internal software errors; an unexpected uncaught failure is a bug |

Commands never require parsing pretty console prose for control flow. Core commands write named
JSON artifacts beneath `--output`; `benchmark guideline-extraction` writes JSON to stdout or
`--output`. A nonzero exit never upgrades the status inside an artifact.

Profiles bundled in the wheel are used when a checkout-level `journal_profiles/` directory is not
present. Profile refresh is always explicit and never occurs during install or ordinary commands.
