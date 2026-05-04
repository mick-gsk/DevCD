# Agent Handoff Demo

This demo proves the core DevCD handoff loop: replay local work-context events,
apply the default local-first policy, and generate a Markdown brief a coding
agent can use without another user explanation.

It does not start a remote service, export telemetry, or perform actions. The
CLI command reads the JSONL events, runs the existing policy, memory, and state
services in process, and prints a read-only context brief.

## Run

From the repository root:

```bash
python -m pip install -e ".[dev]"
devcd context handoff-demo --events examples/agent-handoff/sample-events.jsonl
```

PowerShell:

```powershell
python -m pip install -e ".[dev]"
devcd context handoff-demo --events examples/agent-handoff/sample-events.jsonl
```

The expected output is checked in as `context-brief.md`.

## What The Events Represent

- `goal_update`: the current developer goal.
- `file_focus`: the active implementation file.
- `branch_change` and `commit`: local Git context.
- `test_failure`: the last failed attempt and current blocker.
- `note_update` with `sensitivity=sensitive`: a sensitive signal denied by policy.
- `url_focus` from `browser`: a disabled source denied by policy.

## Agent Handoff

A coding agent can read the generated brief and continue from:

- `active_goal`: what the user is trying to finish.
- `relevant_artifacts`: where the work is happening.
- `git_context`: branch and latest commit metadata.
- `recent_attempts`: what was tried most recently.
- `blockers`: why progress stopped.
- `suggested_next_steps`: policy-safe next action candidates.
- `withheld_context`: which context was withheld, why, and what safe metadata
  remains visible.
- `agent_limitations`: what the agent does not know or cannot see under policy.
- `policy_decision`: the local export decision for this brief.

## Rebuild The Checked-In Brief

```bash
devcd context handoff-demo --events examples/agent-handoff/sample-events.jsonl
```

The command should match the structure in `context-brief.md`. Timestamp fields
are intentionally omitted from the rendered Markdown so the demo is stable.