# Superpower: Agent Resurrection

## Problem

A coding agent loses its chat window. A new session starts. The next agent must:

- rediscover what the goal was
- find the latest failure
- know what was already tried and failed
- not repeat the stale fix

Without DevCD, this requires the user to re-paste context or the agent to
rediscover it from the repository — if the information exists anywhere at all.

## DevCD Capability

DevCD derives a policy-filtered continuity handoff from locally recorded events.
For the shortest proof, that starts as an Action Packet; the broader handoff and
passport layers remain available when an agent needs more context than the first
warm-start surface.

The packet is produced from the local event ledger with no remote call and no
model inference.

It includes:

| Field | What it tells the next agent |
|---|---|
| `active_goal` | What the work is aimed at |
| `last_failure` | The most recent visible failure |
| `last_attempted_fix` | What was tried before this session ended |
| `why_attempt_failed` | Why the last fix did not resolve the blocker |
| `do_not_repeat` | Explicit list of stale or failed strategies |
| `suggested_next_action` | Concrete next step derived from visible events |
| `withheld_context` | Policy-safe summaries for signals that were denied |

The next agent starts from this packet instead of from zero.

## Demo Command

Run the shortest resurrection-style proof against the checked-in fixture:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl --json
```

Run the broader compatibility handoff demo against the resurrection fixture:

```bash
devcd context handoff-demo --events examples/agent-resurrection/sample-events.jsonl
devcd context handoff-demo --events examples/agent-resurrection/sample-events.jsonl --json
```

For daily use, generate the live policy-filtered Agent Passport from the configured
local ledger without passing a fixture file:

```bash
devcd context passport
devcd context passport --json --surface coding-agent --pack developer
```

If the ledger is empty, the passport still renders safely and includes concrete
next commands for recording a goal or converting a local pytest failure report.

The expected handoff packet is checked in at
`examples/agent-resurrection/handoff-packet.md`. The expected machine-readable
packet is checked in at `examples/agent-resurrection/handoff-packet.json` and
documented by `schemas/devcd-agent-handoff-packet.schema.json`.

**Before/after comparison** — shows what a fresh agent knows without DevCD versus
with a policy-filtered handoff:

```bash
# With DevCD
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
```

Read `examples/before-after-agent-continuity/without-devcd.md` for the baseline.

**Agent-switch demo** — coding agent and review agent receive surface-specific
views from the same local events:

```bash
devcd context handoff-demo --events examples/agent-switch/sample-events.jsonl --surface coding-agent
devcd context handoff-demo --events examples/agent-switch/sample-events.jsonl --surface review-agent
```

## Handoff Packet Structure

The broader compatibility packet is rendered as Markdown by the CLI. The
resurrection section looks like:

```text
## Last attempt
- failure: make check still fails: do_not_repeat is absent (task/test_failure)

## Last failure
- make check still fails: do_not_repeat is absent

## Last attempted fix
- Added only a Last failure section to the markdown renderer

## why_attempt_failed
- The latest failure happened after the attempted fix, so the fix did not resolve
  the blocker: make check still fails: do_not_repeat is absent

## do_not_repeat
- Do not repeat the last attempted fix unchanged: Added only a Last failure
  section to the markdown renderer

## Suggested next action
- Add a first-class resurrection context before rendering
```

The packet is produced by `_resurrection_context()` in
`packages/devcd-core/src/devcd/slices/ambient_context/service.py`.

MCP clients can read continuity data through two read-only stdio resources:

- `devcd://context/continuity-packet` — domain-neutral Continuity Packet
  (developer pack by default; includes intent, artifacts, attempts, blockers,
  do_not_repeat, suggested_next_steps, withheld-context metadata)
- `devcd://context/agent-handoff-packet` — legacy developer handoff JSON contract
  (kept for backward compatibility with existing integrations)

To create local events from a concrete pytest failure report before generating a
handoff, use:

```bash
devcd recipe pytest-failure --input examples/event-source-recipes/pytest-failure/input.json
```

## Policy-Safe Withholding

Sensitive signals — note content, test output payloads, browser URLs — are denied
by the default policy. They appear in the packet as `withheld_context` entries.
No payload content is exposed.

Example withheld entry in the output:

```text
## withheld_context
- category: sensitivity
  policy_reason: sensitive events are denied by the default local policy
  safe_summary: notes note_update signal was withheld; only source/type metadata
    is visible as a safe replacement.
- category: payload_content
  policy_reason: metadata-only policy denied full-text payload content
```

The next agent knows that something was withheld and why — without seeing the
content. This is the default local policy. It is not configurable away without
explicit changes to `devcd.toml`.

## Boundary

DevCD is **not an agent**. It does not fix code, make decisions, run tasks, or
call external services. It records what happened locally, applies policy, and
returns a structured packet.

What the next agent does with the packet is up to the agent. DevCD gives it a
verified local starting point.

## Related

- `examples/agent-resurrection/` — resurrection fixture and expected handoff packet
- `examples/before-after-agent-continuity/` — before/after demo with without-devcd baseline
- `examples/agent-switch/` — surface-specific handoff for coding vs. review agents
- `docs/devcd/policy.md` — policy defaults and withheld-context behaviour
- `docs/decisions/ADR-002-agent-context-brief-handoff.md` — decision record for handoff design
