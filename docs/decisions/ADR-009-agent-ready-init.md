---
id: ADR-009
status: proposed
date: 2026-05-05
supersedes: null
---

# Agent-Ready Init

## Context

DevCD's core product problem is not that users need another context command. The
common frustration is that every new AI agent starts cold, asks for the same
recap, and can repeat failed attempts from a previous session.

The acceptable first-run effort is intentionally small: install DevCD, then use
an interactive terminal setup with choices. Any solution that requires users to
learn new product concepts, copy multiple snippets by hand, or configure every
agent separately is too much friction for the product promise.

AI agents already look for workspace-level instruction files. Those files are
the lowest-friction activation surface because they meet the agent where it
already starts: inside the user's project.

## Decision

`devcd init` remains the single first-run entry point. In addition to writing
`devcd.toml`, it may prepare the current workspace for selected agent runtimes
by writing or updating agent-native instruction files:

- Copilot: `.github/copilot-instructions.md`
- Claude: `CLAUDE.md`
- Codex and compatible coding agents: `AGENTS.md`
- OpenClaw: a local read-only MCP config snippet under `.devcd/`

The setup must be local, explicit, and inspectable. It must not make remote
calls, start background daemons, install external tools, or silently mutate
external agent configuration. Existing files must be preserved; DevCD may only
add or replace a clearly marked managed block.

The generated instructions tell agents to consult DevCD's local Agent Passport
or read-only MCP continuity resource before asking the user for a recap. They
also instruct agents to respect withheld-context summaries and policy decisions.

Non-interactive `devcd init` continues to work for automation. Interactive
choices and explicit CLI options are allowed for users who want the agent-ready
workspace setup during initialization.

## Non-Goals

- Do not add a separate activation command as the primary onboarding path.
- Do not mutate Copilot, Claude, Codex, or OpenClaw global configuration without
  a later explicit ADR and opt-in flow.
- Do not require the daemon to be running before a workspace can become
  agent-ready.
- Do not expose write-capable MCP tools or prompts.
- Do not claim that every runtime can consume the same integration depth.

## Consequences

The user-facing promise becomes simpler: after installation, `devcd init` can
make the workspace agent-ready through terminal choices. The next agent sees a
standard instruction file and learns to ask DevCD for local continuity before it
asks the user to recap.

This keeps DevCD's first-run experience within the accepted friction budget while
preserving local-first defaults. It also avoids coupling DevCD to one gateway
runtime or copying OpenClaw's broader agent-router architecture.

The implementation should stay in the CLI layer at first and reuse existing
context, passport, MCP, and policy surfaces. If agent-ready setup later grows
into deeper per-runtime installers, that should be decided separately.

## Validation

Implementation must be covered by CLI tests that verify:

- `devcd init` can create agent-ready workspace files when explicitly requested.
- existing instruction files are preserved and updated only through a managed
  DevCD block.
- unknown agent choices fail clearly.
- generated guidance is live-first and does not reference demo fixtures as the
  success path.
- external runtime configuration is not silently mutated.

Run:

```bash
pytest tests/test_cli.py -q
make check
```
