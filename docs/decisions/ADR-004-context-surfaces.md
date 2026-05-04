---
id: ADR-004
status: proposed
date: 2026-05-04
supersedes: null
---

# Context Surfaces as Product Primitives

## Context

DevCD context briefs are currently policy-filtered, but every allowed local
client receives the same brief shape once the requested data class is allowed.
Different agent roles need different context breadth: coding agents can use
normal working context, reviewers need review-relevant state, debugging agents
need diagnostic depth, subagents need focused handoff context, and public demos
must avoid exposing private work details.

## Decision

Represent context surfaces inside the existing `ambient_context` slice and keep
the existing `policy_layer` as the source of export allow/deny decisions. A
surface definition declares:

- allowed state areas;
- allowed memory scopes;
- detail level;
- sensitive fields that must be withheld;
- policy-readable explanations in the generated brief.

The first product surfaces are `coding-agent`, `review-agent`,
`debugging-agent`, `subagent`, and `public-demo`. Existing transport-oriented
surface kinds such as `cli`, `http`, `mcp`, `vscode`, `artifact`, and `other`
remain compatible and use the current broad local metadata behavior.

The brief generator applies the surface definition after the normal export
policy decision. A surface cannot reveal data that policy denied, and fields not
allowed by the selected surface are represented as withheld context with safe
summaries instead of raw values.

## Non-Goals

- Do not introduce a second global policy engine.
- Do not add remote export, telemetry, or action execution.
- Do not persist new surface state outside the existing local memory/state
  services.
- Do not make public-demo context depend on caller trust or implicit defaults.

## Alternatives Considered

1. Add separate endpoints for each agent role. This would duplicate the brief
   contract and make future policy review harder.
2. Add a new global policy engine for surfaces. This is unnecessary because the
   existing policy layer already owns export allow/deny decisions.
3. Add typed surface definitions to the ambient context service. This is the
   smallest change that keeps the contract testable and preserves slice
   boundaries.

## Consequences

Context briefs become role-aware without weakening the local-first policy
defaults. Public surfaces can safely explain what was withheld, while internal
agent surfaces keep enough context to be useful. The ambient context brief
contract grows with surface metadata, so JSON schema and tests must stay aligned
with the model.

## Validation

Implementation must add or update these checks:

```bash
pytest tests/test_ambient_context.py -v
make check
```

Expected outcomes:

- a coding-agent brief includes allowed work context and visible policy
  reasoning;
- a public-demo brief withholds private goal, Git, attempt, and blocker details;
- a subagent brief includes focused context without broad history;
- all context surfaces are typed and testable through the ambient context slice;
- the full repository check continues to pass.