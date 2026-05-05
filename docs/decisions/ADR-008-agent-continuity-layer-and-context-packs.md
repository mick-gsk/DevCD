---
id: ADR-008
status: proposed
date: 2026-05-05
supersedes: null
---

# Agent Continuity Layer and Context Packs

## Context

DevCD is currently positioned as a Developer Context Daemon. That positioning is
accurate for the first mature proof: local developer events, typed work state,
memory, policy, ambient context, read-only MCP resources, and Agent Resurrection
handoff packets.

The underlying problem is broader than developer workflows. AI agents lose
continuity across sessions, tools, models, and roles. Users then repeat intent,
constraints, artifacts, decisions, failed attempts, blockers, and preferences.
The current developer handoff packet proves that local, typed, policy-filtered
context can give a new agent a useful starting point without exposing raw denied
payloads or depending on chat history.

DevCD needs a product and architecture decision that broadens the core
abstraction without overclaiming implementation. Developer Context should remain
the current proof and first supported domain, while the product center becomes a
local-first continuity layer that can later support other domains through
explicit, policy-gated Context Packs.

## Decision

DevCD's core abstraction becomes Agent Continuity, not only Developer Context.
DevCD is the local-first Agent Continuity Layer between a user's local work
environment and the AI agents that assist them.

Developer Context remains the first supported Context Pack. It continues to own
the current mature proof: coding, review, debugging, subagent handoff, local
event recipes, policy-filtered context briefs, and read-only MCP handoff
resources.

Context Packs are the mechanism for broadening DevCD beyond developer workflows.
A Context Pack maps local domain activity into continuity concepts such as
Intent, Activity, Artifact, Conversation, Decision, Attempt, Blocker,
Preference, Withheld Context, and Policy Decision. Packs specialize domain
interpretation; they do not bypass the shared event, state, memory, policy,
surface, or MCP boundaries.

Continuity Packet becomes the domain-neutral abstraction over the current agent
handoff packet. The existing agent handoff packet remains the Developer Context
implementation of this idea until a compatible domain-neutral packet contract is
introduced. Future work must preserve the current CLI, schema, fixture, and MCP
contract until a migration path is documented.

Local-first, policy-gated, read-only-by-default behavior remains mandatory.
Observation, retention, mutation, and export must continue to pass through
explicit policy decisions. Remote export, telemetry, hosted sync, and
write-capable agent actions remain out of scope unless a later ADR defines an
explicit opt-in boundary.

DevCD remains not a model, chat UI, task runner, telemetry service, or remote
exporter.

## Non-Goals

- Do not implement a new Context Pack as part of this decision.
- Do not rename existing public commands, schemas, examples, or MCP resources in
  this decision.
- Do not add remote export, telemetry, hosted services, or outbound network
  calls.
- Do not add MCP tools, prompts, shell execution, or write capabilities.
- Do not replace the existing `ambient_context`, `policy_layer`, `memory_layer`,
  `events`, or `host_state_engine` slices.
- Do not claim support for research, creator, operator, learning, or knowledge
  work connectors before local event sources, policy behavior, fixtures, and
  tests exist.

## Alternatives Considered

1. Keep DevCD permanently framed as Developer Context Daemon. This preserves the
   current README language but makes the product identity narrower than the
   continuity capability already demonstrated by agent handoff.
2. Rebrand immediately around a generic personal context daemon. This is too
   broad and risks implying connector coverage, personal data capture, or remote
   sync that DevCD does not implement.
3. Define Agent Continuity as the core abstraction and Developer Context as the
   first Context Pack. This keeps the current proof honest while creating a
   disciplined path for future non-developer domains.

## Consequences

Future docs and architecture plans should describe DevCD as an Agent Continuity
Layer when discussing product direction, while keeping developer workflows as the
current implemented proof. README, Vision, and use-case updates can happen in
small follow-up changes and should not claim unsupported packs.

The `ambient_context` slice remains the natural home for derived continuity
models, surfaces, and packet generation until multiple packs prove a need for a
separate abstraction. The `policy_layer` remains authoritative for allow/deny
decisions. The `mcp_server` remains read-only and resource-oriented.

Future Context Pack proposals need concrete local event classes, policy defaults,
surface behavior, packet contributions, documentation, and tests. A pack is not
just marketing language; it is an implementation boundary with fixtures and
policy review.

The Continuity Packet will eventually become a compatibility surface. When that
implementation happens, schema, fixtures, CLI output, MCP resources, and tests
must move together. Existing agent handoff packet consumers must keep working
until a clear migration path exists.

## Validation

This ADR is strategic and docs-only. Later implementation must validate the
decision through concrete checks such as:

```bash
pytest tests/test_ambient_context.py -v
pytest tests/test_mcp_server.py -v
pytest tests/test_cli.py -v
make check
```

Expected outcomes for future implementation:

- Developer Context handoff behavior remains compatible with the current schema,
  fixture, CLI, and MCP resource;
- any new Continuity Packet schema preserves policy-safe withheld context and
  explicit export policy decisions;
- any Context Pack has local fixtures proving useful continuity without remote
  export;
- read-only MCP behavior remains read-only;
- the full repository check continues to pass.

## Related

- `docs/superpowers/specs/2026-05-05-agent-continuity-layer-design.md`
- `docs/decisions/ADR-002-agent-context-brief-handoff.md`
- `docs/decisions/ADR-004-context-surfaces.md`
- `docs/decisions/ADR-007-agent-continuity-golden-path-contract.md`
- `docs/superpowers/agent-resurrection.md`