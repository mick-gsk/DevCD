# Use Cases

DevCD is most useful when an agent or tool needs reliable, local context without
asking you to repeat what your environment already knows.

The examples below stay close to what the current repository already exposes:
events, state, memory, and policy.

## 1. Stop Re-Explaining Your Current Task (Works today)

Problem: each new agent turn starts with missing context, so you repeat the same
file focus, Git state, task intent, or notes.

Where DevCD helps today:

- warm-starts the next coding agent with an Action Packet before it asks for a recap
- keeps the current goal, latest failure or blocker, and one next action visible
- preserves withheld-context notes so the next agent knows what was intentionally hidden

Best commands: `devcd onboard`, `devcd agentic action-packet`, `devcd handoff`

Why this matters: your context becomes queryable state instead of disposable chat
history.

## 2. Keep Context Local While Making Decisions Explicit (Works today)

Problem: many agent workflows mix convenience with unclear trust boundaries. You
can no longer tell what was observed, what was stored, or what was allowed to act.

Where DevCD helps today:

- local-first defaults with no remote export by default
- explicit policy decisions for observation and action paths
- auditable reasoning around what is allowed or denied

Why this matters: local context becomes safer to operationalize because policy is
part of the product surface, not an afterthought.

## 3. Build Agent Integrations On Top of Stable Context (Works today)

Problem: every agent integration invents its own ad-hoc context plumbing.

Where DevCD helps today:

- a mixed agent stack can share one local continuity source instead of passing
  fragile recap text between runtimes
- consistent HTTP surface for event ingestion, state reads, and memory reads
- typed models and schemas that make integration behavior easier to reason about
- agent-facing context through CLI briefs, HTTP context endpoints, and a local
  read-only MCP stdio resource server

Why this matters: you can treat DevCD as a context layer rather than embedding
workflow-specific memory logic into every agent integration.

## 4. Make Work State Inspectable Across Tools (Partial today)

Problem: editor activity, task notes, and Git movement often live in separate
surfaces with no shared model.

Where DevCD helps today:

- event normalization across developer activity sources
- one host state engine instead of disconnected point solutions
- memory and policy that sit next to state instead of outside it

Why this matters: the same local system can answer both "what am I working on?"
and "should this be allowed?"

Best commands: `devcd context passport`, `devcd context control`, `devcd context budget`

## 5. Resume Across Session Boundaries (Agent Continuity, Works today)

Problem: when an agent session ends, the next agent starts from zero. The goal,
last failure, stale attempts, and suggested next action all have to be re-stated
from scratch.

Where DevCD helps today:

- warm-starts the next coding agent with an **Action Packet** before it asks for
  a recap
- includes the current goal, latest failure or blocker, do-not-repeat guidance,
  one suggested next action, and withheld-context notes
- accessible via CLI (`devcd agentic action-packet` or
  `devcd agentic action-packet-demo`) and MCP
  (`devcd://context/action-packet`)
- keeps the broader Agent Passport and Continuity Packet available when an agent
  needs more than the first handoff

Why this matters: session loss becomes a recoverable state, not a blank slate.

Best commands: `devcd agentic action-packet`, `devcd quickstart`, `devcd context passport`

## Context Packs

Context Packs declare the event types, surfaces, and policy notes for a specific
continuity domain. The developer pack is the first mature proof and drives the
coding-agent and IDE surfaces. A research pack is also declared and exercised by
a synthetic metadata-only fixture covering source review metadata, hypotheses,
and failed approaches.

Packs extend the same local policy and continuity infrastructure. They do not
add remote dependencies, external connectors, new event collectors, or telemetry
paths.

List available packs: `devcd context packs`

## When DevCD Is a Good Fit

DevCD is a good fit when you want:

- a local continuity layer between your environment and AI tooling
- inspectable state instead of hidden prompt assembly
- policy-aware handling of observation and action

## When DevCD Is Not the Main Product

DevCD is not a model, chat client, end-user assistant, remote exporter, or
telemetry service. It is most valuable as the continuity layer underneath those
systems so you do not have to rebuild context by hand every time the agent
changes.

If that is the problem you are trying to solve, continue with
[Getting Started](getting-started.md) and then the
[Architecture Overview](devcd/architecture.md).