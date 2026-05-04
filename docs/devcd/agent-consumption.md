# How to consume DevCD as an agent

Use DevCD as a local context source, not as an executor. It gives agents a policy-filtered view of the user's current work state, recent events, memory, and withheld-context summaries.

## Fastest local handoff

Run the checked-in demo from the repository root:

```bash
devcd context handoff-demo --events examples/agent-handoff/sample-events.jsonl
```

Read the expected shape in `examples/agent-handoff/context-brief.md`. The demo is documented in `examples/agent-handoff/README.md` and uses only local JSONL input.

Use the `brief_id` shown in the Markdown when recording local feedback:

```bash
devcd context feedback demo-handoff-brief --kind missing --note "Add the failing test name."
devcd context quality
```

Feedback notes are local full-text input and are withheld from quality output by policy.

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

- `devcd://context/brief`
- `devcd://context/work-state`
- `devcd://context/recent-events`
- `devcd://context/policy-decisions`
- `devcd://context/withheld-context`

It does not expose MCP tools, prompts, shell execution, browser automation, memory writes, or remote HTTP MCP.

## Policy rules for agents

- Treat policy decisions as part of the context, not metadata to ignore.
- Do not ask DevCD for hidden payloads when a brief reports withheld context.
- Do not expect feedback notes to be replayed; quality output reports the kind, brief id, and policy reason.
- Assume actions and remote export are denied unless the policy explicitly allows them.
- Prefer metadata-level context; sensitive, full-text, disabled-source, or disallowed data-class context can be withheld.
