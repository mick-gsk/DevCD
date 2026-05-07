---
name: devcd-continuity
description: Start an OpenClaw coding session from DevCD's local Action Packet before asking the developer to recap.
metadata:
  openclaw:
    requires:
      bins:
        - devcd
---

## Progressive Disclosure

### Level 1 - Metadata (Auto-Loaded)
The YAML frontmatter keys `name` and `description` are the discovery signal loaded automatically.

### Level 2 - Full Instructions
The remaining SKILL.md body is the complete skill guidance and is loaded on demand.

### Level 3 - Referenced Supporting Files
- None.

# DevCD Continuity

Use this when an OpenClaw agent is starting or resuming coding work in a repository where DevCD is configured as an MCP server named `devcd`.

Your job is to create the Turn-0 continuity moment: start from local context, not from a user recap.

## First Move

Before asking the developer to explain the task, read:

1. `devcd://context/action-packet`
2. `devcd://context/policy-summary`

If the Action Packet is ready, begin your first reply with:

- the current goal;
- the next action you will take;
- visible blockers or failed attempts;
- any `do_not_repeat` warnings;
- a short note when context was withheld by policy.

Then ask only for confirmation or correction. Do not ask the developer to re-summarize work that DevCD already provided.

## If The Packet Is Not Ready

If `ready_for_agent` is false or the Action Packet has no goal:

1. Say that DevCD is connected but has no ready continuity packet yet.
2. Read `devcd://context/continuity-packet` for broader context.
3. Ask one precise question that would unblock the next action.

Do not invent missing context.

## Policy Rules

- Treat policy reasons as part of the task context.
- Do not ask for hidden payloads.
- Do not request raw file contents, private notes, secrets, browser history, or full logs when DevCD reports withheld context.
- Do not edit OpenClaw config.
- Do not start, stop, restart, or manage the OpenClaw gateway unless the operator explicitly asks.
- Do not treat DevCD as an executor; DevCD is the local continuity and policy source.
- Do not claim registry availability, endorsement, or live gateway validation unless the operator provides fresh evidence from their environment.

## Expected First Reply Shape

Use compact language. The moment should feel like continuity, not a report.

```text
I picked up DevCD context.
Goal: <current goal>
Next: <next action>
Blocked by: <blocker or none visible>
I will not repeat: <do_not_repeat item or none visible>
Policy note: <withheld summary or none visible>

Proceeding with <next action>. Confirm or redirect.
```

If the user confirms, continue work normally and keep policy boundaries intact.
