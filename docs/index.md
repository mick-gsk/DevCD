---
title: DevCD Docs
---

# DevCD Documentation

DevCD is the current working name for a local-first continuity layer for people
who use AI agents. It turns local activity from tools, tasks, notes, and work
sessions into structured context that agents can query without asking you to
restate your situation on every turn.

If you are evaluating DevCD for the first time, start with the shortest path to
value and only drop into architecture once the workflow makes sense.

## Start Here

- [Getting Started](getting-started.md) for the fastest path from install to a
  visible Agent Passport
- [Use Cases](use-cases.md) for concrete scenarios where DevCD helps today
- [Architecture Overview](devcd/architecture.md) for the system shape and slice
  boundaries

## What DevCD Gives You

- Structured context instead of ad-hoc pasted notes
- Local-first state and memory with explicit policy boundaries
- A typed state tree that external tools and agents can inspect
- Agent-facing context through HTTP briefs, CLI handoff commands, and a local
  read-only MCP stdio resource server

## Current Product Surface

Today, DevCD gives you a running local daemon, a CLI, an HTTP API, a typed state
engine, scoped memory, and an explicit policy layer.

That means you can already:

- ingest normalized events with `POST /event`
- query the current work state with `GET /state`
- inspect scoped memory with `GET /memory/{scope}`
- request policy-filtered agent context with `POST /context/brief`
- read local MCP resources through `devcd mcp serve`
- audit default local-first behavior where observations are allowed and actions
  are denied by default

## Read By Goal

- I want the fastest proof that DevCD works:
  [Getting Started](getting-started.md)
- I want to know whether this fits my workflow:
  [Use Cases](use-cases.md)
- I want to understand the design:
  [Architecture](devcd/architecture.md), [Memory](devcd/memory.md),
  [Policy](devcd/policy.md)
- I am an agent consuming local context:
  [How to consume DevCD as an agent](devcd/agent-consumption.md)
- I want to connect OpenClaw:
  [OpenClaw Integration](devcd/openclaw-integration.md)
- I want to extend DevCD safely:
  [Context Packs](devcd/context-packs.md)
- I want to publish or verify a release:
  [Publishing](devcd/publishing.md)
- I want the product direction:
  [Vision](https://github.com/mick-gsk/DevCD/blob/main/VISION.md)
- I want the naming and positioning notes:
  [Naming and Positioning](devcd/naming-and-positioning.md)
- I want to know whether DevCD is ready to try:
  [Release Readiness](devcd/release-readiness.md)
- I want to validate release artifacts:
  [Publishing](devcd/publishing.md)
- I want an isolated demo or CI sandbox:
  [Container Sandbox](devcd/container.md)

## Principles

- Local-first by default
- Explicit policy for every observation or action
- Vertical Slice Architecture for each product capability
- Small shared kernel, slice-owned behavior everywhere else

## Next Step

Run the guided setup in [Getting Started](getting-started.md), then inspect the
current state and memory responses before moving on to the deeper architecture
pages.
