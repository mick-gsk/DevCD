---
title: DevCD Docs
---

# DevCD Documentation

DevCD is a local-first developer context daemon for agentic workflows. It turns
activity from your editor, Git, tasks, and notes into structured context that
agents can query without asking you to restate your environment on every turn.

If you are evaluating DevCD for the first time, start with the shortest path to
value and only drop into architecture once the workflow makes sense.

## Start Here

- [Getting Started](getting-started.md) for the fastest path from install to a
  visible state update
- [Use Cases](use-cases.md) for concrete scenarios where DevCD helps today
- [Architecture Overview](devcd/architecture.md) for the system shape and slice
  boundaries

## What DevCD Gives You

- Structured context instead of ad-hoc pasted notes
- Local-first state and memory with explicit policy boundaries
- A typed state tree that external tools and agents can inspect
- A foundation for future agent-facing integrations, including the planned MCP
  bridge

## Current Product Surface

Today, DevCD gives you a running local daemon, a CLI, an HTTP API, a typed state
engine, scoped memory, and an explicit policy layer.

That means you can already:

- ingest normalized events with `POST /event`
- query the current work state with `GET /state`
- inspect scoped memory with `GET /memory/{scope}`
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
- I want the product direction:
  [Vision](https://github.com/mick-gsk/DevCD/blob/main/VISION.md)

## Principles

- Local-first by default
- Explicit policy for every observation or action
- Vertical Slice Architecture for each product capability
- Small shared kernel, slice-owned behavior everywhere else

## Next Step

Run the guided setup in [Getting Started](getting-started.md), then inspect the
current state and memory responses before moving on to the deeper architecture
pages.
