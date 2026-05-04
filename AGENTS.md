# DevCD — Agent Instructions

This document provides context for AI agents (Copilot, Claude, Codex, etc.) working in the DevCD repository.

## Project Summary

DevCD is a **local-first Developer Context Daemon** written in Python. It observes developer activity (IDE events, Git, tasks), maintains a typed state tree, stores scoped memory, and gates every observation or action through an explicit policy layer.

It is **not** a model, chat interface, or task runner. It is the structured state and policy layer between a developer's working environment and any agent that assists them.

## Repository Layout

```
packages/devcd-core/src/devcd/
├── cli.py                  # CLI entry point (Typer)
├── host.py                 # FastAPI application factory
├── kernel/
│   └── settings.py         # Shared settings (Pydantic BaseSettings)
└── slices/
    ├── events/             # Event normalization and ledger
    ├── host_state_engine/  # State tree, event application, state API
    ├── memory_layer/       # Working-memory (TTL) and durable memory
    └── policy_layer/       # Policy decisions, allow/deny, audit log

tests/                      # Pytest tests (mirror slice structure)
schemas/                    # JSON Schemas for events and state
docs/devcd/                 # Architecture, memory, and policy documentation
docs/decisions/             # Architecture Decision Records (ADRs)
```

## Architecture Rules

- **Vertical Slice Architecture**: each slice owns its `models.py`, `service.py`, `api.py`, and tests.
- `devcd/kernel/` is shared infrastructure — only add here when two or more slices need it.
- Do **not** add outbound network calls without explicit policy, docs, and tests for the opt-in boundary.
- Every state-changing operation must return or log policy reasoning.
- Local-first by default: no remote export unless explicitly configured.

## Code Conventions

- Python 3.11+ with full type annotations.
- Pydantic v2 models throughout.
- FastAPI for the HTTP API surface.
- `ruff` for linting and formatting (line length 100).
- `mypy` in strict mode for `packages/devcd-core/src`.
- `pytest` with `pytest-asyncio` for async test coverage.
- Conventional Commits: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`.

## Working on a Slice

1. Add models to `slices/<slice>/models.py`.
2. Add service logic to `slices/<slice>/service.py`.
3. Register routes in `slices/<slice>/api.py` and mount them in `host.py`.
4. Add or update tests in `tests/test_<slice>.py`.
5. Run `make check` before opening a pull request.

## Key Commands

```bash
python -m pip install -e ".[dev]"   # Install with dev dependencies
devcd init                           # Create devcd.toml with defaults
devcd run                            # Start the daemon (127.0.0.1:8765)
make check                           # Lint + typecheck + test
make run                             # Run the daemon
```

## Privacy Model

- Sensitive events (e.g., file content, secrets) are **denied by default** in the policy layer.
- Actions are **denied by default** — observation is allowed, mutations are not.
- Memory is stored locally in `~/.devcd/` by default.
- No telemetry, no remote calls without explicit configuration.

## What NOT to Do

- Do not add features outside the current slice scope unless the issue explicitly spans slices.
- Do not add docstrings or comments to unchanged code.
- Do not introduce network calls without a policy decision record.
- Do not add optional dependencies to `[project.dependencies]`; use `[project.optional-dependencies]`.
