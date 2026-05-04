# DevCD — Developer Context Daemon

[![CI](https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Vertical Slice Architecture](https://img.shields.io/badge/architecture-vertical--slice-informational)](docs/devcd/architecture.md)

Developer Context Daemon (DevCD) is a local-first context host for agentic developer workflows. It models the current work state of a developer, keeps short-lived and durable memory separate, and gates every observation or action through an explicit policy layer.

DevCD is not a foundation model, chat frontend, or task scheduler. It is the state and policy layer that lets agents understand what is currently happening without asking the developer to restate context in every prompt.

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

## MVP Surface

- `POST /event` accepts normalized developer events.
- `GET /state` returns the current state tree.
- `GET /memory/{scope}` returns memory entries by scope.
- Default policy allows observation and denies actions.
- Runtime data is local by default.

## Development

```bash
python -m pip install -e ".[dev]"
devcd init
make check
make run
```

The daemon starts on `127.0.0.1:8765` by default.

`devcd init` creates `devcd.toml` with local-first defaults. The same settings can be overridden with `DEVCD_` environment variables.

Submit a normalized event to a running daemon:

```bash
devcd event ide file_focus --payload '{"path":"src/app.py","duration_seconds":30}'
```

Submit current Git context from a repository:

```bash
devcd git-snapshot --repo .
```

## Architecture

DevCD uses Vertical Slice Architecture. Each feature owns its models, service logic, API integration, and tests. Shared kernel code is intentionally small.

See:

- [docs/devcd/architecture.md](docs/devcd/architecture.md)
- [docs/devcd/memory.md](docs/devcd/memory.md)
- [docs/devcd/policy.md](docs/devcd/policy.md)
- [schemas/devcd-state.schema.json](schemas/devcd-state.schema.json)
- [schemas/devcd-event.schema.json](schemas/devcd-event.schema.json)

