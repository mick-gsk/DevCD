---
name: adr-workflow
description: "Use when a change affects architecture, slice boundaries, API contracts, policy rules, or memory schemas. Creates or updates Architecture Decision Records (ADRs) before implementation. Keywords: ADR, decision record, proposed, architecture boundary, policy change, API contract, slice design."
argument-hint: "Describe the planned change and whether you need a new ADR, an ADR update, or validation of an existing draft."
---

# ADR Workflow Skill

Use this skill when a DevCD change needs a documented architectural or product decision before implementation.

## When To Use

- A new slice is added or materially restructured
- An existing slice's public interface or models change
- The policy layer rules (allow/deny defaults) are changed
- An API contract or memory schema changes
- An architecture boundary, trust boundary, input path, or output path changes
- An existing ADR draft must be completed or validated

## When NOT Required

- Typo fixes
- Isolated test-only work
- Pure refactors without behavior change
- Contained bugfixes that preserve the existing design

If unsure, prefer a draft ADR that states the uncertainty explicitly.

## Core Rules

1. **ADR first, implementation second.** For boundary changes, schema changes, or policy rule changes, prepare the ADR before coding.
2. **Agents may draft, not accept.** Agents may create or update ADRs with status `proposed`; only the maintainer changes status to `accepted` or `rejected`.
3. **Validation must be testable.** Every ADR needs a concrete validation section with measurable checks.
4. **Do not blur bugfixes and architectural decisions.** Pure bugfixes do not automatically require a new ADR.

## Step 1: Decide Whether An ADR Is Required

Create or update an ADR when the change affects:

- slice design or slice behavior contracts
- policy allow/deny rules or audit log format
- memory schema (working memory or durable memory)
- API routes or request/response contracts
- kernel settings or shared infrastructure

Do NOT force a new ADR for:

- typo fixes
- isolated test-only work
- pure refactors without behavior change
- contained bugfixes that preserve existing design

**Interface-Design Tip:** Before committing to a slice interface design, spawn 2-3 subagents with explicitly different constraints (e.g., "minimize the interface", "maximize flexibility", "optimize for the most common caller"). Radically different constraints force qualitatively different designs. The `subagent-driven-development` skill provides the operational framework.

## Step 2: Create The ADR File

Create the next ADR under `docs/decisions/` using the repository numbering sequence:

```text
docs/decisions/ADR-NNN-short-slug.md
```

Required YAML frontmatter fields at the top of the file:

```yaml
---
id: ADR-NNN
status: proposed
date: YYYY-MM-DD
supersedes: null
---
```

Do not invent custom status values.

## Step 3: Write The Decision Clearly

The ADR body must answer all of these questions:

- What problem or uncertainty is being addressed?
- What is being done?
- What is explicitly not being done?
- Why was this option chosen over alternatives?
- What trade-offs or consequences are accepted?
- How will the decision be validated?

For policy-related ADRs, be explicit about:
- which operations are allow-listed vs deny-listed
- what audit log entries will be emitted
- whether the change affects local-first privacy defaults

For slice-related ADRs, be explicit about:
- which slice(s) are affected
- whether kernel changes are needed (and why)
- expected impact on other slices

## Step 4: Connect The ADR To Evidence

An ADR is not complete if it floats without validation hooks.

Reference the concrete artifacts the later implementation must touch:

- tests under `tests/`
- slice models in `packages/devcd-core/src/devcd/slices/<slice>/models.py`
- API routes in `packages/devcd-core/src/devcd/slices/<slice>/api.py`
- kernel settings in `packages/devcd-core/src/devcd/kernel/settings.py`

## Step 5: Define Validation

The `Validation` section must contain concrete checks:

```bash
make check
pytest tests/test_<slice>.py -v
```

Also state the expected outcome:
- What should pass after implementation?
- What existing tests must continue to pass?

## Step 6: Prepare Commit Linkage

When implementation follows the ADR, the commit body should carry the decision trailer:

```text
Decision: ADR-NNN
```

Do not change ADR status to `accepted` as part of the agent workflow.

## Review Checklist

- [ ] ADR requirement was correctly identified
- [ ] Status is `proposed`
- [ ] Decision and non-goals are explicit
- [ ] Validation is concrete and testable
- [ ] Policy-related ADRs name allow/deny impacts
- [ ] References to tests and affected files are concrete
- [ ] Maintainer-only status boundaries are respected

## References

- `AGENTS.md`
- `.github/copilot-instructions.md`
- `docs/decisions/ADR-001-vertical-slice-architecture.md`
- `CONTRIBUTING.md`
