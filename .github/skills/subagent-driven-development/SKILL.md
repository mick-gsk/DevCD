---
name: subagent-driven-development
description: "Use when executing implementation plans with independent tasks in the current session. Dispatches fresh subagent per task with two-stage review (spec compliance, then code quality)."
argument-hint: "Provide the path to the implementation plan to execute."
---

## Progressive Disclosure

### Level 1 - Metadata (Auto-Loaded)
The YAML frontmatter keys `name` and `description` are the discovery signal loaded automatically.

### Level 2 - Full Instructions
The remaining SKILL.md body is the complete skill guidance and is loaded on demand.

### Level 3 - Referenced Supporting Files
- None.

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

## When to Use

- You have an implementation plan (from writing-plans skill)
- Tasks are mostly independent
- You want to stay in this session

## The Process

1. **Read plan once** — extract all tasks with full text and context
2. **Create todo list** with all tasks
3. **Per task:**
   - Dispatch implementer subagent with full task text + scene-setting context
   - Answer any questions before letting them proceed
   - Implementer implements, tests, commits, self-reviews
   - Dispatch **spec compliance reviewer** subagent
   - If spec issues found: implementer fixes → re-review
   - Dispatch **code quality reviewer** subagent
   - If quality issues found: implementer fixes → re-review
   - Mark task complete
4. After all tasks: dispatch final code reviewer for entire implementation
5. Run `make check` to confirm everything is green

## Scene-Setting Context

Every implementer subagent dispatch MUST include:

```
Repository: DevCD (local-first Developer Context Daemon)
Language: Python 3.11+, Pydantic v2, FastAPI
Validation: `make check` (lint + typecheck + pytest)
Architecture: Vertical Slice — each feature lives in devcd/slices/<slice>/{models,service,api}.py
Tests: tests/test_<slice>.py, use pytest-asyncio for async
Privacy: mutations denied by default, observation allowed
```

## Model Selection

- **Mechanical tasks** (isolated functions, clear specs, 1-2 files): cheap/fast model
- **Integration tasks** (multi-file, pattern matching, debugging): standard model
- **Architecture/design/review**: most capable model

## Handling Implementer Status

- **DONE:** Proceed to spec compliance review
- **DONE_WITH_CONCERNS:** Read concerns before proceeding. Address correctness/scope concerns first.
- **NEEDS_CONTEXT:** Provide missing context and re-dispatch
- **BLOCKED:** Assess blocker — more context, more capable model, smaller task, or escalate to human

**Never** ignore an escalation or force the same model to retry without changes.

## Spec Compliance Review Prompt

```
Review this implementation against the spec.

Spec requirement: [paste relevant section]
Implementation: [paste code diff or relevant files]

Check:
1. Does the implementation satisfy every requirement in the spec?
2. Are there missing cases or edge conditions?
3. Do types, method signatures, and property names match the spec exactly?

Output: PASS or FAIL with specific issues.
```

## Code Quality Review Prompt

```
Review this implementation for code quality.

Implementation: [paste code diff]
Context: DevCD slice architecture, Pydantic v2, FastAPI, mypy strict mode

Check:
1. Is the logic minimal and clear? No over-engineering?
2. Are there security issues (input validation, injection, etc.)?
3. Is the code idiomatic Python 3.11+ with full type annotations?
4. Does it follow the slice structure (models / service / api)?
5. Does `make check` pass?

Output: PASS or FAIL with specific issues.
```

## Red Flags

**Never:**
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Make subagent read plan file (provide full text instead)
- Skip scene-setting context
- Accept "close enough" on spec compliance
- **Start code quality review before spec compliance is PASS**
- Move to next task while either review has open issues

## Integration

**Required workflow skills:**
- `writing-plans` — Creates the plan this skill executes
- `test-driven-development` — Subagents follow TDD for each task
- `verification-before-completion` — Final gate before claiming work is done
