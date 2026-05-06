# Changelog

All notable changes to DevCD will be documented in this file.

The project follows Conventional Commits and Semantic Versioning once public releases begin.

## 0.2.0 - 2026-05-06

Short version: Initial local-first context daemon foundation with context quality scoring, control-plane report, research-session recipe, live Agent Passport, MCP integration snippets, and daemonless Action Packet demo.

### Added

- CLI polish for first-run flows: root `devcd --version`/`-V`, `devcd smoke --compact`, and richer terminal rendering for `welcome`, `onboard`, and `doctor`.
- `devcd welcome` zero-write first-run guide, Smoke next-step output, and OpenClaw product benchmark notes to make installation and onboarding feel more guided and product-grade.
- `devcd doctor --fix` policy-gated local repair mode with explicit receipts for applied or denied config/profile scaffolding actions.
- Agent-Layer onboarding for `devcd onboard --preview` and `devcd onboard --yes`, including metadata-only workspace detection, persisted `.devcd/agent-layer-profile.json`, Quickstart Agent Layer console, read-only workspace/profile inspectors, and Smoke/Doctor readiness checks.
- Public-consumption docs for release readiness and publishing now distinguish the future PyPI path from checkout installs and point first-time evaluators at a curated examples index plus `devcd smoke` as the install check.
- Context budget and session contract surfaces for Agent Passports, Action Packets, `devcd context budget`, and the read-only `devcd://context/session-contract` MCP resource.
- `ActionPacketBlocker` and `ActionPacketWithheldContext` models on `ActionPacket` for structured blocker and withheld-context surfaces.
- `devcd agentic action-packet-demo --events <file.jsonl>` daemonless CLI command that replays raw DevEvents into an in-memory service and renders the Action Packet contract via `--json` or human-readable markdown.
- `_render_action_packet` helper that renders the full Action Packet (start brief, evidence, blockers, do-not-repeat, withheld context, policy summary) as human-readable markdown.
- `devcd-continuity` agent skill under `skills/devcd-continuity/` for OpenClaw and agent-continuity workflows.
- Agent Landscape documentation (`docs/devcd/agent-landscape.md`) describing the DevCD-in-the-wild ecosystem.

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
