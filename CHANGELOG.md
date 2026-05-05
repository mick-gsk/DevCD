# Changelog

All notable changes to DevCD will be documented in this file.

The project follows Conventional Commits and Semantic Versioning once public releases begin.

## 0.1.0 - Unreleased

Short version: Initial local-first context daemon foundation with context quality scoring, control-plane report, research-session recipe, live Agent Passport, and MCP integration snippets.

### Added

- Research-session event recipe (`devcd recipe research-session`) with policy-gated source, note, and full-text events.
- Context quality scoring: deterministic local score, category counts, risk notes, and suggested next actions on `ContextQualityReport`.
- Context control-plane report model (`ContextControlReport`) with visible/withheld sources, memory counts, continuity preview, and quality summary.
- `GET /context/control-plane` API endpoint exposing the control-plane report.
- `devcd context passport` CLI command to generate a live policy-filtered Agent Passport from the local ledger.
- `devcd context control` CLI command to display the control-plane report (`--json` supported).
- `devcd onboard` first-run wrapper that creates local config, prepares selected agent instruction files, and prints the Agent Passport path without starting a daemon or mutating external config.
- `devcd integrations openclaw` and `devcd integrations hermes` CLI commands with copyable local MCP config snippets and optional `--smoke-test` shape check.
- Release readiness documentation and `make distribution` verification for wheel metadata, typed package marker, and installed CLI smoke tests.
- Container sandbox Dockerfile with CI build and CLI smoke-test workflow.
- Context Packs documentation and examples describing DevCD's metadata-only extension surface.
- Manual PyPI Trusted Publishing workflow and publishing guide for verified release artifacts.
- Context Pack and Event Recipe issue templates plus slice labeler updates for current package layout.
- `make smoke` target for a daemonless local CLI sanity check.
- OpenClaw integration guide that separates verified local MCP behavior from unclaimed gateway E2E status.
- Product-led README rewrite with OpenClaw-style first screen, status table, quickstart, trust defaults, and docs-by-goal navigation.
- DevCD Continuity OS brand system with mark, wordmark, viral social-card/avatar artwork, design tokens, README/MkDocs wiring, and usage guidance.
- Default `devcd.toml` configuration file committed to the repository root.
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
