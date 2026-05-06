# OpenClaw + DevCD MCP Context — Proof Notes

This note shows how [OpenClaw](https://github.com/openclaw/openclaw) could use
DevCD as a **read-only MCP context source** so a new agent session starts with
structured developer context instead of asking the user to recap everything.

DevCD is not an OpenClaw-only tool. The same `devcd mcp serve` stdio endpoint
works with any MCP-capable client (Claude Code, Cursor, Codex CLI, etc.). This
note only uses OpenClaw as one example consumer.

---

## Prerequisites

```bash
python -m pip install -e ".[dev]"   # install DevCD from this repo
devcd init                           # create devcd.toml with local defaults
devcd run &                          # start the daemon on 127.0.0.1:8765
```

---

## Step 1 — Verify the MCP server starts

`devcd mcp serve` speaks the MCP protocol over stdio (JSON-RPC 2.0,
protocol version `2024-11-05`). The following manual probe was run locally to
confirm the server starts and lists its resources:

```powershell
# Verified locally — run from the repo root
$init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}'
$list = '{"jsonrpc":"2.0","id":2,"method":"resources/list","params":{}}'
"$init`n$list" | devcd mcp serve
```

**Verified server response (resources/list):**

```json
{
  "id": 2,
  "jsonrpc": "2.0",
  "result": {
    "resources": [
      { "name": "context_brief",        "uri": "devcd://context/brief" },
      { "name": "work_state",           "uri": "devcd://context/work-state" },
      { "name": "recent_events",        "uri": "devcd://context/recent-events" },
      { "name": "policy_decisions",     "uri": "devcd://context/policy-decisions" },
      { "name": "withheld_context",     "uri": "devcd://context/withheld-context" },
      { "name": "agent_handoff_packet", "uri": "devcd://context/agent-handoff-packet" },
      { "name": "continuity_packet",    "uri": "devcd://context/continuity-packet" },
      { "name": "recent_timeline",      "uri": "devcd://context/recent-timeline" },
      { "name": "policy_summary",       "uri": "devcd://context/policy-summary" }
    ]
  }
}
```

All resources are **read-only**. No tools are registered. The server exposes
no write surface.

---

## Step 2 — Retrieve a context brief directly

Without OpenClaw running, you can retrieve the same contract the MCP server
would expose by running:

```bash
# Verified locally — produces JSON matching the agent-handoff-packet resource
devcd context handoff-demo \
  --events examples/agent-resurrection/sample-events.jsonl \
  --json
```

The output includes: `goal`, `last_attempt`, `last_failure`, `do_not_repeat`,
`blockers`, `suggested_next_action`, `policy_summary`, and
`withheld_context_summary`. See
[`examples/agent-resurrection/handoff-packet.json`](../agent-resurrection/handoff-packet.json)
for a checked-in fixture of this contract.

---

## Step 3 — OpenClaw MCP configuration (draft)

> **Status: draft** — The MCP config format below is taken verbatim from the
> [OpenClaw configuration reference](https://docs.openclaw.ai/gateway/configuration-reference#mcp)
> (stdio `command`/`args` form). The DevCD side is fully verified. The
> end-to-end flow (OpenClaw loading DevCD resources into its context) has not
> been run because installing and configuring a full OpenClaw gateway is outside
> the scope of this demo. No OpenClaw configuration is mutated by this example.

Add the following block to `~/.openclaw/openclaw.json` (JSON5, comments
allowed):

```json5
// ~/.openclaw/openclaw.json  — add only the mcp section
{
  mcp: {
    servers: {
      devcd: {
        // Starts devcd mcp serve as a stdio child process.
        // Requires devcd to be on PATH from a local checkout install.
        command: "devcd",
        args: ["mcp", "serve"],
      },
    },
  },
}
```

Once loaded, OpenClaw discovers the DevCD resources through its `bundle-mcp`
tool mechanism. The agent can then read:

| Resource URI                            | What the agent learns                          |
|-----------------------------------------|------------------------------------------------|
| `devcd://context/brief`                 | Policy-filtered context brief                  |
| `devcd://context/continuity-packet`     | Domain-neutral Continuity Packet               |
| `devcd://context/agent-handoff-packet`  | Goal, blockers, resurrection context           |
| `devcd://context/recent-timeline`       | Chronological narrative of recent events       |
| `devcd://context/policy-summary`        | Which data is allowed or withheld, and why     |

The `devcd mcp serve` process is spawned once per gateway session and
communicates only over its own stdin/stdout — no network ports, no outbound
calls.

---

## Why a new OpenClaw agent asks fewer questions

Without DevCD, a new agent session starts cold. The first few turns are
usually the user re-explaining:

- What they are trying to build or fix
- Which file or branch is the active focus
- What was tried and why it failed
- What the agent should not repeat

With DevCD, the `agent-handoff-packet` resource encodes all of that as a
typed, policy-filtered JSON object. The agent reads it at turn 0, before the
user types anything, and can start from:

```
goal              → "Continue the resurrection demo after Agent A lost chat context"
last_failure      → "make check still fails: do_not_repeat is absent"
do_not_repeat     → ["Do not repeat the last attempted fix unchanged: ..."]
suggested_next    → "Add a first-class resurrection context before rendering"
```

No re-narration needed. Sensitive data (file contents, notes marked
`sensitivity=sensitive`, browser history) is withheld by policy and replaced
with safe summaries so the agent knows *that* context exists without seeing it.

---

## What this proves

- `devcd mcp serve` is a standards-compliant stdio MCP server (JSON-RPC 2.0,
  protocol `2024-11-05`).
- It exposes 9 read-only resources, no tools, no write surface.
- The OpenClaw `mcp.servers` stdio config format (from the official docs) is
  the correct configuration path for wiring DevCD into OpenClaw.
- `devcd context handoff-demo --json` produces the same JSON contract as
  `devcd://context/agent-handoff-packet` over MCP.
- The policy layer withholds sensitive payloads and replaces them with safe
  summaries, so no secret or user-private content leaks through the MCP
  surface.

---

## What this does not do yet

- The end-to-end OpenClaw + DevCD MCP flow has not been run. The config above
  is a correctly-formatted draft based on verified OpenClaw documentation.
- There is no ClawHub skill for DevCD. A skill could teach OpenClaw *when* and
  *how* to read DevCD resources, but none exists yet.
- DevCD does not push context proactively into OpenClaw. The agent must
  request the resource explicitly (or the skill must instruct it to).
- The `devcd run` daemon must be running before `devcd mcp serve` can read
  live events. The stdio server reads from the local event ledger at
  `~/.devcd/` — no daemon means empty context, not an error.
- Multi-agent routing (e.g. dispatching different DevCD surfaces to different
  OpenClaw agents) is not demonstrated here.

---

## Further reading

- [DevCD MCP ADR](../../docs/decisions/ADR-003-read-only-mcp-context-server.md)
- [Agent Continuity ADR](../../docs/decisions/ADR-007-agent-continuity-golden-path-contract.md)
- [Agent Resurrection example](../agent-resurrection/)
- [OpenClaw MCP configuration reference](https://docs.openclaw.ai/gateway/configuration-reference#mcp)
- [OpenClaw tools and skills](https://docs.openclaw.ai/tools)
