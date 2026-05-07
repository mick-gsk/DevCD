<p align="center">
  <img src="docs/assets/devcd-wordmark.svg" alt="DevCD" width="520">
</p>

<p align="center">
  <strong>Stop re-explaining your work to every new AI agent session.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/devcd/"><img src="https://img.shields.io/pypi/v/devcd?style=for-the-badge" alt="PyPI version"></a>
  <a href="https://github.com/mick-gsk/DevCD/actions/workflows/ci.yml?branch=main"><img src="https://img.shields.io/github/actions/workflow/status/mick-gsk/DevCD/ci.yml?branch=main&style=for-the-badge" alt="CI status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="docs/devcd/release-readiness.md"><img src="https://img.shields.io/badge/status-pre--alpha-orange?style=for-the-badge" alt="Pre-alpha"></a>
  <a href="docs/devcd/openclaw-integration.md"><img src="https://img.shields.io/badge/MCP-read--only-informational?style=for-the-badge" alt="Read-only MCP"></a>
  <a href="https://github.com/sponsors/mick-gsk"><img src="https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?style=for-the-badge" alt="GitHub Sponsors"></a>
</p>

**DevCD** is a local continuity layer for mixed AI-agent setups. It gives a
fresh Copilot, Claude, Codex, OpenClaw, or MCP-capable session a
policy-filtered **Action Packet** before it asks you to recap the task.

That packet gives the next agent the current goal, latest failure or blocker,
do-not-repeat guidance, one suggested next action, and a clear note when
context was withheld by policy. DevCD is the warm-start layer for your agent
stack, not another agent runtime to manage.

It is not a model, chat app, remote service, or task runner. DevCD is the local
state and policy layer between your workspace and the agents that help you.

[Getting Started](docs/getting-started.md) | [Examples](examples/README.md) | [Agent Resurrection](docs/superpowers/agent-resurrection.md) | [OpenClaw Integration](docs/devcd/openclaw-integration.md) | [Real-World Testing Playbook](docs/devcd/reality-testing.md) | [Context Packs](docs/devcd/context-packs.md) | [Security](SECURITY.md) | [Release Readiness](docs/devcd/release-readiness.md) | [Publishing](docs/devcd/publishing.md) | [Brand System](docs/devcd/brand-system.md) | [Architecture](docs/devcd/architecture.md) | [Contributing](CONTRIBUTING.md)

## Status

DevCD is **pre-alpha**. The core local continuity loop is implemented and tested.

| Surface | Status |
| --- | --- |
| PyPI install (`pip install devcd`) | Working |
| `devcd setup` first-run path | Working |
| Agent Passport / Continuity Packet | Working |
| Action Packet for the next agent | Working |
| Read-only MCP resources | Working |
| OpenClaw MCP shape check | Working on the DevCD side |
| Context Packs | Developer and research packs built in |
| PyPI release | Published — `devcd 0.2.1` |
| Hosted/cloud mode | Not planned for alpha |

See [Release Readiness](docs/devcd/release-readiness.md) for the full alpha bar.

## Quick Start

For first-time users, this is the recommended path.

1. Install DevCD:

```bash
python -m pip install --disable-pip-version-check --quiet devcd
```

2. Initialize your workspace with defaults:

```bash
devcd setup --yes
```

3. Open the next-agent handoff packet:

```bash
devcd agentic action-packet
```

4. Optional: run a quick health check:

```bash
devcd smoke
```

5. Optional: enable shell completion:

```bash
devcd autocomplete
devcd --install-completion
```

Use `devcd setup` without `--yes` if you want an interactive setup wizard.

### Cross-Platform Notes

- The Quick Start commands are shell-agnostic and work in PowerShell, Bash, and Zsh.
- Commands are written one-per-line (no shell-specific chaining), so they are safe to copy on Windows, macOS, and Linux.
- For automation, prefer commands with `--json` where available.

### Expected Output Formats

Use these commands when you need machine-readable output:

```bash
devcd setup --yes --json
devcd context packs --json
devcd agentic action-packet --json
```

The `--json` variants are valid JSON objects/arrays and intended for scripts and CI.
`devcd smoke` is a human-readable diagnostic command and should not be parsed as
a strict machine format.

### Optional Local Demo

If you want to see the handoff behavior before using your own workspace:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl
```

### Common First-Week Commands

```bash
devcd handoff --goal "Ship the failing release gate" --failure "make check failed on policy tests" --rationale "Policy assertion structure changed" --next-action "Inspect the failing policy assertion"
devcd autocomplete
devcd quickstart
devcd context passport
devcd context control
devcd run
```

Use `devcd handoff` when ending a session or switching agents. Use `devcd run`
only when you need live API event ingestion.

### Alternative Installers

```bash
pipx install devcd
uvx devcd smoke
```

### From Source (Contributors)

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
```

## What The Next Agent Gets

An agent that reads DevCD before asking you to recap can see policy-filtered
continuity like this:

