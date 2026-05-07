# Cross-Agent Handoff Demo

This demo shows the core DevCD differentiator: **Agent A (Copilot) leaves
structured continuity; Agent B (Claude) resumes from the Action Packet —
without recap, without raw logs, without secrets.**

Both agents share one DevCD local event ledger. Neither agent needs to know
what tool the other used.

## Run Agent A's session

```bash
# Replay what Agent A captured during its failed attempt
devcd agentic action-packet-demo \
  --events examples/cross-agent-handoff/agent-a-events.jsonl

# Or inspect the full handoff packet
devcd context handoff-demo \
  --events examples/cross-agent-handoff/agent-a-events.jsonl
```

## Hand off to Agent B

Agent B reads the Action Packet at Turn-0 instead of asking the user to recap:

```bash
# Via CLI (any agent runtime can shell out)
devcd agentic action-packet-demo \
  --events examples/cross-agent-handoff/agent-a-events.jsonl

# Via MCP (OpenClaw, Hermes, or any MCP-native runtime)
# The resource devcd://context/action-packet exposes the same contract.
devcd mcp serve
```

## Verify Agent B continues successfully

```bash
devcd agentic action-packet-demo \
  --events examples/cross-agent-handoff/agent-b-events.jsonl
```

The Action Packet for Agent B's session shows:
- The same `active_goal` Agent A was working on
- `last_failure` from Agent A's failed attempt
- `do_not_repeat` list populated from Agent A's stale strategies
- `suggested_next_action` derived from Agent B's success event

## What the events represent

### agent-a-events.jsonl

| Event | Meaning |
|---|---|
| `goal_update` | Agent A sets the shared goal |
| `branch_change` + `commit` | Git context |
| `test_failure` | Agent A's last failed attempt |
| `note_update` (sensitive) | Private context — withheld by policy |

### agent-b-events.jsonl

| Event | Meaning |
|---|---|
| `goal_update` | Agent B confirms the same goal (from Action Packet) |
| `patch_apply` | Agent B's fix attempt |
| `test_pass` | Agent B succeeded — blockers resolved |
| `next_action` | Agent B captures the handoff for the next session |

## Why this matters

No other tool provides a **runtime-neutral, policy-filtered continuity layer**
that works across Copilot, Claude, Codex, and OpenClaw simultaneously.

- DevCD stores structured metadata only — no raw logs, no file contents, no secrets.
- Policy explains every withheld or allowed decision (see `devcd policy audit`).
- The same Action Packet is available via CLI, HTTP, and MCP — no vendor lock-in.
