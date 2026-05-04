# DevCD Memory Model

DevCD separates memory by lifespan and trust level.

| Scope | Purpose | MVP retention |
| --- | --- | --- |
| `working` | Current session facts, recent actions, active files | 5 minutes |
| `episodic` | Session attempts, failures, debugging paths | planned for v0.2 |
| `semantic` | Stable project rules, preferences, architecture constraints | planned for v0.2 |

Working memory is updated by accepted observation events. It is intentionally short-lived so the daemon can be useful without becoming a hidden long-term recorder.

All memory writes must pass through the policy layer before persistence.
