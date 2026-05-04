# ADR-001: Use Vertical Slice Architecture

## Status

Accepted

## Context

DevCD combines event ingestion, state modeling, memory, policy, and future connector integrations. A classic layered architecture would make it easy for policy and persistence details to spread across the codebase.

## Decision

DevCD will use Vertical Slice Architecture. Product capabilities live under `devcd/slices/<slice_name>/` and own their models, service behavior, API integration, and tests.

## Consequences

- Feature work should usually touch one slice.
- Shared abstractions require evidence from at least two slices.
- Policy checks remain explicit in domain flow.
- Connector-specific behavior can become its own slice when it gains state or policy rules.
