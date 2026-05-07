---
id: ADR-015
status: proposed
date: 2026-05-07
supersedes: null
---

# Additive MCP Detail-Level Resource URIs

## Context

DevCD's MCP server is intentionally read-only and resource-only. Central context
resources such as action packets and continuity packets are policy-filtered and
safe, but they can still be larger than some agent turns can reliably consume.

The product goal is to improve token efficiency and fault tolerance for agent
consumers without changing trust boundaries or breaking existing clients.

## Decision

Add two additive read-only URI detail levels for key MCP context resources while
preserving existing URIs as compatible defaults:

- `devcd://context/action-packet/concise`
- `devcd://context/action-packet/detailed`
- `devcd://context/continuity-packet/concise`
- `devcd://context/continuity-packet/detailed`
- `devcd://context/session-contract/concise`
- `devcd://context/session-contract/detailed`

Existing base URIs remain unchanged and continue to be listed and readable:

- `devcd://context/action-packet`
- `devcd://context/continuity-packet`
- `devcd://context/session-contract`

Behavior contract:

- `concise` returns a deterministic reduced field set for high-signal startup and
  low-token reads.
- `detailed` returns full policy-filtered context for deeper debugging and
  reconstruction.
- Base URIs remain backward-compatible default reads.

Ownership remains unchanged:

- `ambient_context` remains the domain source for context objects.
- `mcp_server` remains the read-only protocol adapter.
- `cli` and docs provide usage guidance for URI selection.

## Non-Goals

- Do not add MCP tools or prompts.
- Do not add state mutations, memory writes, or agent orchestration.
- Do not add remote export paths or telemetry.
- Do not remove or rename existing MCP resource URIs.
- Do not weaken policy filtering or local-first defaults.

## Alternatives Considered

1. Replace existing URIs with a single reduced shape.
   - Rejected: would be a breaking contract change.
2. Add query parameters to existing resources.
   - Rejected: current MCP resource contract is URI-based and simpler to discover
     in resource listings.
3. Add explicit `/concise` and `/detailed` URI variants.
   - Chosen: additive, discoverable, and testable without changing existing
     callers.

## Consequences

Agents can choose low-token startup reads by default and escalate to detailed
reads only when needed. Existing integrations remain stable.

The MCP resource catalog grows, so tests and docs must verify that the read-only
boundary and compatibility guarantees are preserved.

## Validation

Implementation must add or update these checks:

```bash
pytest tests/test_mcp_server.py -v
pytest tests/test_cli.py -k "mcp or action-packet or continuity" -v
make check
```

Expected outcomes:

- new concise/detailed URIs are listed and readable for the selected resources;
- concise variants return reduced, deterministic high-signal fields;
- detailed variants return full policy-filtered payloads;
- existing base URIs remain unchanged and continue to pass prior behavior tests;
- MCP continues to expose no tools and no prompts.
