# Getting Started

DevCD lets a new agent continue from local, policy-filtered context without asking you to recap. The first success point is a warm-started agent workspace, not a running daemon and not a demo fixture. The goal is: Stop re-explaining yourself to AI agents.

Use this guide when you want DevCD to solve the real frustration: a new agent starts cold and asks you to re-explain the work. The path below gets from a fresh checkout to a local Action Packet in 2 to 5 minutes, then leaves live daemon ingestion and MCP integration as explicit follow-up paths. The primary entry point is `devcd setup`, which guides the full install-time setup chain.

<div class="devcd-happy-path">
	<div class="devcd-happy-path__step devcd-callout--checkpoint">
		<strong>1. Start once</strong>
		<p>Run one command to install DevCD and start the setup wizard.</p>
		<code>python -m pip install --disable-pip-version-check --quiet devcd &amp;&amp; devcd setup</code>
	</div>
	<div class="devcd-happy-path__step devcd-callout--trust">
		<strong>2. Configure interactively</strong>
		<p>Select project paths and agent targets in the terminal wizard.</p>
		<code>devcd setup</code>
	</div>
	<div class="devcd-happy-path__step devcd-callout--safe-share">
		<strong>3. Continue from Action Packet</strong>
		<p>Agents can start directly from the seeded handoff context.</p>
		<code>devcd agentic action-packet</code>
	</div>
</div>

If you want the shortest zero-state proof before touching a real workspace, run:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl
```

That demo shows the exact warm-start shape DevCD is trying to produce in your
own workspace. Then come back here for the real path.

## Prerequisites

- Python 3.11+
- A local shell on Windows, macOS, or Linux

## Warm-start path: make the real workspace useful

This path starts with your actual local workspace. It starts no background service until you explicitly choose `devcd run`, makes no remote calls, and keeps agent setup inside explicit terminal choices. After `devcd setup`, the next agent should know to read `devcd agentic action-packet` before asking you to recap; agents with shell access can capture continuity metadata themselves, and agents without shell access only read DevCD context.

Success checkpoint after Step 1:

- `devcd.toml` exists for each selected project.
- Selected agent runtime files contain the DevCD managed continuity block.
- A fresh agent in each configured workspace should start from `devcd agentic action-packet`.
- No daemon was started and no external agent config was mutated.

### Step 1: Install

```bash
python -m pip install --disable-pip-version-check --quiet devcd && devcd setup
```

What happened: the `devcd` CLI is now available and `devcd setup` runs the
interactive setup wizard in one command. It configures the selected projects,
writes the agent-ready files you chose, and seeds an initial goal plus next
action so the first Action Packet is immediately useful. The `--quiet` install
keeps first-run terminal output cleaner.

Optional fast proof before onboarding:

```bash
devcd smoke
```

**Alternatively** with pipx or uvx:

```bash
pipx install devcd
# or: uvx devcd smoke
```

**From source (contributors):**

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
```

If you prefer an isolated local tool install and already use one of these
tooling paths, you can install from the same checkout with `pipx install .` or
`uv tool install .` instead.

Success looks like: `devcd setup` prints a setup summary with configured and
failed project counts, and each configured workspace is ready for
`devcd agentic action-packet`.

Next: open the Action Packet in any configured project.

If it fails: confirm Python 3.11+ is active, then rerun the install. Use
`devcd smoke` for a narrow install check and `devcd doctor` for local
remediation details.

### Step 2: Single-workspace guided alternative (`onboard`)

```bash
devcd onboard
```

What happened: `devcd onboard` runs the full guided local setup for the current
workspace only. It creates or
keeps `devcd.toml`, prepares selected local agent runtime files, and reports
what still needs attention without starting the daemon.

Success looks like: `devcd.toml` exists with loopback, local storage, and policy defaults. Selected agent files contain a managed DevCD continuity block with a small capture routine:

- Copilot: `.github/copilot-instructions.md`
- Claude: `CLAUDE.md`
- Codex and compatible coding agents: `AGENTS.md`
- DevCD startup skill: `.github/skills/devcd-startup-gate/SKILL.md`
- DevCD continuity templates: `.devcd/templates/devcd-first-turn.template.md`, `.devcd/templates/devcd-capture-loop.template.md`

OpenClaw MCP remains optional and is only created when `openclaw` is explicitly selected.

If you want a narrower target list, pass `--agents` with a comma-separated subset.
Use `--archetype builder`, `reviewer`, `researcher`, or `orchestrator` when you
want to override the recommendation explicitly.

Use `--preview` only when you need a read-only plan. Use `--yes` only when you
want to force proposal-based apply behavior in non-interactive runs.

For read-only inspection without changing the workspace, use:

```bash
devcd context workspace-analysis
devcd context profile
```

If you only want the lower-level config primitive, use `init` directly. Most
users should stay on `devcd onboard`:

```bash
devcd init --agent-ready --agents copilot,claude,codex
```

Optional MCP snippet path:

```bash
devcd init --agent-ready --agents copilot,claude,codex,openclaw
```

Next: read the Action Packet the next agent should see first.

If it fails: if config already exists, do not overwrite it blindly; run `devcd doctor` and decide whether to keep, modify, or intentionally reset. Existing instruction files are preserved; DevCD only adds or replaces its marked managed block.

### Step 3: Read the warm-start Action Packet

```bash
devcd agentic action-packet
```

