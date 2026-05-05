# DevCD + OpenClaw: Zero re-explanation across coding sessions

> **Draft status**: DevCD MCP server is locally verified.
> The end-to-end OpenClaw gateway flow (OpenClaw loading DevCD resources) is a
> draft — the OpenClaw side has not been run. This document may be submitted to
> `awesome-openclaw-usecases` after end-to-end verification.

---

## Pain Point

Every new agent session starts cold. Within the first few turns the developer
has to re-explain:

- What they are trying to build or fix
- Which file, branch, or task is the active focus
- What was already tried and why it failed
- What the previous agent tried that should not be repeated

This re-explanation is low-value, error-prone, and breaks flow. It is
especially painful when an agent session ends unexpectedly (context limit,
crash, accidental window close) or when the same task is handed off between
different agent surfaces (coding agent → review agent → debugging agent).

---

## What It Does

[DevCD](https://github.com/mick-gsk/DevCD) is a local-first Developer Context
Daemon. It observes IDE events, Git activity, and task results, applies an
explicit policy layer, and exposes the result through a read-only MCP server.

When DevCD is registered as an MCP server in OpenClaw, a new agent session
can read the `agent-handoff-packet` resource at turn 0 and learn:

| Field | Example value |
|---|---|
| `goal` | `"Continue the resurrection demo after Agent A lost chat context"` |
| `last_failure` | `"make check still fails: do_not_repeat is absent"` |
| `do_not_repeat` | `["Do not repeat the last attempted fix unchanged: ..."]` |
| `suggested_next_action` | `"Add a first-class resurrection context before rendering"` |
| `withheld_context_summary` | Safe metadata for denied events (no raw content) |

No re-narration by the developer is required. Sensitive data (file contents,
notes flagged `sensitivity=sensitive`, browser history) is withheld by policy
and replaced with safe summaries so the agent knows *that* context exists
without receiving the raw payload.

### MCP resources exposed

| Resource URI | What the agent learns |
|---|---|
| `devcd://context/agent-handoff-packet` | Goal, blockers, resurrection context, do-not-repeat list |
| `devcd://context/continuity-packet` | Domain-neutral Continuity Packet, developer pack by default |
| `devcd://context/brief` | Policy-filtered context brief for the current session |
| `devcd://context/recent-timeline` | Chronological narrative of recent events |
| `devcd://context/policy-summary` | Which data is allowed or withheld, and why |
| `devcd://context/work-state` | Derived work state from observed events |
| `devcd://context/withheld-context` | Safe metadata for all withheld events |

All resources are **read-only**. No MCP tools are registered. The server
exposes no write surface.

---

## Setup

### 1. Install DevCD

```bash
python -m pip install -e ".[dev]"
```

### 2. Initialise and start the daemon

```bash
devcd init       # creates devcd.toml with local defaults in the current directory
devcd run        # starts the daemon on 127.0.0.1:8765
```

### 3. Verify the MCP server starts

Before touching OpenClaw config, confirm the server is responding:

```powershell
# Verified locally — run from the repo root (PowerShell)
$init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}'
$list = '{"jsonrpc":"2.0","id":2,"method":"resources/list","params":{}}'
"$init`n$list" | devcd mcp serve
```

Expected: a `resources/list` response listing the current read-only DevCD MCP resources.
Full verified output: [`examples/openclaw-mcp-context/README.md`](../../examples/openclaw-mcp-context/README.md).

### 4. Inspect a handoff packet without OpenClaw

```bash
# Verified locally — produces JSON matching the agent-handoff-packet resource
devcd context handoff-demo \
  --events examples/agent-resurrection/sample-events.jsonl \
  --json
```

Checked-in fixture: [`examples/agent-resurrection/handoff-packet.json`](../../examples/agent-resurrection/handoff-packet.json).

---

## OpenClaw MCP Configuration

> **Draft** — the `mcp.servers` config format below follows the
> [OpenClaw configuration reference](https://docs.openclaw.ai/gateway/configuration-reference#mcp)
> (stdio `command`/`args` form). The DevCD command and arguments are verified.
> The end-to-end OpenClaw→DevCD flow has not been run.

Add the `mcp.servers.devcd` entry to `~/.openclaw/openclaw.json`
(JSON5, comments allowed):

```json5
// ~/.openclaw/openclaw.json — add only the mcp.servers.devcd block
{
  mcp: {
    servers: {
      devcd: {
        // Requires `devcd` on PATH from a local checkout install.
        // `devcd run` must be running in the background before starting OpenClaw.
        command: "devcd",
        args: ["mcp", "serve"],
      },
    },
  },
}
```

`devcd mcp serve` communicates only over its own stdin/stdout (one process per
gateway session). It opens no network ports and makes no outbound calls.

---

## Agent Prompt / Context Instruction

Once the MCP server is registered, add a startup instruction to the agent so
it reads DevCD context before asking the developer anything:

```
At the start of every session:
1. Read devcd://context/agent-handoff-packet
2. If `last_failure` is set, acknowledge it and avoid repeating the listed
   `do_not_repeat` items.
3. State the active goal from `goal` and confirm it with the developer in one line.
4. Read devcd://context/policy-summary to understand what context is withheld
   and why before asking the developer to provide it manually.
```

This instruction can be placed in the agent's system prompt or as an OpenClaw
Skill instruction file once an end-to-end verified Skill is ready
(see [openclaw-packaging-spike.md](openclaw-packaging-spike.md)).

---

## Expected Outcome

A session that previously required 3–5 re-explanation turns is reduced to a
single confirmation:

```
Agent:    Goal: "Continue the resurrection demo after Agent A lost chat context".
          Last failure: "make check still fails: do_not_repeat is absent".
          I will not repeat the fix that added only a Last failure section to the renderer.
          Ready to proceed — confirm or redirect?
Developer: Proceed.
```

The developer never re-narrates history. The agent works from structured,
policy-filtered state that DevCD maintains automatically in the background.

---

## Security Notes

- **Read-only**: The MCP server registers no tools. No mutations are possible
  through the MCP interface.
- **Local-only**: `devcd mcp serve` communicates exclusively over stdio. No
  outbound network calls are made. Data stays on the local machine.
- **Policy layer**: Every event is passed through an explicit policy decision
  before it can appear in an MCP resource. Sensitive events (file contents,
  notes flagged `sensitivity=sensitive`, secrets, browser URLs) are withheld and
  replaced with safe summaries. See
  [`devcd policy simulate`](../../docs/devcd/policy.md) for the policy CLI.
- **No secret exposure**: The `payload_content` withheld category prevents raw
  payload content from reaching the MCP layer. A detected prompt-injection note
  event is represented only as:
  `"notes prompt_injection signal was withheld; only source/type metadata is visible"`.
- **Scope**: `devcd init` creates a project-scoped `devcd.toml`. Memory and
  events are stored locally in `~/.devcd/` by default. Nothing leaves the
  machine without explicit opt-in configuration.

---

## Limitations

1. **End-to-end OpenClaw flow unverified**: The MCP config format is taken from
   the OpenClaw documentation. The scenario of OpenClaw actually loading and
   injecting DevCD resources into an agent session has not been run. The DevCD
   MCP server side is fully verified.
2. **Daemon must be running**: `devcd run` must be started before the OpenClaw
   gateway loads the MCP server. There is currently no auto-start mechanism.
3. **Event sources are passive**: DevCD observes events that are explicitly
   pushed to it (IDE plugin, Git hooks, CLI calls). It does not hook into the
   IDE automatically without additional event-source setup.
4. **Context window cost**: Reading every resource at session start adds
   tokens. In practice only `agent-handoff-packet` and `policy-summary` are
   needed for continuity; the others are available on demand.
5. **Not on ClawHub**: DevCD has not been submitted to or published on ClawHub.
  Installation is manual from a local checkout until a package is published.

---

## Verification Status

| Step | Status | Evidence |
|---|---|---|
| `devcd mcp serve` starts and lists resources | Verified locally | [`examples/openclaw-mcp-context/README.md`](../../examples/openclaw-mcp-context/README.md) |
| `devcd context handoff-demo --json` produces valid packet | Verified locally | [`examples/agent-resurrection/handoff-packet.json`](../../examples/agent-resurrection/handoff-packet.json) |
| MCP resources are read-only (no tools registered) | Verified locally | `resources/list` response in README |
| Policy withholds sensitive events correctly | Verified via tests | `make check` → `tests/test_policy_layer.py`, `tests/test_ambient_context.py` |
| OpenClaw gateway loads DevCD resources end-to-end | **Not verified** | Requires full OpenClaw gateway install |
| ClawHub publication | **Not done** | Out of scope for this draft |
