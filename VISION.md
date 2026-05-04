# Vision

DevCD is built on one conviction: **agents should know what you are working on without you having to tell them every time.**

## The Problem

Today, every agentic tool starts with a blank slate. You paste context. You explain your stack. You re-describe the task that was already described in three other places. Context is not portable, not structured, and not policy-governed.

## The Direction

DevCD is the context layer that sits between a developer's working environment and the agents that assist them.

It is not a model, a chat interface, or a task runner. It is a daemon — a persistent, local, structured source of truth about what is happening right now.

### Principles

1. **Local-first, always.** Developer context is sensitive. Observation runs locally by default. Remote export requires explicit configuration and policy.

2. **Explicit policy.** Every observation or action passes through a policy decision that can be inspected, logged, and reasoned about. No implicit side effects.

3. **Structured state, not raw text.** Events are normalized. State is typed. Memory has scope and TTL. Agents receive structured context, not raw file diffs.

4. **Vertical Slice Architecture.** Each feature domain — events, state, memory, policy, bridge — owns its models, services, and tests. The kernel stays intentionally small.

5. **Zero vendor lock-in.** The protocol is MCP-compatible. The storage is local JSON Lines. The daemon runs on any POSIX-compatible machine.

## Milestones

### v0.1 — Foundation (current)
- POST /event, GET /state, GET /memory/{scope}
- Default policy: observe allowed, actions denied
- Working-memory TTL
- Local event ledger
- CLI and runtime config

### v0.2 — MCP Bridge
- MCP-compatible resource + tool surface
- Agent-facing context API (read-only)
- Scoped memory access per agent session

### v0.3 — IDE Integration
- VS Code extension for event emission
- Git hook event normalization
- Task/TODO integration

### v0.4 — Policy Editor
- Human-readable policy definitions
- Per-event-class allow/deny rules
- Audit log with policy reasoning

### Future
- Multi-machine context sync (opt-in, encrypted)
- Agent-writable memory scope (with policy gate)
- Webhook emission for external automation
- Plugin SDK for custom event normalizers
