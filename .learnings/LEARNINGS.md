# Learnings

## [LRN-20260505-002] correction

**Logged**: 2026-05-05T00:00:00Z
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
DevCD brand assets should be treated as a small design system, not quick decorative SVGs.

### Details
The first generated mark and wordmark looked like low-quality placeholder branding. For DevCD, visual assets need to support the product's trust posture: local-first, policy-visible, agent continuity, and pre-alpha honesty. Avoid decorative node diagrams, fake badges inside logo art, and overworked icon details that do not survive README-scale rendering.

### Suggested Action
For future brand updates, define the direction, assets, color tokens, usage rules, and render previews before accepting SVG changes. Prefer a restrained Continuity OS system with reusable tokens over one-off SVG decoration.

### Metadata
- Source: user_feedback
- Related Files: docs/assets/devcd-mark.svg, docs/assets/devcd-wordmark.svg, docs/devcd/brand-system.md
- Tags: branding, docs, visual-identity

---

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
