---
id: ADR-002
status: proposed
date: 2026-05-04
supersedes: null
---

# Agent Context Brief Handoff Contract

## Context

DevCD needs a reproducible product proof that a coding agent can recover local
work context without asking the developer to restate it. The existing ambient
context slice already derives work state and exposes `/context/brief`, but the
brief response is still too close to internal models for direct agent handoff:
Git context is indirect, blockers are nested in open loops, and withheld context
does not describe the safe substitute information an agent can still use.

## Decision

Extend the ambient context brief contract inside the existing
`ambient_context` slice. The `/context/brief` response and CLI output will keep
the existing compatibility fields while adding explicit agent-handoff fields:

- `active_goal`
- `relevant_artifacts`
- `git_context`
- `recent_attempts`
- `blockers`
- `suggested_next_steps`
- `withheld_context`
- `policy_decision`

The handoff remains read-only and localhost-first. It reuses the existing state
engine, memory store, and policy engine. No remote export, telemetry, durable
storage layer, or action execution path is added.

Withheld context entries must explain the withheld category, the policy reason,
and any safe replacement information that remains visible. Sensitive or
full-text payloads stay denied by the policy layer and must not be persisted or
included in the brief.

## Non-Goals

- Do not introduce an MCP server in this phase.
- Do not add a new persistent storage layer.
- Do not change default policy allow/deny behavior.
- Do not add new remote connections or exports.
- Do not add a VS Code extension or launch-marketing surface.

## Alternatives Considered

1. Keep the current JSON-only brief unchanged and document it better. This is too
   weak for a product proof because agents still need to infer important fields.
2. Build MCP first. MCP is an important future integration path, but it would add
   a new surface before the local handoff contract is proven.
3. Add a focused handoff contract to the existing ambient context slice. This is
   the smallest path that produces a real agent-usable output while preserving
   existing architecture and policy boundaries.

## Consequences

Agents get a stable, explicit handoff shape without losing backward
compatibility with existing `ContextBrief` consumers. The brief remains derived
from policy-visible state only, so denied sensitive context is represented by
explanations rather than raw content.

MCP remains the next likely integration phase after the handoff contract is
validated. Any MCP MVP should expose this read-only brief contract through the
existing ambient context service and be covered by tests that do not require an
external MCP client.

## Validation

Implementation must add or update these checks:

```bash
pytest tests/test_ambient_context.py -v
pytest tests/test_policy_layer.py -v
pytest tests/test_cli.py -v
make check
```

Expected outcomes:

- a service test confirms the brief contains goal, file, Git context, recent
  attempt, blocker, next steps, and policy boundaries;
- a policy test confirms sensitive context is withheld with an explainable
  reason and no raw sensitive payload is exposed;
- a CLI test confirms the demo/handoff flow is available from the CLI;
- the full repository check continues to pass.
