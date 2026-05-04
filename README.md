# DevCD — Developer Context Daemon

[![CI](https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Vertical Slice Architecture](https://img.shields.io/badge/architecture-vertical--slice-informational)](docs/devcd/architecture.md)

**DevCD is a local-first context daemon for agentic developer workflows.**

It observes what you are working on — files, Git state, tasks, notes — normalizes that activity into structured events, maintains a typed state tree, and gates every observation or action through an explicit policy layer. Agents query DevCD instead of asking you to re-explain your context on every prompt.

DevCD is not a model, chat interface, or task runner. It is the **state and policy layer** that lives between your working environment and any AI that assists you.

[Vision](VISION.md) · [Architecture](docs/devcd/architecture.md) · [Contributing](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md)

---

## Why DevCD?

Today, every AI tool starts with a blank slate. You paste context. You describe the task that already lives in three other places. DevCD fixes this:

- **Structured context** — events are normalized and typed, not raw text
- **Scoped memory** — working-memory (short-lived) and durable memory stay separate
- **Explicit policy** — every observation or action passes through a policy decision you can inspect and audit
- **Local-first** — your context never leaves your machine without explicit configuration

## Highlights

- `POST /event` — ingest normalized developer events (IDE, Git, tasks, notes)
- `GET /state` — current typed state tree
- `GET /memory/{scope}` — memory entries by scope (working / durable)
- Default policy: **observations allowed, actions denied**
- Local JSON Lines ledger for all events
- 5-minute TTL working-memory with configurable scopes
- CLI for config initialization and event submission
- MCP-compatible bridge (roadmap)

## Quick Start

**Runtime: Python 3.11+**

```bash
pip install devcd
devcd init        # creates devcd.toml with local-first defaults
devcd run         # starts daemon on 127.0.0.1:8765
```

Submit your first event:

```bash
devcd event ide file_focus --payload '{"path":"src/app.py","duration_seconds":30}'
```

Query the current state:

```bash
curl http://127.0.0.1:8765/state
```

Query working memory:

```bash
curl http://127.0.0.1:8765/memory/working
```

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
CLI / MCP Bridge / External Agents (explicit opt-in)
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
    └── policy_layer/
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
| v0.2 | MCP Bridge — agent-facing read-only context API |
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

