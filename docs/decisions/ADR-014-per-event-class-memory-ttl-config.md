---
id: ADR-014
status: proposed
date: 2026-05-07
supersedes: null
---

# Per-Event-Class Working Memory TTL Configuration

## Context

Decision 4 requires additive configuration under `[memory.ttl_by_event_class]` with documented defaults (`tool_output=3600`, `decision=604800`, `warning=2592000`) and runtime behavior that computes and enforces `expires_at` by event class.

## Decision

Do not implement Decision 4 in this change because introducing `[memory.ttl_by_event_class]` and `memory.max_entries` requires extending the central config contract in `kernel/settings.py`, which is out of scope under the current kernel-change constraint.

## Rationale

Kernel-owned settings are the single source of truth for `devcd.toml`; bypassing them in slice code would create a hidden contract fork and break vertical-slice boundary guarantees.
