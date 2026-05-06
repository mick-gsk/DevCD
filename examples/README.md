# Examples

Use these examples by the outcome you want to evaluate, not by folder name.
The main question should be: what kind of warm start do I want the next agent
to receive?

## Start Here

If you want the shortest honest proof before touching a real workspace, start
with the Action Packet demo:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl
```

That is the product in one move: the next agent starts from a local,
policy-filtered handoff instead of a recap request.

## Pick By Scenario

| Scenario | Start here | Why |
| --- | --- | --- |
| A fresh coding agent should resume the current task immediately | `agentic-action-packet/` | Shortest proof of goal, blocker, do-not-repeat guidance, next action, and withheld-context notes. |
| You want the broader compatibility handoff layer behind the warm-start story | `agent-handoff/` | Shows the older handoff-oriented brief and how it is derived from the same local-first pipeline. |
| You want to inspect a stronger session-loss recovery story | `agent-resurrection/` | Focuses on cross-session continuity after a previous agent lost context. |
| You want a before/after comparison for continuity value | `before-after-agent-continuity/` | Makes the cost of no continuity visible next to the DevCD path. |
| You want to inspect multi-session switching behavior | `agent-switch/` | Demonstrates continuity across agent changes rather than a single restart. |
| You want to explore context packs as workflow-specific continuity contracts | `context-packs/` | Shows how the developer and research continuity shapes differ. |
| You want the short context brief surface rather than the full passport | `context-brief/` | Demonstrates the smaller policy-filtered brief contract. |
| You want event-source or recipe-oriented examples | `event-source-recipes/` | Shows the metadata-first event patterns DevCD expects. |
| You want to inspect research continuity instead of coding continuity | `research-continuity/` | Demonstrates warm-start behavior for research-oriented workflows. |
| You want to see how a read-only MCP consumer can start warm | `openclaw-mcp-context/` | Connects the Action Packet and session-contract story to an MCP-capable runtime. |
| You want a repeatable real-world evaluation session with scoring | `reality-testing/` | Provides a practical scorecard template to measure correctness and quality, not only pass/fail. |

## Read The Fixtures Correctly

- Prefer `agentic-action-packet/` for first evaluation.
- Treat the other folders as comparison points, compatibility layers, or
  workflow-specific extensions.
- Checked-in outputs are proofs of contract shape, not promises that DevCD is a
  hosted platform or a remote service.
- If a fixture includes withheld-context notes, that is part of the proof: the
  next agent learns that context exists without receiving the raw payload.