# Changelog

All notable changes to DevCD will be documented in this file.

The project follows Conventional Commits and Semantic Versioning once public releases begin.

## 0.1.0 - Unreleased

Short version: Initial local-first context daemon foundation.

### Added

- Python monorepo scaffold with Vertical Slice Architecture.
- MVP daemon API for `POST /event`, `GET /state`, and `GET /memory/{scope}`.
- Default observe-only policy layer with explicit policy reasoning.
- Working-memory store with 5-minute TTL.
- Local JSON Lines event ledger.
- Initial state and event JSON Schemas.
- Runtime config via `devcd.toml` and `DEVCD_` environment variables.
- CLI commands for config initialization and event submission.
- Git snapshot source for branch and latest-commit events.
- Context feedback and context quality report models and CLI commands.
- Context surfaces (coding-agent, review-agent, debugging-agent, subagent, public-demo) with surface-aware brief generation.
- Agent resurrection and handoff packet models (`AgentResurrectionContext`, `AgentHandoffPacket`).
- `devcd context handoff-demo` command for machine-readable agent-continuity hand-off output.
- `devcd status` and `devcd doctor` operational readiness CLI commands.
- MCP resource `devcd://context/agent-handoff-packet` exposing the agent-continuity packet.
- JSON Schema for the agent handoff packet (`schemas/devcd-agent-handoff-packet.schema.json`).
