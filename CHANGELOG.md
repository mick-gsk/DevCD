# Changelog

All notable changes to DevCD will be documented in this file.

The project follows Conventional Commits and Semantic Versioning once public releases begin.

## 0.2.1 - 2026-05-07

Short version: Action Packet now projects verification-ready session contracts, rejected dead-end paths, and additive vision-alignment signals for completion/compliance. New workflow_layer slice adds resumable YAML workflow runner, trust-bounded catalog stack, and layered instruction resolver.

### Added

- New `workflow_layer` slice: resumable YAML workflow runner with human-gate pause/resume, `WorkflowEngine` persisting run state under `.devcd/workflows/runs/`, and `CommandStep`/`ShellStep`/`GateStep` step types.
- `WorkflowCatalog` with trust-bounded resolution stack (builtin → user → project → env); env-supplied URLs validated for HTTPS/localhost; `CatalogTrustError` on invalid sources.
- `InstructionLayerResolver` composing agent instruction content from managed-core, team-preset (`.devcd/presets/<target>-*.md`), and workspace-override (`.devcd/instructions/<target>.md`) layers with replace/wrap strategies.
- `_write_agent_instruction` now routes through `InstructionLayerResolver` so workspace overrides and team presets are automatically composed on top of the managed DevCD block.
- New `devcd workflow` CLI sub-group with `run`, `status`, `resume`, and `info` commands.
- Workflow command steps now support in-process CLI execution via an injected command runner, reducing reliance on external `devcd` subprocess lookup.
- New read-only HTTP API surface for workflow catalog discovery and resolution: `GET /workflow/catalog` and `GET /workflow/catalog/{name}`.
- Continuity hook capture points added around key orchestration commands: before/after `setup`, before/after `agentic action-packet`, and before/after `handoff`.
- Three new `PolicyEngine` decision methods: `decide_workflow_step_execute`, `decide_catalog_install`, `decide_instruction_layer_write`.
- ADR-019: architecture decision record for workflow orchestration, catalog trust stack, and layered instruction resolver.
- Action Packet additive fields: `rejected_paths` and a dedicated `session_contract` shape (`next_action`, `done_when`, `verification_required`, `withheld_count`).
- Local CLI and MCP Action Packet builders now inject configured workspace vision consistently, and `devcd agentic completion-check` / `devcd agentic compliance` add a policy-safe vision alignment note with warnings on clear drift.
- Action Packet projection now derives `done_when` from `event_class="goal.done_when"` and sets verification requirements when completion criteria are missing.
- Read-only MCP `devcd://context/session-contract` now exposes the Action Packet session contract contract with matching context budget metadata.
- New `event_class` support on `DevEvent` with validated `dead_end` and `goal.done_when` payload contracts.
- `dead_end` continuity curation support for developer-triggered non-retriable approach tracking (`approach_summary`, `reason`, `related_goal`).

## 0.2.0 - 2026-05-06

Short version: Initial local-first context daemon foundation with context quality scoring, control-plane report, research-session recipe, live Agent Passport, MCP integration snippets, and daemonless Action Packet demo.

### Added

- Faster local development gate: `make check-dev` now uses `dmypy` and affected-test execution via `pytest-testmon` (with automatic fallback), plus `make test-fast-parallel` for optional `pytest-xdist` parallel runs.
- New `devcd setup` install-time wizard for interactive multi-project configuration, manual agent-target selection, and automatic initial handoff seeding so `devcd agentic action-packet` is usable immediately after first setup.
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
