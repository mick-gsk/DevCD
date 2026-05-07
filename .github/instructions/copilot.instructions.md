# DevCD Codebase Patterns

This repository is a local-first Developer Context Daemon built as a Python monorepo with Vertical Slice Architecture.

## Tech Stack

- Runtime: Python 3.11+
- Language: Python with full type annotations
- API/CLI/UI: FastAPI, Typer, Textual
- Models/settings: Pydantic v2, pydantic-settings
- Lint/format: Ruff
- Typecheck: mypy in strict-oriented repo settings
- Tests: pytest, pytest-asyncio
- Packaging/docs: Hatchling build backend, MkDocs Material

## Anti-Redundancy Rules

- Reuse existing slice models, services, and helpers before creating new abstractions.
- Do not duplicate contract shapes across CLI, API, MCP, docs, and schemas when one typed boundary can stay authoritative.
- Add shared code to `packages/devcd-core/src/devcd/kernel/` only when at least two slices need the same abstraction.
- Prefer extending the owning slice over adding parallel helpers in unrelated packages or scripts.

## Source Of Truth Locations

### Runtime Surfaces

- CLI entry: `packages/devcd-core/src/devcd/cli.py`
- App assembly: `packages/devcd-core/src/devcd/host.py`
- Shared settings: `packages/devcd-core/src/devcd/kernel/settings.py`

### Core Slices

- Event normalization: `packages/devcd-core/src/devcd/slices/events/`
- Git observation: `packages/devcd-core/src/devcd/slices/git_source/`
- State tree: `packages/devcd-core/src/devcd/slices/host_state_engine/`
- Memory: `packages/devcd-core/src/devcd/slices/memory_layer/`
- Policy: `packages/devcd-core/src/devcd/slices/policy_layer/`
- Ambient and agentic context: `packages/devcd-core/src/devcd/slices/ambient_context/`, `packages/devcd-core/src/devcd/slices/agentic_context/`
- MCP surface: `packages/devcd-core/src/devcd/slices/mcp_server/`

### Contracts And Docs

- Public schemas: `schemas/`
- Regression and slice tests: `tests/`
- Product and architecture docs: `docs/devcd/`, `docs/decisions/`
- Examples and demos: `examples/`
- Implementation plan and feature spec context: `specs/002-ambient-context-kernel/plan.md`

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read
`specs/002-ambient-context-kernel/plan.md`.
<!-- SPECKIT END -->

## Code Quality

- Keep changes minimal, typed, and covered by focused tests.
- Treat DevCD as a public product, not a private experiment: favor stable, documented, user-facing behavior over ad hoc local-only shortcuts.
- Preserve local-first privacy defaults: observe by default, deny actions by default, never introduce remote export without explicit policy.
- Every state-changing operation must be explainable through a policy decision.
- Keep public contracts aligned across CLI, API, MCP, docs, schemas, and examples when they describe the same capability.
- Prefer explicit Pydantic models and typed boundaries over ad hoc dict payloads.
- Avoid unnecessary comments and duplicate helpers. Reuse existing slice abstractions before creating new ones.
- Keep FastAPI, CLI, MCP, and TUI entry surfaces thin. Business logic belongs in slice services.
- Update focused tests with behavior changes; broaden scope only when the contract crosses multiple surfaces.

## Stack & Commands

- Install: `python -m pip install -e ".[dev]"`
- Lint: `make lint`
- Format: `make format`
- Typecheck: `make typecheck`
- Tests: `make test`
- Full validation: `make check`
- Smoke: `make smoke`
- Distribution validation: `make distribution`
- Run daemon: `make run`
- Docs: `make docs`

Run `make check` before considering implementation work complete.