---
name: devcd-recovery-fallback
description: Recovery path when continuity packet readiness or tooling is limited.
---

## Progressive Disclosure

### Level 1 - Metadata (Auto-Loaded)
The YAML frontmatter keys `name` and `description` are the discovery signal loaded automatically.

### Level 2 - Full Instructions
The remaining SKILL.md body is the complete skill guidance and is loaded on demand.

### Level 3 - Referenced Supporting Files
- None.

# DevCD Recovery Fallback

## When to invoke
Use this skill when the normal startup-gate sequence cannot complete cleanly:
- devcd agentic action-packet returns ready_for_agent: false
- Shell command execution is unavailable in this environment
- Policy withholds required context and the packet is insufficient
- DevCD is not installed or commands are not on PATH

## Recovery sequence
1. If shell is available but packet is not ready:
   - Run: devcd agentic tasks
   - Pick the first safe Scout Task and start from there.
   - Run: devcd context passport for broader orientation.
2. If shell is unavailable but MCP is configured:
   - Read: devcd://context/action-packet/concise
   - If you need full context: devcd://context/action-packet/detailed
   - Read: devcd://context/policy-summary
   - Proceed from visible goal and next_action.
3. If neither shell nor MCP is available:
   - Ask exactly ONE precise unblock question to the user.
   - Make the question specific: ask for the current goal or the next intended step.
   - Do not ask for a full recap of past work.

## Rules
- Do not invent missing context — state what is unknown explicitly.
- Do not ask for denied raw payloads or withheld context summaries.
- Do not promise automatic capture when shell is unavailable.
- Do not ask multiple questions at once; one focused question unblocks faster.
- If DevCD is not installed, suggest: pip install devcd && devcd setup
