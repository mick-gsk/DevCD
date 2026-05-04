# Use Cases

DevCD is most useful when an agent or tool needs reliable, local context without
asking you to repeat what your environment already knows.

The examples below stay close to what the current repository already exposes:
events, state, memory, and policy.

## 1. Stop Re-Explaining Your Current Task

Problem: each new agent turn starts with missing context, so you repeat the same
file focus, Git state, task intent, or notes.

Where DevCD helps today:

- normalize activity into structured events
- maintain a typed state tree behind `GET /state`
- separate working memory from longer-lived memory scopes

Why this matters: your context becomes queryable state instead of disposable chat
history.

## 2. Keep Context Local While Making Decisions Explicit

Problem: many agent workflows mix convenience with unclear trust boundaries. You
can no longer tell what was observed, what was stored, or what was allowed to act.

Where DevCD helps today:

- local-first defaults with no remote export by default
- explicit policy decisions for observation and action paths
- auditable reasoning around what is allowed or denied

Why this matters: local context becomes safer to operationalize because policy is
part of the product surface, not an afterthought.

## 3. Build Agent Integrations On Top of Stable Context

Problem: every agent integration invents its own ad-hoc context plumbing.

Where DevCD helps today:

- consistent HTTP surface for event ingestion, state reads, and memory reads
- typed models and schemas that make integration behavior easier to reason about
- a clear product direction toward an agent-facing MCP bridge

Why this matters: you can treat DevCD as a context layer rather than embedding
workflow-specific memory logic into every agent integration.

## 4. Make Work State Inspectable Across Tools

Problem: editor activity, task notes, and Git movement often live in separate
surfaces with no shared model.

Where DevCD helps today:

- event normalization across developer activity sources
- one host state engine instead of disconnected point solutions
- memory and policy that sit next to state instead of outside it

Why this matters: the same local system can answer both "what am I working on?"
and "should this be allowed?"

## When DevCD Is a Good Fit

DevCD is a good fit when you want:

- a local context layer between your environment and AI tooling
- inspectable state instead of hidden prompt assembly
- policy-aware handling of observation and action

## When DevCD Is Not the Main Product

DevCD is not a model, chat client, or end-user assistant. It is most valuable as
infrastructure that makes those systems more consistent, local, and explainable.

If that is the problem you are trying to solve, continue with
[Getting Started](getting-started.md) and then the
[Architecture Overview](devcd/architecture.md).