```text
Goal: Ship the failing release gate
Latest failure: make check failed on policy tests
Do not repeat: rerunning the same patch without checking the policy assertion
Suggested next action: inspect the failing policy assertion
Withheld context: raw logs or sensitive notes were not included by policy
```

That packet is derived from local structured events and metadata. It is not
model memory, not telemetry, and not remote sync.

## Why DevCD Exists

Every AI coding tool starts cold unless you manually rebuild context. That means
lost time, repeated failed attempts, accidental stale fixes, and unnecessary
copy/paste of sensitive context.

DevCD gives agents a local, typed, policy-filtered continuity layer:

- **Agent resurrection** - new sessions can continue from the previous goal,
  failure, stale attempts, blockers, and next action.
- **Warm-start handoff** - the next agent gets a concrete starting point before
  it asks for a recap.
- **Local-first context** - data stays on your machine unless a future explicit
  policy says otherwise.
- **Policy visibility** - every observation, storage decision, export, or action
  has an explainable policy reason.
- **Structured continuity instead of pasted recap** - captures are designed for
  compact metadata, not raw logs, transcripts, file contents, or secrets.
- **Runtime-neutral consumption** - CLI, localhost API, and read-only MCP expose
  the same policy-filtered state to different agent surfaces.

## Highlights

- `devcd setup` - install-time wizard for multi-project config, manual
  agent-target selection, initial handoff seeding, and immediate Action Packet
  readiness.
- `devcd onboard` - single-workspace guided wrapper for config, selected agent
  instruction files, and staged setup output.
- `devcd handoff` - one-command goal, failure, and next-action capture before
  switching to a fresh agent.
- `devcd capture` - daemonless, policy-gated continuity metadata capture.
- `devcd agentic action-packet` - next-action packet for the next local agent.
- `devcd quickstart` - interactive activation report that expands on the same
  Action Packet workflow after onboarding, including an Agent Layer console.
- `devcd context workspace-analysis` and `devcd context profile` - read-only
  inspectors for the detected workspace layer and persisted profile.
- `devcd context passport` - broader live continuity view from the configured
  local ledger.
- `devcd context control` - visibility report for included and withheld context.
- `devcd doctor --fix` - policy-gated local repairs for missing config/profile scaffolding.
- `devcd mcp serve` - read-only local MCP stdio resources.
- `devcd integrations openclaw --smoke-test` - verifies the local MCP shape
  without installing OpenClaw or mutating its config.
- `devcd recipe research-session` - local recipe that proves non-developer
  continuity through the research Context Pack.
- `make distribution` - builds and verifies wheel/sdist artifacts and installed
  CLI behavior.
- `make smoke` - quick daemonless confidence check for evaluators.

## Local Agent Skills

This repo also carries local agent skills for repeatable engineering workflows
under `.github/skills/`.

- `agent-ops-observability` - diagnose instruction drift, weak handoffs, tool
  misuse, and missing verification in agent-driven work.
- `devils-advocate` - stress-test plans, ADRs, policy changes, and rollout
  ideas before implementation.
- `deep-interview`, `brainstorming`, `systematic-debugging`, and
  `verification-before-completion` cover clarification, design, debugging, and
  evidence discipline.

These are repository workflow assets, not DevCD product features. They exist to
make agent work in this repo more reliable and reviewable.

## Security Defaults

DevCD is built around local-first privacy boundaries.

- Local storage and loopback API by default.
- No telemetry.
- No remote export by default.
- Observations are policy-gated.
- Actions are denied by default.
- Sensitive or raw-content events are denied or withheld by default.
- MCP exposes read-only resources and no write-capable tools.
- Agent capture should record metadata only, never raw file contents, raw logs,
  full chat transcripts, private notes, credentials, or secrets.

Read [Security](SECURITY.md) before adding any feature that observes, stores,
exports, or acts on local context.

## OpenClaw And MCP

DevCD can be used as a read-only MCP context source for OpenClaw:

```bash
devcd integrations openclaw --smoke-test
```

The smoke test verifies the DevCD MCP server shape locally: initialize,
resources/list, tools/list, and prompts/list. Current expected shape: resources
present, tools empty, prompts empty.

DevCD does **not** claim to be an OpenClaw plugin, ClawHub package, or fully
end-to-end verified OpenClaw gateway integration yet. See
[OpenClaw Integration](docs/devcd/openclaw-integration.md) for the exact claim
boundary and config snippet.

## Context Packs

Context Packs are DevCD's current extension surface. They define which metadata
signals matter for a workflow and how a policy-filtered Continuity Packet should
be rendered for an agent surface.

Built-in packs:

- `developer` - coding-agent continuity across goals, git state, files,
  failures, blockers, and next actions.
- `research` - metadata-only research continuity across reviewed sources,
  hypotheses, decisions, and failed attempts.

List them:

```bash
devcd context packs
devcd context packs --json
```

See [Context Packs](docs/devcd/context-packs.md) and
[Context Pack examples](examples/context-packs/README.md).

## Architecture

