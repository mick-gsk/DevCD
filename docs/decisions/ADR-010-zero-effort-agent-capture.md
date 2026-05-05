---
id: ADR-010
status: proposed
date: 2026-05-05
supersedes: null
---

# Zero-Effort Agent Capture

## Context

DevCD is useful only when the local ledger already contains enough continuity
metadata for the next agent to resume without asking the user to recap. The
acceptable onboarding budget remains installation plus `devcd init`. Any design
that requires the user to run another bookkeeping command, copy chat history,
write events manually, or configure each agent after initialization misses the
product promise.

AI agents already infer the current goal, failed attempts, decisions, blockers,
relevant artifacts, and next action during normal work. DevCD should give those
agents a small, safe local routine for capturing that metadata when shell command
execution is available.

## Decision

Add a top-level `devcd capture` command that writes structured continuity
metadata to the configured local ledger without requiring a running daemon.
`capture` constructs a metadata-only `DevEvent`, evaluates it through the
existing observation policy, evaluates local storage through the existing storage
policy, and persists only when both decisions allow the operation. The persisted
record uses the existing ledger shape with the storage policy decision.

Extend the DevCD-managed block created by `devcd init --agent-ready` with a
DevCD Continuity Capture Routine. The routine tells agents with shell access to
read `devcd context passport` and then opportunistically capture goals, failed
attempts, failures, decisions, blockers, next actions, and artifact references
as metadata. It also states that agents without shell access should only read
DevCD and must not claim automatic capture.

The model for captured metadata includes provenance and confidence. Each capture
records `basis` and `confidence`, defaulting to `agent_inference` and `inferred`,
plus the agent name, session id, optional fingerprint, and optional artifact or
next action when provided.

## Non-Goals

- Do not add a plugin architecture, skill registry, marketplace, remote skill
  loader, or write-capable MCP tool.
- Do not mutate global or external agent configuration.
- Do not require the DevCD daemon for capture.
- Do not capture raw file contents, raw logs, full chat text, secrets, or remote
  context.
- Do not change MCP from read-only resources.
- Do not make demo fixtures part of the capture or agent-ready success path.

## Consequences

The user-facing flow stays small: after installation and `devcd init`, compatible
agents learn from workspace instructions how to maintain DevCD continuity during
ordinary work. Users do not need to perform DevCD bookkeeping.

The CLI layer owns the first implementation because no second slice needs a new
domain service yet. The implementation still respects existing slice boundaries
by using `DevEvent`, `EventLedger`, `PolicyEngine`, `StateEngine`, and
`DevCDSettings` instead of creating a parallel writer.

The safety boundary is intentionally strict. `capture` accepts only a small enum
of continuity kinds, rejects empty or overly long summaries, rejects obvious
full-text or log-dump input, rejects sensitive payload keys, uses metadata as the
only data class, and performs no remote calls.

## Validation

Implementation must be covered by CLI tests that verify:

- `devcd capture --kind goal --summary ...` writes an allowed local ledger event.
- failure capture plus next action feeds a useful live Agent Passport.
- capture works without a running daemon.
- invalid kinds, full-text-like input, sensitive keys, and policy denial prevent
  persistence.
- `devcd init --agent-ready` embeds the capture routine while preserving existing
  user-authored agent instructions through the managed block.
- demo fixtures and external runtime config mutation are absent from the capture
  and agent-ready success path.

Run:

```bash
python -m pytest tests/test_cli.py -q
python -m pytest tests/test_ambient_context.py -q
python -m ruff check packages tests
python -m mkdocs build --strict
make check
```