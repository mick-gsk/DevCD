# DevCD — Local-First Agent Continuity Layer

[![CI](https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Vertical Slice Architecture](https://img.shields.io/badge/architecture-vertical--slice-informational)](docs/devcd/architecture.md)

**DevCD lets a new agent continue from local, policy-filtered context without asking you to recap.**

DevCD records local work state as typed events and serves policy-filtered context over localhost and read-only MCP. When an agent loses its session, DevCD produces a structured **Continuity Packet** or **Agent Passport** with the current goal, latest failure, do-not-repeat guidance, suggested next action, and withheld-context summary. The packet is derived entirely from local metadata with no remote call or model inference.

The product goal is simple: **Stop re-explaining yourself to AI agents.** After installation and `devcd init`, agents with shell access can keep the ledger useful by running `devcd capture` themselves during normal work. Agents without shell access only read DevCD context and make no false auto-capture claim.

The first proof is **developer workflow continuity**: coding agents can resume from where the previous session stopped. A synthetic research fixture now exercises the same local-first, policy-filtered packet path through **Context Packs** without adding connectors or remote export.

Use it as a read-only MCP context source for MCP-native agent runtimes such as OpenClaw.

The product core is local-first work state, typed context, policy-filtered context briefs, a localhost API, and no telemetry.

[Getting Started](docs/getting-started.md) · [Use Cases](docs/use-cases.md) · [Agent Resurrection](docs/superpowers/agent-resurrection.md) · [Vision](VISION.md) · [Architecture](docs/devcd/architecture.md) · [Contributing](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md)

Start here if you want the shortest path to value:

- [Agent Resurrection](docs/superpowers/agent-resurrection.md) to see the five-minute handoff packet: goal, latest failure, stale fix to avoid, suggested next action, and policy-safe withheld context
- [Getting Started](docs/getting-started.md) to run DevCD, submit one event, and inspect state locally
- [Use Cases](docs/use-cases.md) to see where DevCD helps today
- [Architecture](docs/devcd/architecture.md) once you want the slice and data-flow details

---

## Why DevCD?

Today, every AI tool starts with a blank slate. You paste context. You describe the task that already lives in three other places. DevCD fixes this:

- **Structured context** — events are normalized and typed, not raw text
- **Scoped memory** — working-memory (short-lived) and durable memory stay separate
- **Explicit policy** — every observation or action passes through a policy decision you can inspect and audit
- **Local-first** — your context never leaves your machine without explicit configuration
- **Agent resurrection** — when a session ends and context is lost, DevCD produces a policy-filtered handoff packet from local events: current goal, latest failure, stale attempts to avoid, and suggested next action

See [docs/superpowers/agent-resurrection.md](docs/superpowers/agent-resurrection.md) for a runnable demo.

## Highlights

- `POST /event` — ingest normalized developer events (IDE, Git, tasks, notes)
- `GET /state` — current typed state tree
- `GET /memory/{scope}` — memory entries by scope (working / durable)
- `GET /context/work-state` — derived active intent, artifacts, loops, blockers, and suggestions
- `POST /context/brief` — policy-filtered local agent context brief
- `GET/PATCH/DELETE /context/memory` — inspect and control retained context
- Default policy: **observations allowed, actions denied**
- Local JSON Lines ledger for all events
- 5-minute TTL working-memory with configurable scopes
- CLI for config initialization and event submission
- `devcd capture` — daemonless, policy-gated continuity metadata capture for agents
- `devcd agentic action-packet` — policy-filtered next-action packet for the next local agent
- `devcd agentic tasks` — metadata-only Scout Tasks when the Action Packet is not ready
- Read-only local MCP stdio resources for policy-filtered context
- `devcd integrations openclaw` and `devcd integrations hermes` — copyable local MCP
    config snippets with optional shape checks
- `devcd://context/continuity-packet` — domain-neutral Continuity Packet via MCP
- `devcd://context/action-packet` — agentic Action Packet via MCP
- `devcd://context/agent-handoff-packet` — legacy developer handoff contract via MCP (kept for compatibility)

## Quick Start

**Goal: make this workspace agent-ready in one terminal setup.** The first success point is not "the daemon starts" and it is not a demo. It is that the next Copilot, Claude, Codex, or OpenClaw session knows to consult local DevCD continuity before asking you to recap.

**Prerequisites:** Python 3.11+, a local checkout, and a shell on Windows, macOS, or Linux.

### Step 1: Install from checkout

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
```

What happened: the `devcd` CLI becomes available from this checkout.

Success looks like: `devcd --help` lists `quickstart`, `status`, `doctor`, `context`, `mcp`, and `integrations`.

Next: initialize local config for your real workspace.

If it fails: confirm Python 3.11+ is active, then rerun the editable install.

### Step 2: Initialize and make the workspace agent-ready

```bash
devcd init
```

What happened: DevCD creates `devcd.toml`. In an interactive terminal, it can also ask which agent runtimes should read DevCD continuity and then writes standard workspace instruction files such as `.github/copilot-instructions.md`, `CLAUDE.md`, `AGENTS.md`, plus a local OpenClaw MCP snippet under `.devcd/` when selected.

Success looks like: the selected agent files contain a managed DevCD block telling agents to run `devcd agentic action-packet`, fall back to `devcd agentic tasks` or `devcd context passport`, use `devcd capture` for safe continuity metadata when shell access is available, or read the `devcd://context/action-packet` MCP resource before asking you to recap.

Non-interactive equivalent:

```bash
devcd init --agent-ready --agents copilot,claude,codex,openclaw
```

Next: inspect the current local passport and readiness.

If it fails: if config already exists, keep it and inspect with `devcd doctor` before choosing any reset. Existing agent instruction files are preserved; DevCD only adds or replaces a clearly marked managed block.

### Step 3: Inspect the live passport

```bash
devcd quickstart
```

What happened: DevCD reads your configured local ledger and prints a policy-filtered Agent Passport. If no events are visible yet, the passport says that plainly; agent-ready instructions tell capable agents how to capture continuity metadata themselves during work.

Success looks like: the output is useful for your current workspace. With an empty ledger, it should point at agent-led capture instead of pretending a demo solved the problem or asking you to do bookkeeping.

Next: run `devcd quickstart --json` if another local tool needs the same activation report, or start the daemon when you want live event ingestion.

If it fails: run `devcd doctor`; it validates local config, policy, ledger, docs, and MCP readiness.

Machine-readable activation report:

```bash
devcd quickstart --json
```

### Step 4: Check readiness

```bash
devcd status
devcd doctor
```

What happened: `status` summarizes local state; `doctor` gives remediation without mutating external tool configs.

Success looks like: config, token, daemon, ledger, policy, docs, and MCP checks are understandable.

Next: start the live daemon path.

If it fails: follow the first non-pass `doctor` next step.

### Step 5: Start the live daemon path

```bash
devcd run
```

What happened: the local API listens on `127.0.0.1:8765` when you explicitly choose to start it.

Success looks like: `devcd status` reports the daemon as reachable and shows the token source.

Next: let an agent capture continuity metadata during work, or send an optional normalized event from a second terminal for diagnostics.

If it fails: `devcd quickstart` and `devcd context passport` can still inspect local continuity; run `devcd doctor` for live remediation.

### Step 6: Optional manual live event

The normal agent-ready path does not require you to write DevCD events by hand. Agents with shell access use `devcd capture` for metadata-only continuity while they work:

```bash
devcd capture --kind goal --summary "Try DevCD live continuity"
devcd capture --kind failure --summary "Example check failed" --next-action "Inspect the failing command output"
```

These captures do not require the daemon. They write only structured metadata to the configured local ledger after observation and storage policy allow the event. They must not include raw file contents, raw logs, full chat text, or secrets.

The older live event command remains useful for diagnostics and integrations that already emit normalized events:

```bash
devcd event task goal_update --payload '{"current_goal":"Try DevCD live continuity"}'
```

PowerShell uses the same JSON quoting for this command:

```powershell
devcd event task goal_update --payload '{"current_goal":"Try DevCD live continuity"}'
```

What happened: a policy-checked observation is added to the local ledger.

Success looks like: `devcd status` reports at least one event and an active goal after a capture or normalized event exists.

Next: print a live Agent Passport.

If it fails: inspect the policy reason and token source from `devcd status`.

### Step 7: Get context brief / passport

```bash
devcd context passport
devcd context brief --surface cli --detail standard
```

What happened: DevCD rebuilds live local state from the configured ledger.

Success looks like: the Agent Passport tells the next agent what is known, unknown, suggested, and withheld.

Next: inspect policy or connect an MCP consumer.

If it fails: if it says no goal is visible, send a `goal_update` event or import a recipe first.

### Step 8: Optional MCP/OpenClaw integration

```bash
devcd integrations openclaw --smoke-test
devcd integrations hermes --json --smoke-test
```

What happened: DevCD prints copyable MCP snippets and verifies the read-only MCP resource shape.

Success looks like: the smoke test passes without installing OpenClaw, mutating external config, or starting external daemons.

Next: copy the snippet into the MCP-capable runtime you choose.

If it fails: fix the local `devcd` command path or run `devcd doctor`.

### QuickStart defaults vs Advanced

QuickStart defaults:

- Loopback only: `127.0.0.1`
- Default port: `8765`
- Local config: `devcd.toml`
- Token source: `.devcd/token` or `DEVCD_TOKEN`
- Local ledger and memory: under the configured `.devcd/` runtime paths
- Policy default: observations allowed, actions denied
- Remote export: disabled by default
- MCP: read-only resources only, no tools or prompts

Advanced/full control:

- Custom host/port: `devcd run --host <host> --port <port>`
- Custom token: `DEVCD_TOKEN=<token>` or `api_token` in `devcd.toml`
- Custom memory/ledger path: configure runtime paths in `devcd.toml`
- Alternate Context Pack: `devcd context passport --pack research`
- MCP consumer integration: `devcd integrations openclaw --smoke-test`
- OpenClaw/Hermes snippets: `devcd integrations openclaw --json` or `devcd integrations hermes --json`

### Local-first defaults

- No telemetry.
- No remote export by default.
- Observations are allowed by default; actions are denied by default.
- Sensitive context is withheld by policy.
- MCP resources are read-only.
- Capture stores structured metadata only; no raw contents, logs, chat transcripts, secrets, or remote data.

### Next paths

- Continue live: `devcd run`, send one event, then `devcd context passport`
- Connect an agent: `devcd integrations openclaw --smoke-test`
- Inspect policy: `devcd context control`
- Try the OpenClaw MCP path: `devcd integrations openclaw --smoke-test`

See [examples/context-brief](examples/context-brief/README.md) for a reproducible text demo of the two-minute context-brief flow.

## Boundary

DevCD is not a model, chat interface, task runner, remote exporter, or telemetry service. It is the **state and policy layer** that lives between your working environment and any AI that assists you.

Context Packs define which event types and surfaces each domain (developer, research, …) needs. The developer pack is the first mature proof. The research pack is a synthetic metadata-only fixture and renderer path; it does not add browser, note, or library connectors.

## Architecture

```text
IDE / Git / Tasks / Notes
          |
          v
    Normalized Events
          |
          v
+---------------------+       +----------------+
| DevCD Host          | ----> | Policy Layer   |
|                     |       | observe/action |
|  Event API          |       +----------------+
|  State Engine       |
|  Memory Layer       | ----> local ledger / memory store
+---------------------+
          |
          v
CLI / read-only MCP stdio / External Agents (explicit opt-in)
```

DevCD uses **Vertical Slice Architecture**. Each feature domain owns its models, service logic, API routes, and tests. The shared kernel is intentionally small.

```
packages/devcd-core/src/devcd/
├── cli.py
├── host.py
├── kernel/settings.py
└── slices/
    ├── events/
    ├── host_state_engine/
    ├── memory_layer/
    ├── policy_layer/
    └── ambient_context/
```

See: [Architecture](docs/devcd/architecture.md) · [Memory](docs/devcd/memory.md) · [Policy](docs/devcd/policy.md) · [Schemas](schemas/)

## Development

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
devcd init
make check       # lint + typecheck + test
make run         # run the daemon
```

The daemon starts on `127.0.0.1:8765` by default. Override with `DEVCD_HOST` and `DEVCD_PORT` environment variables, or via `devcd.toml`.

## Configuration

`devcd init` creates `devcd.toml` with local-first defaults:

```toml
[daemon]
host = "127.0.0.1"
port = 8765

[memory]
working_ttl_seconds = 300

[policy]
default_observe = true
default_action = false
```

## Security Model

- Local storage only by default — no telemetry, no remote calls.
- Sensitive events are denied by the default policy.
- Actions are denied by default. Observations are opt-in per event class.
- Policy reasoning is recorded for every accepted observation or action.

See [SECURITY.md](SECURITY.md) for the vulnerability reporting policy.

## Roadmap

| Version | Focus |
|---------|-------|
| **v0.1** | Foundation — event API, state engine, memory, policy, CLI ✅ |
| v0.2 | MCP Bridge hardening — read-only MCP context API MVP exists; hardening next |
| v0.3 | IDE Integration — VS Code extension, Git hook events |
| v0.4 | Policy Editor — human-readable rules, per-class allow/deny |

See [VISION.md](VISION.md) for the full product direction.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, commit format, and architecture rules.

- [Good first issues](https://github.com/mick-gsk/DevCD/labels/good%20first%20issue)
- [Open issues](https://github.com/mick-gsk/DevCD/issues)
- [Discussions](https://github.com/mick-gsk/DevCD/discussions)

## Community

DevCD is early-stage. The best way to contribute is to open an issue describing your use case or limitation.

Built and maintained by [Mick Gottschalk](https://github.com/mick-gsk).
