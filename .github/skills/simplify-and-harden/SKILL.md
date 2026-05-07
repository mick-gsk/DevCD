---
name: simplify-and-harden
description: "Post-completion self-review for coding agents that runs simplify, harden, and micro-documentation passes on non-trivial code changes. Use when: a coding task just completed, the diff touches executable source files with 10+ changed lines or high-impact logic (auth, validation, queries, file paths, network, concurrency). Feeds recurring findings into self-improving-agent via .learnings/LEARNINGS.md."
argument-hint: "Run after completing a coding task. Provide the list of modified files if not auto-detected."
---

## Progressive Disclosure

### Level 1 - Metadata (Auto-Loaded)
The YAML frontmatter keys `name` and `description` are the discovery signal loaded automatically.

### Level 2 - Full Instructions
The remaining SKILL.md body is the complete skill guidance and is loaded on demand.

### Level 3 - Referenced Supporting Files
- None.

# Agent Skill: Simplify & Harden

Post-completion self-review: clean, harden, and document your work before moving on.

## Trigger Conditions

Activate automatically when ALL of the following are true:

1. The agent has completed its primary coding task
2. The diff contains a **non-trivial** code change:
   - Touches at least one executable source file (`*.py`)
   - AND includes either ≥10 changed non-comment/non-whitespace lines OR at least one high-impact logic change (auth/authz, input validation, data access, external commands, file paths, network requests, concurrency)
3. The skill has not already run on this task (no re-entry loops)

**Does NOT activate** when:
- The change is docs-only, config-only, comments-only, formatting-only, generated artifacts only, or tests-only
- The agent failed or was interrupted
- User explicitly skips via `--no-review`

## Scope Constraints

**Hard rule: Only touch code modified in this task.**

- Do NOT refactor adjacent code that was not modified
- Do NOT introduce new dependencies or architectural changes
- Flag out-of-scope concerns in the summary output rather than acting on them

**Budget limits:**
- Maximum additional changes: **20% of the original diff size** (lines changed)
- Maximum execution time: **60 seconds**
- If either limit is hit, stop and output what you have with a `budget_exceeded` flag

## Pass 1: Simplify

**Objective:** Reduce unnecessary complexity introduced during implementation.

**Default posture:** Simplify, don't restructure. Bias heavily toward cosmetic fixes. Refactoring is the exception.

**Fresh-eyes start (mandatory):** Before any edits, re-read all code added or modified with fresh eyes. Actively look for obvious bugs, confusing logic, brittle assumptions, and naming issues.

### Review Checklist

- **Dead code** — debug logs, commented-out attempts, unused imports, temp variables
- **Naming clarity** — function/variable names that made sense mid-implementation but read poorly after
- **Control flow** — nested conditionals that can be flattened, deep nesting replaceable by early returns
- **API surface** — exposed more than necessary? Can public methods become private?
- **Over-abstraction** — classes or wrappers not justified by current scope
- **Consolidation** — logic spread across functions/files when it could live in one place

### Simplify Actions

- **Cosmetic fix** (dead code, unused imports, naming, control flow, visibility reduction) → applied automatically if within budget
- **Refactor** (consolidation, restructuring, abstraction changes) → proposed ONLY when genuinely necessary

**Refactor Stop Hook (mandatory):** Any refactor triggers an interactive prompt:

```
[simplify-and-harden] Refactor proposal:

  What: [description]
  Why: [rationale]
  Files affected: [list]
  Estimated diff: [+/- lines]

  [approve] [reject] [show diff] [skip all refactors]
```

Wait for explicit human approval before applying. Do not batch refactor proposals.

## Pass 2: Harden

**Objective:** Close security and resilience gaps while the agent still understands the code's intent.

Ask: *"If someone malicious saw this code, what would they try?"*

### Review Checklist

- **Input validation** — external inputs validated before use? Type coercion, bounds checks, unconstrained strings?
- **Error handling** — catch blocks specific? Errors logged without leaking sensitive data? Swallowed exceptions?
- **Injection vectors** — SQL injection, XSS, command injection, path traversal, template injection
- **Auth/authz** — new endpoints enforce auth? Permission checks present and correct? Privilege escalation risk?
- **Secrets** — hardcoded API keys, tokens, passwords? Connection strings parameterized? Credentials in logs?
- **Data exposure** — error output leaks internal state, stack traces, DB schemas, or PII?
- **Dependency risk** — new dependencies introduced? Well-maintained, properly versioned, no known CVEs?
- **Race conditions** — shared resources synchronized? TOCTOU vulnerabilities?

For DevCD: policy layer must gate any state-changing operation. Observation allowed, mutations denied by default.

### Harden Actions

- **Patch** (adding validation, escaping output, removing hardcoded secret) → applied automatically if within budget
- **Security refactor** (restructuring auth flow, replacing vulnerable pattern) → ALWAYS requires human approval

Same Refactor Stop Hook applies with added severity and attack vector context.

## Pass 3: Document (Micro-pass)

**Objective:** Capture non-obvious decisions while the agent still remembers why it made them.

**Rules:**
- For logic requiring >5 seconds of "why does this exist?" thought: add a single-line comment
- For any workaround or hack: add a comment with context and a TODO with removal conditions
- For performance-sensitive choices: note why current approach was chosen over obvious alternative
- **Maximum: 5 comments added per task**

## Self-Improvement Integration

After each run, normalize recurring findings into `.learnings/LEARNINGS.md` when a pattern appears ≥3 times across ≥2 distinct tasks in a 30-day window.

## Core Invariants

- Scope lock — only files modified in the current task
- Budget cap — 20% max additional diff
- Simplify-first posture — cleanup is the default, refactoring is the exception
- Refactor stop hook — structural changes always require human approval
- Three passes — simplify, harden, document (in that order)
- Run `make check` after all passes to verify no regressions
