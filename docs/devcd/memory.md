# DevCD Memory Model

DevCD separates memory by lifespan and trust level.

| Scope | Purpose | MVP retention |
| --- | --- | --- |
| `working` | Current session facts, recent actions, active files | 5 minutes |
| `episodic` | Session attempts, failures, debugging paths | planned for v0.2 |
| `semantic` | Stable project rules, preferences, architecture constraints | planned for v0.2 |

Working memory is updated by accepted observation events. It is intentionally short-lived so the daemon can be useful without becoming a hidden long-term recorder.

All memory writes must pass through the policy layer before persistence.

## Ambient context memory control

The ambient context slice exposes retained context through policy-filtered memory items. Each item includes its scope, summary, source, freshness, confidence, policy reason, creation time, update time, and optional expiry.

Developers can inspect items with `devcd context memory`, correct a retained summary with `devcd context memory-correct`, or remove stale context with `devcd context memory-delete`. Corrections are stored with an audit reason and influence later work-state derivation; deleted or expired items are excluded from future ambient context and agent briefs.
