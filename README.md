# DevCD

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
make check
make run
```

The daemon starts on `127.0.0.1:8765` by default.

## Architecture

DevCD uses Vertical Slice Architecture. Each feature owns its models, service logic, API integration, and tests. Shared kernel code is intentionally small.

See:

- [docs/devcd/architecture.md](docs/devcd/architecture.md)
- [docs/devcd/memory.md](docs/devcd/memory.md)
- [docs/devcd/policy.md](docs/devcd/policy.md)
- [schemas/devcd-state.schema.json](schemas/devcd-state.schema.json)
- [schemas/devcd-event.schema.json](schemas/devcd-event.schema.json)

