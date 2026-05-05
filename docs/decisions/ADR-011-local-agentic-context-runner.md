---
id: ADR-011
status: proposed
date: 2026-05-05
supersedes: null
---

# Local Agentic Context Runner

## Context

DevCD's current continuity path is intentionally local-first and mostly passive.
It records typed metadata, derives work state, renders a Continuity Packet or
Agent Passport, and teaches compatible agents to read or capture context without
asking the user to recap. This reduces repeated explanation, but it still leaves
one important gap: when useful context is missing, DevCD does not actively ask a
local agent to gather it.

The product direction is not to build a larger deterministic parser for every
source and not to become a full autonomous task runner. The stronger direction is
to let local agent runners perform bounded context scouting, then turn their
structured results into the next agent's starting state. The output should be an
actionable packet for the next agent run, not a dashboard that merely displays
raw context.

Starting local agent processes changes DevCD's trust boundary. Process launch is
a state-changing action and must be explainable through policy. Runner output can
contain sensitive content, prompt injection, logs, or file text, so it must be
bounded, validated, and stored only as policy-safe metadata.

## Decision

Add a new vertical slice, `agentic_context`, that owns local scout-runner
lifecycle, scout task contracts, scout report validation, and Action Packet
generation.

The MVP may start configured local agent CLI processes, but only through an
explicit allowlist of runner command templates from local DevCD settings. DevCD
must not accept arbitrary shell strings as runner commands. Each runner start is
evaluated through a new policy decision such as `agentic_runner_start`, and each
accepted report or output summary is evaluated before local storage.

The MVP runner protocol is provider-neutral: DevCD writes a JSON `ScoutTask` to
stdin or to a temporary file under `.devcd/agentic/`, the runner returns a JSON
`ScoutReport`, and DevCD synthesizes an `ActionPacket`. The first implementation
must be testable with a fake local runner and must not require Copilot,
OpenClaw, Hermes, Claude, Codex, or any other external agent runtime to be
installed.

`agentic_context` consumes the existing ambient context service, policy engine,
state engine, memory store, and event ledger. It does not replace
`ambient_context`; it uses continuity data as input and produces the action-ready
layer above it.

## Non-Goals

- Do not make DevCD a general task runner.
- Do not run arbitrary shell commands supplied by an API request or model.
- Do not perform automatic code edits, commits, pull requests, pushes, remote
  exports, or external service calls in the MVP.
- Do not make MCP write-capable or start runners from MCP in the MVP.
- Do not require a specific agent runtime for tests or default behavior.
- Do not persist raw stdout, stderr, file contents, raw logs, private chat text,
  secrets, or full browser/note content.
- Do not make a UI cockpit the primary product surface. The primary output is an
  Action Packet that can prime the next agent run.

## Consequences

DevCD gains an active local context-preparation path while preserving the core
local-first boundary. Users should not need to manually collect context, choose
Scout Tasks, or copy packets between tools. Compatible agents and local runner
templates can do that work on the user's machine.

The settings surface grows to include local runner opt-in, runner allowlists,
timeouts, concurrency limits, and output-size limits. Defaults remain
conservative: runner starts are disabled unless explicitly configured.

The policy layer must distinguish general actions from bounded local scout
runner starts. This keeps the existing observe-by-default and deny-actions-by-
default posture intact while allowing a narrower opt-in path for local context
preparation.

The implementation adds a new API and CLI surface under `agentic-context` or
`devcd agentic`, but runner starts remain local, authenticated, and policy-
explained. MCP remains read-only in the MVP.

## Validation

Implementation must be covered by tests that verify:

- Scout task models require bounded metadata and evidence expectations.
- Action Packets can be derived from existing continuity data without starting a
  runner.
- Runner starts are denied by default.
- Configured runner starts are allowed only through allowlisted command
  templates.
- Arbitrary shell strings are rejected.
- Runner timeout, output byte limit, and failed JSON report handling produce
  safe status objects and no raw output persistence.
- Accepted Scout Reports require evidence and are converted into Action Packet
  fields.
- API routes remain protected by loopback plus local bearer token.
- CLI commands provide JSON and human-readable output without requiring a real
  third-party agent runtime.
- Agent-ready instructions prefer the Action Packet path and do not ask the user
  to perform DevCD bookkeeping.

Run:

```bash
python -m pytest tests/test_agentic_context.py -q
python -m pytest tests/test_api.py -q
python -m pytest tests/test_cli.py -q
python -m ruff check packages tests
make check
python -m mkdocs build --strict
```
