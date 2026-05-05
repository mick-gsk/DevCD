---
name: improve-codebase-architecture
description: "Use when asked to audit, review, or improve the codebase architecture. MUST invoke for: architecture audit, codebase smell, coupling analysis, testability review, shallow module, deep module, slice coupling, module deepening, refactor RFC, AI-navigability, improve testability, what's wrong with the architecture, technical debt review, hard to test, too much coupling, module too large, spaghetti code."
argument-hint: "Describe the scope: full codebase audit, a specific slice, or a known coupling problem."
---

# Improve Codebase Architecture

Surface architectural friction in DevCD, design better interfaces, and capture refactor RFCs — without touching production code.

A **deep module** (John Ousterhout, "A Philosophy of Software Design") has a small interface hiding a large implementation. Deep modules are more testable, more AI-navigable, and let you verify correctness at the boundary instead of in the internals.

<HARD-GATE>
Do NOT propose interface designs or write any RFC before completing the exploration phase and presenting the candidate list to the user. Skipping exploration produces shallow recommendations that miss the real friction.
</HARD-GATE>

## When To Use

- User asks for an architecture audit, codebase review, or "what should we refactor"
- A test is hard to write because it requires standing up too many dependencies
- A new feature forces changes in multiple slices simultaneously
- Two slices share types, call each other directly, or co-own a concept
- The kernel is growing and it's unclear what belongs there
- User says "this is getting hard to navigate" or "I'm not sure how to test this"

## When NOT To Use

- The user wants to implement a specific feature (use `brainstorming` instead)
- The user has a bug to fix (use `systematic-debugging` instead)
- The change is purely cosmetic, docs, or test-only

---

## Step 1 — Explore (mandatory, no skipping)

Use the `Explore` subagent with thoroughness `thorough`. Instruct it to map the following with concrete observations, not generalities:

**Shallow-module signals:**
- Services or modules where the public interface has nearly as many methods as the implementation has lines
- Pure helper functions extracted only for testability but whose callers still contain the real logic
- `api.py` files that do non-trivial business logic instead of delegating to `service.py`

**Coupling signals:**
- Slices that import directly from another slice (instead of through kernel or a shared contract)
- Shared Pydantic models owned by one slice but used by two or more
- Slices that call the same external resource independently without a shared abstraction
- Policy bypass: state changes that don't route through `PolicyEngine`

**Testability signals:**
- Tests that construct 3+ real objects just to test one function
- Tests that use `monkeypatch` extensively instead of testing through the public interface
- Missing test coverage on whole slices or service methods

**AI-navigability signals:**
- Concepts split across many small files requiring context-hopping to understand
- Naming inconsistencies between models, services, and API routes for the same concept

The Explore subagent returns its findings as structured observations, not recommendations.

---

## Step 2 — Present Candidates

Immediately after exploration, present a numbered candidate list. Do NOT wait for a second prompt. For each candidate:

| Field | What to include |
|---|---|
| **Cluster** | Which slices/modules are involved |
| **Problem** | One sentence: what friction this creates today |
| **Coupling category** | (a) direct import, (b) shared type, (c) event/message, (d) configuration |
| **Deepening opportunity** | What a better boundary would look like in one sentence |
| **Test impact** | Which existing tests would become simpler or unnecessary |

End with: *"Which of these would you like to explore? (Pick a number, or say 'all' for a full audit)"*

---

## Step 3 — User Selects a Candidate

---

## Step 4 — Frame the Problem Space

Before spawning design sub-agents, write a short framing section for the selected candidate:

1. **What the module/slice currently does** — its responsibilities and callers
2. **What the friction costs** — concrete: harder tests, forced cross-slice changes, hidden bugs
3. **Constraints a good interface must satisfy** — what must not break, what invariants must hold
4. **Illustrative sketch** — a rough before/after code snippet to make the constraints concrete (not a proposal)

Show this framing, then **immediately** proceed to Step 5. The user reads while sub-agents work in parallel.

---

## Step 5 — Design Multiple Interfaces (parallel sub-agents)

Spawn **3 sub-agents in parallel** using `runSubagent`. Give each a different design constraint:

- **Agent 1 — Minimal**: "Design an interface with 1–3 entry points max. Collapse everything else into internals."
- **Agent 2 — Flexible**: "Design an interface that supports extension points and multiple use cases without the caller knowing the internals."
- **Agent 3 — Caller-optimised**: "Design around the most common real caller. Make the default case trivially simple."

Each sub-agent must produce:

1. Interface signature — Python 3.11+, full type annotations, Pydantic v2 models
2. Usage example from the perspective of the most common real caller
3. What complexity moves into the implementation (what the caller no longer needs to know)
4. How cross-slice dependencies are handled
5. Trade-offs (what this design gives up)

Present all three designs. Then give your own recommendation: which is strongest, why, and whether a hybrid would be better. Be opinionated — don't hedge.

---

## Step 6 — User Confirms Interface

---

## Step 7 — Write the RFC

Write the refactor RFC to `docs/superpowers/plans/RFC-<slug>.md` using this template:

```markdown
# RFC: [Short Title]

**Status:** draft
**Date:** YYYY-MM-DD
**Slices affected:** [list]

## Problem

[2–3 sentences: what friction exists today, what it costs.]

## Proposed Interface

[Paste the chosen interface design from Step 5 with full type signatures.]

## What It Hides

[What complexity moves into the implementation? What does the caller no longer need to know?]

## Migration Path

[How do existing callers migrate? Are there breaking changes? Step-by-step if needed.]

## Validation

[What tests confirm the refactor is correct? Name specific test functions or describe boundary tests.]

## Alternatives Considered

[Brief summary of the other two designs from Step 5 and why this one was chosen.]
```

Write the file without asking first. Share the path when done.

---

## DevCD Architecture Notes

When exploring and designing, apply these DevCD-specific lenses:

- **Vertical Slice Architecture**: each slice owns `models.py`, `service.py`, `api.py`. Cross-slice direct imports are a coupling smell.
- **Kernel boundary**: `devcd/kernel/` is shared infrastructure. Kernel growth is a sign that slice boundaries have drifted.
- **Policy layer**: every state-changing operation must route through `PolicyEngine`. Direct bypasses are both a bug and a coupling problem.
- **Local-first privacy**: any module that could leak data across a trust boundary without an explicit policy decision is a hardening candidate.
- **Pydantic v2 models**: shared models that leak into multiple slices create rigid coupling — a candidate for per-slice view models with a kernel-level canonical type.

---

## Output Checklist

Before finishing, confirm:

- [ ] Candidate list was presented before any interface was proposed
- [ ] Problem framing was written before sub-agents were spawned
- [ ] Three distinct designs were produced by parallel sub-agents
- [ ] A concrete recommendation was given (not just "it depends")
- [ ] RFC file written to `docs/superpowers/plans/RFC-<slug>.md`
- [ ] RFC includes migration path and validation section
