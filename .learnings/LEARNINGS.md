# Learnings

## [LRN-20260505-001] best_practice

**Logged**: 2026-05-05T00:00:00Z
**Priority**: medium
**Status**: pending
**Area**: policy

### Summary
Capture metadata validation must reject exact sensitive-key markers as well as key/value forms.

### Details
The initial `devcd capture` validation rejected values such as `token=...` or `file_content=...`, but accepted an exact metadata value like `--fingerprint token`. Exact sensitive markers are still unsafe in provenance/fingerprint fields because they can normalize secret-bearing labels into the local ledger.

### Suggested Action
When adding metadata-only capture fields, test both `key=value` and exact `key` inputs for denylisted terms such as `token`, `secret`, `password`, `content`, and `file_content`.

### Metadata
- Source: simplify-and-harden
- Related Files: packages/devcd-core/src/devcd/cli.py, tests/test_cli.py
- Tags: capture, validation, policy

---
