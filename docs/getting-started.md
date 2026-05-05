# Getting Started

DevCD lets a new agent continue from local, policy-filtered context without asking you to recap. The first success point is an agent-ready workspace, not a running daemon and not a demo fixture. The goal is: Stop re-explaining yourself to AI agents.

Use this guide when you want DevCD to solve the real frustration: a new agent starts cold and asks you to re-explain the work. The path below gets from a fresh checkout to a live local passport with as little friction as possible.

## Prerequisites

- Python 3.11+
- A local shell on Windows, macOS, or Linux
- A local checkout of this repository

## Live-first path: make the real workspace useful

This path starts with your actual local workspace. It starts no background service until you explicitly choose `devcd run`, makes no remote calls, and keeps agent setup inside explicit terminal choices. After `devcd init`, you should not need to do DevCD bookkeeping; agents with shell access capture continuity metadata themselves, and agents without shell access only read DevCD context.

### Step 1: Install from checkout

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
```

What happened: the `devcd` CLI becomes available from this checkout.

Success looks like: `devcd --help` lists `quickstart`, `status`, `doctor`, `context`, `agentic`, `mcp`, and `integrations`.

Next: initialize local config for this workspace.

If it fails: confirm Python 3.11+ is active, then rerun the editable install.

### Step 2: Initialize and choose agent setup

```bash
devcd init
```

What happened: DevCD creates `devcd.toml`. In an interactive terminal, choose whether to make the workspace agent-ready and select the agent runtimes you use.

Success looks like: `devcd.toml` exists with loopback, local storage, and policy defaults. Selected agent files contain a managed DevCD continuity block with a small capture routine:

- Copilot: `.github/copilot-instructions.md`
- Claude: `CLAUDE.md`
- Codex and compatible coding agents: `AGENTS.md`
- OpenClaw: `.devcd/openclaw-mcp.json`

For non-interactive setup, pass choices explicitly:

```bash
devcd init --agent-ready --agents copilot,claude,codex,openclaw
```

Next: inspect the local passport and readiness.

If it fails: if config already exists, do not overwrite it blindly; run `devcd doctor` and decide whether to keep, modify, or intentionally reset. Existing instruction files are preserved; DevCD only adds or replaces its marked managed block.

### Step 3: Inspect the local passport

```bash
devcd quickstart
```

What happened: DevCD reads the configured local ledger and prints a policy-filtered activation report. If no events are visible yet, the report says what is missing; agent-ready instructions tell capable agents how to capture continuity metadata themselves during work.

The handoff-oriented surface is the Action Packet:

```bash
devcd agentic action-packet
devcd agentic tasks
```

Success looks like: the output is honest about the current workspace. With an empty ledger, it should not pretend a demo solved the problem or ask you to do bookkeeping; it should point at agent-led capture.

Next: run `devcd quickstart --json` if another local tool needs the same activation report.

If it fails: run `devcd doctor`; it validates local config, policy, ledger, docs, and MCP readiness.

Machine-readable report:

```bash
devcd quickstart --json
```

Optional preview commands are still available when you want to inspect the shape before recording real context:

```bash
devcd quickstart --demo-events examples/agent-resurrection/sample-events.jsonl
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
devcd context handoff-demo --events examples/agent-resurrection/sample-events.jsonl --json
```

## Live daemon path

Use this path when you want DevCD to accept live local events from CLI calls, hooks, or future editor integrations.

### Step 4: Check readiness

```bash
devcd status
devcd doctor
```

What happened: `status` summarizes local state; `doctor` gives remediation without mutating external tool configs.

Success looks like: config, token, daemon, ledger, policy, docs, and MCP checks are understandable.

Next: start the daemon when you are ready for live context.

If it fails: follow the first non-pass `doctor` next step.

`devcd status` reports the daemon endpoint, token source, local workspace, event/state summary, policy mode, memory path, handoff availability, MCP availability, and the next suggested command. `devcd doctor --json` emits the same readiness checks for local automation.

### Step 5: Start the live daemon path

```bash
devcd run
```

What happened: the local API listens on `127.0.0.1:8765` when you explicitly choose to start it.

Success looks like: `devcd status` reports the daemon as reachable and shows the token source.

Next: let an agent capture continuity metadata during work, or send an optional normalized event from another terminal for diagnostics.

If it fails: `devcd quickstart` and `devcd context passport` can still inspect local continuity; run `devcd doctor` for live remediation.

The daemon requires a local bearer token. If `api_token` is not configured, DevCD writes one to `.devcd/token` on startup. CLI commands automatically read `DEVCD_TOKEN` or `.devcd/token` for loopback API calls; direct `curl` calls need the token header explicitly.

Bash:

```bash
TOKEN="$(cat .devcd/token)"
```

PowerShell:

```powershell
$env:DEVCD_TOKEN = Get-Content .devcd/token
```

### Step 6: Optional manual live event

The normal agent-ready path does not require you to write DevCD events by hand. Agents with shell access use daemonless capture while they work:

```bash
devcd capture --kind goal --summary "Try DevCD live continuity"
devcd capture --kind failure --summary "Example check failed" --next-action "Inspect the failing command output"
devcd capture --kind artifact_ref --summary "CLI entrypoint" --artifact packages/devcd-core/src/devcd/cli.py
```

Each capture is local, metadata-only, and policy-gated through observation and storage decisions before it reaches the configured ledger. Capture must not include raw file contents, raw logs, full chat text, secrets, or remote data.

The older live event command remains useful for diagnostics and integrations that already emit normalized events:

```bash
devcd event task goal_update --payload '{"current_goal":"Try DevCD live continuity"}'
```

PowerShell:

```powershell
devcd event task goal_update --payload '{"current_goal":"Try DevCD live continuity"}'
```

What happened: a policy-checked observation is added to the local ledger.

Success looks like: `devcd status` reports at least one event and an active goal after a capture or normalized event exists.

Next: ask DevCD for a live Agent Passport.

If it fails: inspect the policy reason and token source from `devcd status`.

To add richer continuity, send a failure with a suggested next action:

```bash
devcd event task test_failure --payload '{"reason":"Example check failed","suggested_next_action":"Inspect the failing command output"}'
```

### Step 7: Get context brief / passport

```bash
devcd context passport
devcd context brief --surface cli --detail standard
```

What happened: DevCD rebuilds live local state from the configured ledger and renders policy-filtered context.

Success looks like: the Agent Passport tells the next agent what is known, unknown, suggested, and withheld.

Next: inspect policy or connect an MCP consumer.

If it fails: if it says no goal is visible, send a `goal_update` event or import a recipe first.

JSON contract:

```bash
devcd context passport --json --surface coding-agent --pack developer
```

## MCP / OpenClaw integration path

This path is optional. DevCD is not an OpenClaw plugin, ClawHub package, chat interface, model provider, channel gateway, or remote service. It is a local context and policy source that MCP-capable runtimes can read.

### Step 8: Generate and smoke-test a read-only MCP snippet

```bash
devcd integrations openclaw --smoke-test
```

What happened: DevCD prints a copyable MCP snippet and verifies its read-only MCP resource shape.

Success looks like: the smoke test passes without installing OpenClaw, mutating OpenClaw config, or starting external daemons.

Next: copy the snippet into the MCP-capable runtime you choose.

If it fails: fix the local `devcd` command path or run `devcd doctor`.

Hermes-Agent snippet:

```bash
devcd integrations hermes --json --smoke-test
```

## QuickStart defaults vs Advanced

QuickStart defaults are intentionally local and conservative:

- Loopback only: `127.0.0.1`
- Default port: `8765`
- Local config: `devcd.toml`
- Token source: `.devcd/token` or `DEVCD_TOKEN`
- Local ledger and memory: under configured `.devcd/` runtime paths
- Policy default: observations allowed, actions denied
- Remote export: disabled by default
- MCP: read-only resources only, no tools or prompts

Advanced/full control stays explicit:

- Custom host/port: `devcd run --host <host> --port <port>`
- Custom token: `DEVCD_TOKEN=<token>` or `api_token` in `devcd.toml`
- Custom memory/ledger path: configure runtime paths in `devcd.toml`
- Alternate Context Pack: `devcd context passport --pack research`
- MCP consumer integration: `devcd integrations openclaw --smoke-test`
- OpenClaw/Hermes snippets: `devcd integrations openclaw --json` or `devcd integrations hermes --json`

## Local-first defaults

- No telemetry.
- No remote export by default.
- Observations are allowed by default; actions are denied by default.
- Sensitive context is withheld by policy.
- MCP resources are read-only.
- Capture stores structured metadata only; no raw contents, logs, chat transcripts, secrets, or remote data.

## Success Criteria

You are done with the first-run flow when all of the following are true:

- `devcd init` has created `devcd.toml` and, when selected, agent-native instruction files for your runtimes.
- The next agent sees DevCD instructions from the workspace and knows to consult local continuity before asking you to recap.
- `devcd quickstart` prints an Agent Passport from the configured local ledger.
- If the ledger is empty, the visible packet says what is missing and gives real next commands instead of showing a fixture as success.
- After one real capture or event, the visible packet includes goal, latest failure when present, do-not-repeat guidance when present, suggested next action, and withheld-context summary when policy denies raw context.
- `devcd status` and `devcd doctor` explain the current local state.
- For the live path, `devcd event ...` is accepted and `devcd context passport` reflects your local ledger.
- For the integration path, `devcd integrations openclaw --smoke-test` verifies the read-only MCP shape without mutating external config.

## Common next paths

- Continue live: `devcd run`, send one event, then `devcd context passport`
- Connect an agent: `devcd integrations openclaw --smoke-test`
- Inspect policy: `devcd context control`
- Inspect local context: `devcd context state` and `devcd context memory --scope working`
- Convert a pytest failure report into events: `devcd recipe pytest-failure --input examples/event-source-recipes/pytest-failure/input.json`

## Troubleshooting

If the optional preview path fails:

- run `devcd doctor`
- confirm `examples/agent-resurrection/sample-events.jsonl` exists
- confirm `devcd quickstart --demo-events examples/agent-resurrection/sample-events.jsonl --json` returns JSON

If the daemon does not start:

- confirm Python 3.11+ is active
- confirm `devcd` is available in your shell after installation
- run `devcd status` to see config, token, and endpoint state
- run `devcd doctor` for concrete next steps

If the live passport is empty:

- confirm `devcd init --agent-ready` wrote the managed DevCD block for your agent
- if your agent has shell access, let it use `devcd capture --kind goal --summary "..."`
- if you are testing the daemon path, make sure direct HTTP requests include `Authorization: Bearer <token>`
- inspect shell output for validation or policy errors
- run `devcd status` to confirm active workspace, event count, and latest event timestamp
