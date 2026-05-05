# How to consume DevCD as an agent

Use DevCD as a local context source, not as an executor. It gives agents a policy-filtered view of the user's current work state, recent events, memory, and withheld-context summaries.

## Fastest local handoff

Run the checked-in continuity demo from the repository root:

```bash
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
devcd context handoff-demo --events examples/agent-resurrection/sample-events.jsonl --json
```

Read the Markdown expected shape in `examples/before-after-agent-continuity/with-devcd.md`. Read the JSON expected shape in `examples/agent-resurrection/handoff-packet.json`. The JSON contract is documented in `schemas/devcd-agent-handoff-packet.schema.json`.

Use the `brief_id` shown in the Markdown when recording local feedback:

```bash
devcd context feedback demo-handoff-brief --kind missing --note "Add the failing test name."
devcd context quality
```

Feedback notes are local full-text input and are withheld from handoff output by policy. The handoff can still report a policy-safe quality note that feedback exists.

To convert a local pytest failure report into DevCD JSONL events:

```bash
devcd recipe pytest-failure --input examples/event-source-recipes/pytest-failure/input.json
```

## Running daemon path

Start DevCD locally:

```bash
devcd init
devcd run
```

Then ask for context through one of these existing surfaces:

- CLI: `devcd context brief --surface cli --detail standard`
- CLI state: `devcd context state`
- HTTP: `GET /context/work-state`
- HTTP: `POST /context/brief`

Direct HTTP clients must call loopback and include the local bearer token. CLI commands read `DEVCD_TOKEN` or `.devcd/token` automatically for loopback calls.

## MCP path

DevCD includes a minimal local MCP stdio server:

```bash
devcd mcp serve
```

It exposes only read-only resources:

- `devcd://context/agent-handoff-packet`
- `devcd://context/brief`
- `devcd://context/work-state`
- `devcd://context/recent-events`
- `devcd://context/policy-decisions`
- `devcd://context/withheld-context`
- `devcd://context/recent-timeline`
- `devcd://context/policy-summary`

Agents that need continuity should prefer `devcd://context/agent-handoff-packet`. It exposes the same JSON contract as `devcd context handoff-demo --json`.

It does not expose MCP tools, prompts, shell execution, browser automation, memory writes, or remote HTTP MCP.

## Policy rules for agents

- Treat policy decisions as part of the context, not metadata to ignore.
- Do not ask DevCD for hidden payloads when a brief reports withheld context.
- Do not expect feedback notes to be replayed; quality output reports the kind, brief id, and policy reason.
- Assume actions and remote export are denied unless the policy explicitly allows them.
- Prefer metadata-level context; sensitive, full-text, disabled-source, or disallowed data-class context can be withheld.
