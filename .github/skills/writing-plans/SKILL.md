---
name: writing-plans
description: "Use when you have a spec or requirements for a multi-step task, before touching code. Creates detailed, bite-sized implementation plans with exact file paths, complete code, and verification steps."
argument-hint: "Provide the spec or describe the feature to plan."
---

## Progressive Disclosure

### Level 1 - Metadata (Auto-Loaded)
The YAML frontmatter keys `name` and `description` are the discovery signal loaded automatically.

### Level 2 - Full Instructions
The remaining SKILL.md body is the complete skill guidance and is loaded on demand.

### Level 3 - Referenced Supporting Files
- None.

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`

## Scope Check

If the spec covers multiple independent subsystems, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## DevCD File Structure

Before defining tasks, map out which files will be created or modified.

For a new slice, the canonical structure is:
```
packages/devcd-core/src/devcd/slices/<slice_name>/
├── __init__.py
├── models.py      # Pydantic v2 models
├── service.py     # Business logic (pure functions where possible)
└── api.py         # FastAPI router

tests/
└── test_<slice_name>.py
```

Shared code belongs in `devcd/kernel/` only when at least two slices need it.

**Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.**

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run `make check` and make sure it passes" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Use subagent-driven-development to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** Python 3.11+, Pydantic v2, FastAPI, pytest + pytest-asyncio

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `packages/devcd-core/src/devcd/slices/<slice>/models.py`
- Modify: `packages/devcd-core/src/devcd/host.py`
- Test: `tests/test_<slice>.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior(client):
    response = client.get("/endpoint")
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_<slice>.py::test_name -v`
Expected: FAIL with "..."

- [ ] **Step 3: Write minimal implementation**

```python
# packages/devcd-core/src/devcd/slices/<slice>/service.py
def function(input: str) -> str:
    return expected
```

- [ ] **Step 4: Run `make check` to verify it passes**

Expected: All checks green

- [ ] **Step 5: Commit**

```bash
git add tests/test_<slice>.py packages/devcd-core/src/devcd/slices/<slice>/
git commit -m "feat(<slice>): add specific feature"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Remember
- Exact file paths always
- Complete code in every step — if a step changes code, show the code
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
- Every state-changing operation must be explainable through a policy decision (DevCD architecture rule)

## Self-Review

After writing the complete plan, check it against the spec:

1. **Spec coverage:** Can you point to a task that implements each requirement?
2. **Placeholder scan:** Search for "TBD", incomplete steps, vague instructions.
3. **Type consistency:** Do types, method signatures, and property names match across tasks?

Fix issues inline. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, offer:

**"Plan complete and saved to `docs/superpowers/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review between tasks

**2. Inline Execution** — execute tasks in this session with checkpoints

**Which approach?"**
