---
name: devcd-handoff-close
description: Close a session with a compact handoff before switching agents.
---

## Progressive Disclosure

### Level 1 - Metadata (Auto-Loaded)
The YAML frontmatter keys `name` and `description` are the discovery signal loaded automatically.

### Level 2 - Full Instructions
The remaining SKILL.md body is the complete skill guidance and is loaded on demand.

### Level 3 - Referenced Supporting Files
- .devcd/templates/devcd-handoff-close.template.md

# DevCD Handoff Close

## When to invoke
Before ending a session, switching to another agent, or when the user signals done.
Also invoke when completing a major milestone and the next step belongs to a new context.

## Step sequence
1. Run: devcd agentic completion-check
   - If it fails: the action packet is not ready or no handoff next_action exists.
   - Resolve by writing a handoff before closing.
2. Run the handoff command (see below).
3. Confirm: 'Handoff written. Continuity is preserved for the next agent or session.'

## Commands
Minimal (no failure):
devcd handoff --goal "<current_goal>" --next-action "<next_action>"

With failure or blocker:
devcd handoff --goal "<current_goal>" --failure "<failure_or_blocker>" --next-action "<next_action>"

## Required fields
- goal: the active goal at session close (not a summary of everything done)
- next_action: the exact next step the succeeding agent should start from
- failure (optional): the most recent blocker or failed attempt, one sentence

## Rules
- Do not claim continuity is complete without running the handoff command.
- Do not omit next_action - it is the primary continuity anchor for the next agent.
- Do not capture raw file content or logs as the failure summary.
- If shell access is unavailable, state explicitly: 'Handoff not written - shell unavailable.'
