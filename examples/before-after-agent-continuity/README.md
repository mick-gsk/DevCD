# Before/After Agent Continuity Demo

This is a proof demo for DevCD's continuity value. It does not claim that DevCD
is a model, a task runner, or a code fixer. It shows the difference between a
new agent starting with no handoff context and a new agent receiving a
policy-filtered handoff packet generated from local events.

The demo uses a checked-in JSONL fixture and the real DevCD CLI command:

```bash
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
```

PowerShell:

```powershell
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
```

The full expected output is checked in as `with-devcd.md`.

## Run In Under Five Minutes

From the repository root:

```bash
python -m pip install -e ".[dev]"
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
```

PowerShell:

```powershell
python -m pip install -e ".[dev]"
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
```

Optional PowerShell comparison against the checked-in expected output:

```powershell
$actual = (devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl | Out-String).TrimEnd() -replace "`r`n", "`n"
$expected = (Get-Content examples/before-after-agent-continuity/with-devcd.md -Raw).TrimEnd() -replace "`r`n", "`n"
$actual -eq $expected
```

Expected result: `True`.

## Before

Read `without-devcd.md` for the baseline. Without DevCD, a new agent does not
know the goal, the latest failure, the stale prior attempt, or the next action
unless the user repeats that context or the agent rediscovers it manually.

## After

With DevCD, the same fixture produces a handoff packet with these fields:

```text
## active_goal
Finish the before/after continuity proof demo for DevCD

## Last failure
- make check still fails: expected CLI output is stale and omits do_not_repeat

## do_not_repeat
- Do not repeat the last attempted fix unchanged: Added a generic handoff paragraph but did not regenerate the CLI output from the fixture

## Suggested next action
- Regenerate with-devcd.md from sample-events.jsonl and verify withheld_context is present

## context_quality_notes
- No context feedback recorded.

## withheld_context
- category: sensitivity
  policy_reason: sensitive events are denied by the default local policy
- category: source
  policy_reason: source is not enabled by policy
```

That output is generated from `sample-events.jsonl`, not from a mocked LLM
answer.

## What The Events Represent

- `goal_update`: the active work goal.
- `file_focus`: the files the developer was working on.
- `branch_change`: local Git context.
- `test_failure`: the visible blocker and latest failure.
- `fix_attempt`: a prior attempt that should not be repeated unchanged.
- sensitive `note_update`: a sensitive signal withheld by policy.
- `browser` `url_focus`: a disabled source withheld by policy.

## Boundaries

- No real LLM output is fabricated.
- DevCD does not claim to fix code.
- Sensitive data remains withheld; the output contains only safe summaries and
  policy reasons.
- The documented command uses the existing `devcd context handoff-demo` CLI.