What happened: DevCD renders the handoff surface a fresh coding agent should read first. If local continuity exists, it shows the current goal, latest failure or blocker, stale attempt warnings, suggested next action, and withheld-context policy notes.

Success looks like: the output starts from the work instead of the tool. With an empty ledger, it should say the packet is not ready yet and point to safe metadata capture rather than pretending a demo solved the problem.

Next: if the packet is empty, seed one safe piece of continuity metadata.

If it fails: run `devcd doctor`; it validates local config, policy, ledger, docs, and MCP readiness.

Before ending a session or switching to a fresh agent, enforce closure with:

```bash
devcd agentic completion-check
```

To inspect startup/capture/handoff compliance coverage, run:

```bash
devcd agentic compliance
```

### Step 4: Seed safe continuity when the ledger is empty

```bash
devcd handoff --goal "Try DevCD live continuity" --next-action "Ask the next agent to read the Action Packet"
devcd capture --kind goal --summary "Try DevCD live continuity"
```

What happened: `devcd handoff` stores a compact next-agent handoff, and `devcd capture` remains available when you only want one granular continuity event. Both paths store local metadata only after observation and storage policy allow it. Do not paste raw logs, source text, full chat transcripts, credentials, or private notes into capture fields.

Success looks like: rerunning `devcd agentic action-packet` or `devcd context passport` shows the goal as visible continuity for the next agent.

Next: when a session ends with a useful failure, capture the whole handoff in one command.

```bash
devcd handoff --goal "Try DevCD live continuity" --failure "Example check failed" --next-action "Inspect the failing command output"
```

### Step 5: Open the interactive follow-up report

```bash
devcd quickstart
```

What happened: DevCD reads the configured local ledger and prints the interactive activation report for the onboard flow. The report now includes an Agent Layer console with profile status, chosen archetype, target agents, detected tools, and the next safe command. If no events are visible yet, the report says what is missing; agent-ready instructions tell capable agents how to capture continuity metadata themselves during work.

The handoff-oriented surface remains the Action Packet, and the passport is the
broader continuity view around it:

```bash
devcd agentic action-packet
devcd agentic tasks
```

Success looks like: the output is honest about the current workspace. With an empty ledger, it should not pretend a demo solved the problem or ask you to do bookkeeping; it should point at agent-led capture and make it obvious how to return to the Action Packet.

Next: run `devcd quickstart --json` if another local tool needs the same activation report, including the `agent_layer` contract checked by `devcd smoke`.

If it fails: run `devcd doctor`; it validates local config, policy, ledger, docs, and MCP readiness.

Machine-readable report:

```bash
devcd quickstart --json
```

Optional preview commands are still available when you want to inspect the shape before recording real context. Start with the Action Packet demo; the others are deeper comparisons and compatibility checks:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl
devcd quickstart --demo-events examples/agent-resurrection/sample-events.jsonl
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
devcd context handoff-demo --events examples/agent-resurrection/sample-events.jsonl --json
```

## Live daemon path

Use this path when you want DevCD to accept live local events from CLI calls, hooks, or future editor integrations.

### Step 6: Check readiness

```bash
devcd status
devcd doctor
devcd doctor --fix
```

What happened: `status` summarizes local state; `doctor` gives remediation without mutating external tool configs. `doctor --fix` applies only safe local repairs (for example missing `devcd.toml` and missing `.devcd/agent-layer-profile.json`) and records policy receipts for each repair.

Important: `doctor --fix` does not auto-start the daemon. When `daemon_reachable`
is the only warning, the expected manual recovery step remains `devcd run`.

Success looks like: config, token, daemon, ledger, policy, docs, and MCP checks are understandable.

Next: start the daemon when you are ready for live context.

If it fails: follow the first non-pass `doctor` next step. If the issue is only missing local scaffolding, run `devcd doctor --fix` and review the repair receipts.

`devcd status` reports the daemon endpoint, token source, local workspace, event/state summary, policy mode, memory path, handoff availability, MCP availability, and the next suggested command. `devcd doctor --json` emits the same readiness checks for local automation, and `devcd doctor --fix --json` includes applied or denied local repair receipts.

### Step 7: Start the live daemon path

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

### Step 8: Optional manual live event

The normal agent-ready path does not require you to write DevCD events by hand. Agents with shell access use daemonless capture while they work:

```bash
devcd handoff --goal "Try DevCD live continuity" --failure "Example check failed" --next-action "Inspect the failing command output"
devcd capture --kind goal --summary "Try DevCD live continuity"
devcd capture --kind failure --summary "Example check failed" --next-action "Inspect the failing command output"
devcd capture --kind artifact_ref --summary "CLI entrypoint" --artifact packages/devcd-core/src/devcd/cli.py
```

Each handoff or capture is local, metadata-only, and policy-gated through observation and storage decisions before it reaches the configured ledger. Capture must not include raw file contents, raw logs, full chat text, secrets, or remote data.

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

---

## Set Your North Star

Give every future agent session a persistent orientation — initialize a North Star once:

```bash
devcd vision init --guided
```

Agents receive it automatically in every Action Packet and Continuity Packet.
See [Agent Vision](devcd/agent-vision.md) for the full reference.

To add richer continuity, send a failure with a suggested next action:

```bash
devcd event task test_failure --payload '{"reason":"Example check failed","suggested_next_action":"Inspect the failing command output"}'
```

### Step 9: Get context brief / passport

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

### Step 10: Generate and smoke-test a read-only MCP snippet

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
