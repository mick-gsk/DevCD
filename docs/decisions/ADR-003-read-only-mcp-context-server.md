---
id: ADR-003
status: proposed
date: 2026-05-04
supersedes: null
---

# Read-Only MCP Context Server

## Context

DevCD should let local MCP-capable agents such as Claude Code, Cursor, Hermes,
and similar clients consume DevCD context without adding remote export, action
execution, or write paths. The ambient context slice already owns the policy-gated
work-state and agent brief domain model, while ADR-002 explicitly left MCP as a
future integration phase after the context brief contract was validated.

The new MCP surface is an export boundary. It must therefore stay local-first,
token-gated, policy-filtered, and read-only.

## Decision

Add a minimal `devcd mcp serve` command that starts a local MCP stdio server. The
server exposes only MCP resources, not MCP tools, prompts, shell execution,
browser automation, memory writes, or agent orchestration.

The MCP adapter will live in a dedicated vertical slice under
`packages/devcd-core/src/devcd/slices/mcp_server/`. It will reuse existing slice
services instead of owning domain behavior:

- `AmbientContextService` for `context_brief`, `work_state`, and
  `withheld_context`
- `StateEngine` and `EventLedger` for local recent event reconstruction
- `PolicyEngine` for local context export decisions and source/data-class
  visibility

The server will support read-only MCP resource reads for:

- `devcd://context/brief`
- `devcd://context/agent-handoff-packet`
- `devcd://context/work-state`
- `devcd://context/recent-events`
- `devcd://context/policy-decisions`
- `devcd://context/withheld-context`
- `devcd://context/recent-timeline`
- `devcd://context/policy-summary`

Every resource response is JSON and includes only policy-visible data or safe
withheld-context summaries. Sensitive or denied payloads must not be included.

Token gating uses the same local bearer token concept as the HTTP daemon. The
CLI accepts `--token`, `DEVCD_TOKEN`, or the local `.devcd/token` file. If a token
exists in settings, the provided token must match it before the stdio server
starts. No network listener is opened for MCP.

## Non-Goals

- Do not expose MCP tools or prompts.
- Do not add mutations, memory writes, shell/browser/actions, or agent
  orchestration.
- Do not add remote HTTP MCP or any remote export path.
- Do not weaken existing policy defaults.
- Do not add telemetry.
- Do not introduce a new persistent storage layer.

## Alternatives Considered

1. Put MCP handling directly in `ambient_context`. This keeps the file count low
   but mixes protocol and transport behavior into the domain slice.
2. Proxy MCP through the existing FastAPI daemon. This reuses HTTP routes but
   adds a second local service dependency and conflicts with the no-remote-HTTP
   MCP MVP boundary.
3. Add a dedicated read-only MCP adapter slice. This keeps the protocol boundary
   explicit while preserving the ambient context slice as the domain owner.

The dedicated adapter slice is chosen because it best preserves Vertical Slice
Architecture and makes read-only protocol tests straightforward.

## Consequences

MCP clients get a stable local context surface through stdio without gaining any
write or action capability. DevCD gains a new export boundary that must remain
policy-filtered and token-gated. The first implementation intentionally keeps the
protocol surface narrow so later MCP capabilities require an explicit design
decision rather than accidental expansion.

## Validation

Implementation must add or update these checks:

```bash
pytest tests/test_mcp_server.py -v
pytest tests/test_cli.py -v
make check
```

Expected outcomes:

- handler tests initialize the server and read `devcd://context/brief` without an
  external MCP client;
- resource-list tests confirm only the five read-only context resources are
  exposed and MCP tools are empty;
- policy tests confirm denied or sensitive context appears only as withheld
  summaries, never as raw payload;
- CLI tests confirm `devcd mcp serve` exists and advertises token/config options;
- the full repository check continues to pass.
