# With DevCD

A fresh research agent can continue from a policy-filtered continuity packet instead of reconstructing the prior chat.

Run from the repository root:

```bash
devcd context handoff-demo --events examples/research-continuity/sample-events.jsonl --surface research-agent --pack research
```

The generated packet is checked in at `continuity-packet.md`.

## What The New Agent Gets

- The research goal.
- Reviewed source metadata only, not source text.
- The current hypothesis and research decision.
- The failed approach and why it failed.
- A do-not-repeat instruction.
- Policy-safe summaries for withheld full-text notes and disabled browser context.
- A concrete next research step.

## Boundary

The fixture is synthetic and local. The command reads checked-in JSONL only, makes no remote calls, and preserves policy-safe withholding for full-text note content and browser context.
