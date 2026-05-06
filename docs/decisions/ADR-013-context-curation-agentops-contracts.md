---
id: ADR-013
status: proposed
date: 2026-05-06
supersedes: null
---

# Context Curation And AgentOps Contracts

## Context

DevCD already exposes local continuity through Context Briefs, Agent Passports,
Action Packets, and read-only MCP resources. The next product step is to make
those surfaces more useful for AI power users who move between agent sessions:
fresh agents should receive the smallest high-signal packet possible, know the
single next unit of work, understand how to verify it, and see why some context
was withheld.

This changes public contracts across CLI, MCP, schemas, and agent-facing models.
It also creates a path for future local AgentOps reports and verification-aware
handoffs. That makes the change architectural even though the first
implementation remains additive.

## Decision

Extend the existing ambient and agentic context contracts with additive,
metadata-only fields:

1. `ContinuityPacket` may include local context references, a context budget,
   and a session contract. These fields summarize what was selected, why it was
   selected, and what the next agent should do without embedding raw payloads.
2. `ActionPacket` may include the same session contract, context references,
   budget summary, and a `verification_required` flag. It remains a projection
   of the ambient continuity model, not a separate source of truth.
3. `devcd context budget` may render a local estimate of context size,
   reference count, withheld-context count, and suggested trimming actions.
4. MCP may expose a new `devcd://context/session-contract` read-only JSON
   resource. MCP continues to expose no tools, prompts, shell execution, browser
   automation, memory writes, or agent orchestration.
5. Future verification, task-done, context-adaptation, and AgentOps records must
   remain metadata-only by default and must be policy-explainable before they are
   projected as completed work.

The owning slices remain unchanged:

- `ambient_context` owns Context Briefs, Continuity Packets, context references,
  budgets, and session contracts.
- `agentic_context` owns Action Packet projection.
- `mcp_server` owns read-only MCP protocol adaptation.
- `policy_layer`, `events`, and `host_state_engine` will own later
  verification and adaptation gates when those phases are implemented.

## Non-Goals

- Do not add remote export, cloud sync, telemetry, or hosted services.
- Do not add a GUI or dashboard in this decision.
- Do not expose write-capable MCP tools or prompts.
- Do not capture or inline raw file contents, raw logs, full chat transcripts,
  browser payloads, secrets, or private notes.
- Do not make DevCD execute verification commands. DevCD may record and project
  local metadata about verification, but command execution remains outside this
  contract.
- Do not replace existing Context Brief, Agent Passport, Action Packet, or MCP
  resource names. All first-phase fields and resources are additive.

## Alternatives Considered

1. Add a new ContextOps slice. This would create a new product noun but split
   ownership away from the existing ambient context slice that already owns work
   state, briefs, quality, and control reports.
2. Put all new fields only in Action Packets. This would help the primary
   handoff surface but leave Agent Passport, MCP, schemas, and future API
   surfaces inconsistent.
3. Additive contract extension in the existing slices. This preserves vertical
   ownership, avoids migrations, and keeps the first implementation small.

The additive extension is chosen.

## Consequences

Agents get a clearer start surface: one next action, a definition of done,
verification guidance, policy-filtered context references, and a local budget
summary. Power users get a quick way to inspect whether DevCD is sending too
much, too little, or withheld context before switching agents.

Because public JSON contracts grow additively, downstream consumers must ignore
unknown fields. Existing commands and MCP resources continue to work.

Verification-aware done claims and adaptive curator history remain planned but
must be implemented behind explicit policy decisions in later phases. This
avoids introducing a state-changing workflow without tests and policy coverage.

## Validation

The first implementation phase must include focused checks:

```bash
pytest tests/test_ambient_context.py -v
pytest tests/test_agentic_context.py -v
pytest tests/test_mcp_server.py -v
pytest tests/test_cli.py -v
make check
```

Expected outcomes:

- Continuity Packets expose context references, a budget, and a session
  contract without leaking sensitive payloads.
- Action Packets project the same session contract and budget fields while
  preserving existing fields.
- `devcd context budget --json` emits a machine-readable local budget report.
- MCP lists and reads `devcd://context/session-contract` as JSON while
  `tools/list` and `prompts/list` remain empty.
- Full repository validation continues to pass.