---
id: ADR-007
status: proposed
date: 2026-05-05
supersedes: null
---

# Agent Continuity Golden Path Contract

## Context

DevCD already derives agent handoff context from local events and can render it
as Markdown or JSON. The core capability is strongest when a new agent can see
the current goal, latest failure, stale attempted fix, concrete next action, and
policy-safe withheld-context summaries without access to chat history.

The existing implementation proves this through fixture demos, but the product
surface needs a more explicit machine-readable contract, a documented MCP path
for the same packet, and a local recipe CLI path that turns concrete pytest
failure reports into DevCD events.

## Decision

Treat the agent handoff packet as a first-class product contract:

- `devcd context handoff-demo --json` emits the stable JSON packet shape.
- `devcd://context/agent-handoff-packet` exposes the same JSON packet shape over
  the read-only MCP stdio server.
- `schemas/devcd-agent-handoff-packet.schema.json` documents the machine-readable
  packet fields that agents should rely on.
- `examples/agent-resurrection/handoff-packet.json` is the checked-in golden
  fixture for the resurrection demo.
- `devcd recipe pytest-failure --input <file>` converts a local pytest failure
  report into DevCD JSONL events without starting a daemon, uploading data, or
  executing tests.

Feedback and context-quality notes remain local. A context brief may expose a
policy-safe list of recorded quality signals, but it must not leak hidden
feedback note payloads when policy withholds them.

## Non-Goals

- Do not add remote export, telemetry, hosted services, or outbound network
  calls.
- Do not add MCP tools, prompts, shell execution, or write capabilities.
- Do not replace the existing ambient-context model; keep backward-compatible
  context brief fields.
- Do not auto-run pytest or mutate the user's repository from the recipe CLI.

## Alternatives Considered

1. Keep the Markdown demo as the only product proof. This is easy to read but
   weak for agents and MCP clients that need a stable contract.
2. Add a new `agent_handoff` slice. This creates ownership clarity, but it would
   duplicate Ambient Context behavior before the contract needs independent
   state or policy rules.
3. Stabilize the contract inside the existing Ambient Context, Events Recipe,
   MCP, and CLI boundaries. This keeps the product pass narrow while making the
   visible superpower easier to consume.

## Consequences

The handoff JSON shape becomes a compatibility surface. Future changes should
update the schema, JSON fixture, CLI tests, and MCP tests together. Documentation
should present the agent-resurrection flow as the shortest path to value, while
the daemon/state quickstart remains available for users who need lower-level
runtime details.

The pytest recipe CLI is intentionally a converter. It creates local DevCD event
records but does not decide whether to store, export, or act on them. Normal
policy handling still occurs when those events are accepted by the state engine
or daemon.

## Validation

Implementation must verify:

```bash
pytest tests/test_cli.py::test_agent_resurrection_json_fixture_matches_cli_output -v
pytest tests/test_cli.py::test_recipe_pytest_failure_cli_emits_devcd_jsonl -v
pytest tests/test_mcp_server.py::test_mcp_server_agent_handoff_packet_matches_cli_contract_fields -v
make check
```

Expected outcomes:

- the checked-in JSON fixture matches `devcd context handoff-demo --json` for the
  resurrection events;
- the JSON fixture contains the contract fields defined in the schema;
- the MCP handoff packet exposes the same core contract fields as the CLI JSON;
- pytest failure reports can be converted to local DevCD JSONL events;
- sensitive fixture payloads do not appear in handoff JSON or MCP handoff
  packets except inside explicitly sensitive local recipe output events.