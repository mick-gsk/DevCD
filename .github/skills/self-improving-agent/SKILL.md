---
name: self-improving-agent
description: "Log learnings, errors, and corrections to .learnings/ for continuous improvement. Use when: (1) A command or operation fails unexpectedly, (2) User corrects the agent, (3) A knowledge gap is identified, (4) A better approach is found. Captures corrections, insights, errors, and feature requests; promotes broadly applicable learnings to project memory files."
argument-hint: "Describe what happened: error, correction, knowledge gap, or feature request."
---

# Self-Improvement Skill

Log learnings and errors to markdown files for continuous improvement. Important learnings get promoted to project memory files.

## First-Use Initialisation

Before logging anything, ensure the `.learnings/` directory and files exist:

```bash
mkdir -p .learnings
# Create LEARNINGS.md if missing
# Create ERRORS.md if missing
# Create FEATURE_REQUESTS.md if missing
```

Never overwrite existing files. Do not log secrets, tokens, private keys, or full config files.

## Quick Reference

| Situation | Action |
|---|---|
| Command/operation fails | Log to `.learnings/ERRORS.md` |
| User corrects you | Log to `.learnings/LEARNINGS.md` with category `correction` |
| User wants missing feature | Log to `.learnings/FEATURE_REQUESTS.md` |
| API/external tool fails | Log to `.learnings/ERRORS.md` with integration details |
| Knowledge was outdated | Log to `.learnings/LEARNINGS.md` with category `knowledge_gap` |
| Found better approach | Log to `.learnings/LEARNINGS.md` with category `best_practice` |
| Simplify/Harden recurring patterns | Log/update `.learnings/LEARNINGS.md` with `Source: simplify-and-harden` |
| Broadly applicable learning | Promote to `AGENTS.md` and/or `.github/copilot-instructions.md` |

## Logging Format

### Learning Entry

Append to `.learnings/LEARNINGS.md`:

```
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: api | service | policy | memory | events | kernel | tests | docs | config

### Summary
One-line description of what was learned

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement to make

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- See Also: LRN-20250110-001 (if related to existing entry)
- Pattern-Key: simplify.dead_code | harden.input_validation (optional)
- Recurrence-Count: 1 (optional)

---
```

### Error Entry

Append to `.learnings/ERRORS.md`:

```
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: high
**Status**: pending
**Area**: api | service | policy | memory | events | kernel | tests | docs | config

### Summary
Brief description of what failed

### Error
Actual error message or output

### Context
- Command/operation attempted
- Input or parameters used
- Environment details if relevant

### Suggested Fix
If identifiable, what might resolve this

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file.ext
- See Also: ERR-20250110-001 (if recurring)

---
```

### Feature Request Entry

Append to `.learnings/FEATURE_REQUESTS.md`:

```
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601 timestamp
**Priority**: medium
**Status**: pending
**Area**: api | service | policy | memory | events | kernel | tests | docs | config

### Requested Capability
What the user wanted to do

### User Context
Why they needed it, what problem they're solving

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
How this could be built, what slice it might extend

### Metadata
- Frequency: first_time | recurring
- Related Features: existing_feature_name

---
```

## ID Generation

Format: `TYPE-YYYYMMDD-XXX`

- TYPE: `LRN` (learning), `ERR` (error), `FEAT` (feature)
- YYYYMMDD: Current date
- XXX: Sequential number or random 3 chars (e.g., `001`, `A7B`)

## Resolving Entries

When an issue is fixed, update the entry:

- Change `**Status**: pending` → `**Status**: resolved`
- Add resolution block:

```
### Resolution
- **Resolved**: 2025-01-16T09:00:00Z
- **Commit**: abc123
- **Notes**: Brief description of what was done
```

## Promoting to Project Memory

When a learning is broadly applicable (not a one-off fix), promote it to permanent project memory.

### When to Promote

- Learning applies across multiple files/features
- Knowledge any contributor (human or AI) should know
- Prevents recurring mistakes
- Documents project-specific conventions

### Promotion Targets

| Target | Use for |
|---|---|
| `AGENTS.md` | Agent-specific workflows, tool usage patterns, automation rules |
| `.github/copilot-instructions.md` | Project context and conventions for GitHub Copilot |

### How to Promote

1. Distill the learning into a concise rule or fact
2. Add to appropriate section in target file
3. Update original entry: Change `**Status**: pending` → `**Status**: promoted` and add `**Promoted**: <target file>`

## Recurring Pattern Detection

If logging something similar to an existing entry:

- Search first: `grep -r "keyword" .learnings/`
- Link entries: Add `**See Also**: ERR-20250110-001` in Metadata
- Bump priority if issue keeps recurring
- Consider systemic fix: Recurring issues often indicate missing documentation (→ promote to `AGENTS.md`)

## Detection Triggers

Automatically log when you notice:

**Corrections** (→ learning with `correction` category):
- "No, that's not right..."
- "Actually, it should be..."
- "That's outdated..."

**Feature Requests** (→ feature request):
- "Can you also..."
- "I wish you could..."

**Knowledge Gaps** (→ learning with `knowledge_gap` category):
- User provides information you didn't know
- Documentation you referenced is outdated

**Errors** (→ error entry):
- Command returns non-zero exit code
- Exception or stack trace
- Unexpected output or behavior

## Best Practices

- Log immediately — context is freshest right after the issue
- Be specific — future agents need to understand quickly
- Include reproduction steps — especially for errors
- Suggest concrete fixes — not just "investigate"
- Promote aggressively — if in doubt, add to `.github/copilot-instructions.md`