```text
IDE / Git / Tasks / Notes / Recipes
          |
          v
    Normalized DevEvents
          |
          v
  +---------------------+      +----------------+
  | DevCD Host          | ---> | Policy Layer   |
  | Event API           |      | allow / deny   |
  | State Engine        |      +----------------+
  | Memory Layer        |
  | Ambient Context     | ---> Agent Passport / Action Packet / MCP resources
  +---------------------+
          |
          v
 local JSONL ledger + local memory store
```

The codebase uses Vertical Slice Architecture. Slice-owned models, API routes,
services, and tests live under `packages/devcd-core/src/devcd/slices/<slice>/`.
Shared infrastructure belongs in `devcd/kernel/` only when multiple slices need
it.

## Trust And Public Signals

DevCD should earn trust by making current maturity visible instead of pretending
to be more finished than it is.

| Signal | Where |
| --- | --- |
| Security policy and threat model | [SECURITY.md](SECURITY.md) |
| Alpha readiness and known limitations | [Release Readiness](docs/devcd/release-readiness.md) |
| Distribution artifact checks | [Publishing](docs/devcd/publishing.md) |
| Container sandbox and CI proof path | [Container Sandbox](docs/devcd/container.md) |
| Brand system and project assets | [Brand System](docs/devcd/brand-system.md) |
| Funding configuration | [GitHub Sponsors](https://github.com/sponsors/mick-gsk) |
| Community contribution path | [Contributing](CONTRIBUTING.md) |

No PyPI, Homebrew, Discord, hosted service, or production-support badge appears
here until that surface actually exists.

## Operator Quick Refs

- First run: `devcd setup`
- Quick health check: `devcd smoke`
- Full local verification: `make check`
- Distribution verification: `make distribution`
- Local daemon: `devcd run`
- Agent Passport: `devcd context passport`
- Action Packet: `devcd agentic action-packet`
- Context control report: `devcd context control`
- OpenClaw snippet and shape check: `devcd integrations openclaw --smoke-test`
- Read-only MCP server: `devcd mcp serve`

## Docs By Goal

- New here: [Getting Started](docs/getting-started.md),
  [Agent Resurrection](docs/superpowers/agent-resurrection.md),
  [Release Readiness](docs/devcd/release-readiness.md)
- Agent runtime integration: [Agent Consumption](docs/devcd/agent-consumption.md),
  [OpenClaw Integration](docs/devcd/openclaw-integration.md)
- Context and privacy: [Security](SECURITY.md), [Policy](docs/devcd/policy.md),
  [Memory](docs/devcd/memory.md), [Context Packs](docs/devcd/context-packs.md)
- Examples: [Context Brief](examples/context-brief/README.md),
  [Agent Resurrection](examples/agent-resurrection/README.md),
  [Research Continuity](examples/research-continuity/README.md),
  [OpenClaw MCP Context](examples/openclaw-mcp-context/README.md)
- Internals: [Architecture](docs/devcd/architecture.md),
  [Decisions](docs/decisions/ADR-001-vertical-slice-architecture.md),
  [Schemas](schemas/)
- Release work: [Publishing](docs/devcd/publishing.md),
  [Container Sandbox](docs/devcd/container.md), [Changelog](CHANGELOG.md)

## Development

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
make smoke
make check
```

Useful targets:

```bash
make smoke         # daemonless CLI sanity check
make check         # ruff + mypy + pytest
make distribution  # build, twine check, wheel content check, installed CLI smoke
make docs          # strict MkDocs build
make run           # run the local daemon
```

If `make` is unavailable in your environment, run the equivalent tools directly:

```bash
python -m ruff check .
python -m mypy packages/devcd-core/src/devcd
python -m pytest
```

## Configuration

`devcd onboard` and `devcd init` create `devcd.toml` with local-first defaults.
The daemon binds to `127.0.0.1:8765` by default, stores runtime data locally, and
uses a local bearer token for protected API routes.

Example shape:

```toml
[devcd]
host = "127.0.0.1"
port = 8765
runtime_dir = ".devcd"
working_memory_ttl_seconds = 300
allowed_data_classes = ["metadata"]
allow_observation = true
allow_local_storage = true
allow_remote_export = false
allow_actions = false
```

## Roadmap

| Milestone | Focus |
| --- | --- |
| `0.1` | Local continuity foundation, Agent Passport, policy layer, read-only MCP |
| Public alpha | PyPI publish, install docs, release notes, OpenClaw E2E verification |
| Next | Native IDE event sources, more recipes, pack authoring guide |
| Later | Policy editor, stable API contracts, broader runtime integrations |

DevCD will stay local-first by default. Remote export, write-capable MCP tools,
hosted deployment, and arbitrary plugin execution are not part of the first
alpha boundary.

## Community

DevCD is maintained by [Mick Gottschalk](https://github.com/mick-gsk). Community
contributions are welcome, especially focused bug reports, reproducible Context
Pack proposals, Event Recipe proposals, and policy-boundary reviews.

See [Contributing](CONTRIBUTING.md), [Security](SECURITY.md),
[Open issues](https://github.com/mick-gsk/DevCD/issues), and
[GitHub Sponsors](https://github.com/sponsors/mick-gsk).
