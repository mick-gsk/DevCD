---
name: improve-codebase-architecture
description: Explore a codebase to find opportunities for architectural improvement, focusing on making the codebase more testable by deepening shallow modules. Use when user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more AI-navigable.
---

# Improve Codebase Architecture

Explore the DevCD codebase like an AI would, surface architectural friction, discover opportunities for improving testability, and propose module-deepening refactors as GitHub issue RFCs.

A **deep module** (John Ousterhout, "A Philosophy of Software Design") has a small interface hiding a large implementation. Deep modules are more testable, more AI-navigable, and let you test at the boundary instead of inside.

## Process

### 1. Explore the codebase

Use the Explore subagent to navigate the codebase naturally. Do NOT follow rigid heuristics — explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small files?
- Where are slice services so shallow that the interface is nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called?
- Where do tightly-coupled slices create integration risk in the seams between them?
- Which slices are untested or hard to test?
- Where does the policy layer create unnecessary coupling?

The friction you encounter IS the signal.

### 2. Present candidates

Present a numbered list of deepening opportunities. For each candidate, show:

- **Cluster**: Which slices/modules are involved
- **Why they're coupled**: Shared types, call patterns, co-ownership of a concept
- **Dependency category**: One of — (a) direct call, (b) shared type, (c) event/message, (d) configuration
- **Test impact**: What existing tests would be replaced by boundary tests

Do NOT propose interfaces yet. Ask the user: "Which of these would you like to explore?"

### 3. User picks a candidate

### 4. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would need to rely on
- A rough illustrative code sketch to make the constraints concrete — this is not a proposal, just a way to ground the constraints

Show this to the user, then immediately proceed to Step 5. The user reads and thinks about the problem while the sub-agents work.

### 5. Design multiple interfaces

Spawn 3+ sub-agents in parallel using the runSubagent tool. Each must produce a **radically different** interface for the deepened module.

Give each agent a different design constraint:

- Agent 1: "Minimize the interface — aim for 1-3 entry points max"
- Agent 2: "Maximize flexibility — support many use cases and extension points"
- Agent 3: "Optimize for the most common caller — make the default case trivial"
- Agent 4 (if applicable): "Design around ports & adapters for cross-slice dependencies"

Each sub-agent outputs:

1. Interface signature (types, methods, params) — Python 3.11+ with full type annotations
2. Usage example showing how callers use it
3. What complexity it hides internally
4. Dependency strategy (how deps are handled)
5. Trade-offs

Present designs sequentially, then compare them in prose.

After comparing, give your own recommendation: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. Be opinionated.

### 6. User picks an interface (or accepts recommendation)

### 7. Write issue file

Write the refactor RFC as a local markdown file in `issues/` using this template:

```markdown
# RFC: [Short Title]

## Problem

[2-3 sentences describing the friction or architectural problem.]

## Proposed Interface

[Paste the chosen interface from Step 5.]

## What It Hides

[What complexity does this hide internally?]

## Migration Path

[How do existing callers migrate? Any breaking changes?]

## Validation

[What tests confirm the refactor is correct?]
```

Do NOT ask the user to review before writing — just write it and share the path.

## DevCD Architecture Notes

When exploring, keep these DevCD-specific patterns in mind:

- **Vertical Slice Architecture**: each slice owns its `models.py`, `service.py`, `api.py`. Cross-slice coupling is a candidate for deepening.
- **Kernel boundary**: `devcd/kernel/` is shared infrastructure. If it grows too large, that's architectural friction.
- **Policy layer**: every state-changing operation should route through policy. If slices bypass the policy layer directly, that's a coupling problem.
- **Local-first privacy**: any module that could accidentally leak data across a boundary is a hardening candidate.
