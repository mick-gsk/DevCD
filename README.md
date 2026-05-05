# DevCD — Local-First Agent Continuity Layer

[![CI](https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Vertical Slice Architecture](https://img.shields.io/badge/architecture-vertical--slice-informational)](docs/devcd/architecture.md)

**DevCD gives agents persistent, policy-safe continuity across sessions.**

DevCD records local work state as typed events and serves policy-filtered context over localhost and read-only MCP. When an agent loses its session, DevCD produces a structured **Continuity Packet** — goal, failure history, stale attempts to avoid, and suggested next action — derived entirely from local events with no remote call or model inference.

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
- Read-only local MCP stdio resources for policy-filtered context
- `devcd integrations openclaw` and `devcd integrations hermes` — copyable local MCP
    config snippets with optional shape checks
- `devcd://context/continuity-packet` — domain-neutral Continuity Packet via MCP
- `devcd://context/agent-handoff-packet` — legacy developer handoff contract via MCP (kept for compatibility)

## Quick Start

**Runtime: Python 3.11+**

DevCD is in early developer preview. Until a PyPI release is published, install it from a local checkout:

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
```

See the core superpower first, without starting a daemon:

```bash
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
devcd context handoff-demo --events examples/agent-resurrection/sample-events.jsonl --json
```

The first command shows what a new agent can continue from after chat history is lost. The second emits the machine-readable handoff packet described by `schemas/devcd-agent-handoff-packet.schema.json` and checked in at `examples/agent-resurrection/handoff-packet.json`.

Then run the local daemon path:

```bash
devcd init        # creates devcd.toml with local-first defaults
devcd run         # starts daemon on 127.0.0.1:8765
```

CLI commands automatically read the local bearer token from `DEVCD_TOKEN` or `.devcd/token`
for loopback API calls. For direct `curl` calls, read the token written by the daemon:

```bash
TOKEN="$(cat .devcd/token)"
```

PowerShell:

```powershell
$env:DEVCD_TOKEN = Get-Content .devcd/token
```

Submit your first event:

```bash
devcd event ide file_focus --payload '{"path":"src/app.py","duration_seconds":30}'
```

PowerShell:

```powershell
devcd event ide file_focus --payload '{"path":"src/app.py","duration_seconds":30}'
```

Query the current state:

```bash
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/state
```

Ask DevCD for a policy-filtered context brief a coding agent can use:

```bash
devcd context brief --surface cli --detail standard
```

Generate the current live Agent Passport from your configured local ledger:

```bash
devcd context passport
devcd context passport --json --surface coding-agent --pack developer
```

Generate a local MCP config snippet for an external runtime and verify DevCD's
read-only MCP shape without editing that runtime's config:

```bash
devcd integrations openclaw --smoke-test
devcd integrations hermes --json --smoke-test
```

Inspect ambient context:

```bash
devcd context state
devcd context memory --scope working
```

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
