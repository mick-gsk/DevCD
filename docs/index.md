---
title: DevCD Docs
---

## Choose Your Path

<div class="devcd-path-grid">
  <div class="devcd-path-card devcd-callout--checkpoint">
    <h3>Proof in one minute</h3>
    <p>Preview the exact warm-start shape without touching a live workspace.</p>
    <code>devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl</code>
  </div>
  <div class="devcd-path-card devcd-callout--trust">
    <h3>Real workspace in a few minutes</h3>
    <p><a href="getting-started.md">Getting Started</a> is the primary path: onboard, read the Action Packet, then use quickstart as the follow-up report.</p>
  </div>
  <div class="devcd-path-card devcd-callout--safe-share">
    <h3>Deeper fit and architecture</h3>
    <p><a href="use-cases.md">Use Cases</a> and <a href="devcd/architecture.md">Architecture Overview</a> explain where DevCD helps today and how the slices fit together.</p>
  </div>
</div>

<div class="devcd-signal-grid">
  <div class="devcd-callout devcd-callout--trust">
    <p><strong>Trust:</strong> local-first defaults, explicit policy receipts, and visible withheld-context boundaries.</p>
  </div>
  <div class="devcd-callout devcd-callout--safe-share">
    <p><strong>Safe to share:</strong> goal, blocker, do-not-repeat guidance, one next action, and load hints for deeper context.</p>
  </div>
  <div class="devcd-callout devcd-callout--risk">
    <p><strong>Not the default payload:</strong> raw logs, raw file content, secrets, or pasted chat transcripts.</p>
  </div>
</div>

## What DevCD Gives You

- A warm-start handoff for the next agent instead of a manual recap
- Local-first continuity with explicit policy boundaries and withheld-context
  visibility
- Structured metadata instead of pasted transcripts, logs, or raw file dumps
- One continuity layer that CLI, localhost API, and read-only MCP can all read

## Current Product Surface

Today, DevCD gives you a local continuity layer with one dominant first proof:
the next agent can read a policy-filtered Action Packet before asking for a
recap. Around that, DevCD also exposes a CLI, an HTTP API, scoped memory, and a
read-only MCP server for local consumption.

If you only remember one thing, remember this: DevCD is not another agent to
run. It is the layer that lets the next agent resume instead of restart.

That means you can already:

- warm-start a fresh agent with `devcd agentic action-packet`
- make a workspace agent-ready with `devcd onboard`
- inspect the broader continuity view with `devcd context passport`
- read local MCP resources through `devcd mcp serve`
- audit included and withheld context with `devcd context control`
- ingest normalized events and query live local state when you choose to run the
  daemon

## Read By Goal

- I just installed DevCD and want the main path:
  [Getting Started](getting-started.md)
- I want the shortest honest proof before touching my workspace:
  `devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl`
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
- I want the product direction:
  [Vision](https://github.com/mick-gsk/DevCD/blob/main/VISION.md)
- I want the naming and positioning notes:
  [Naming and Positioning](devcd/naming-and-positioning.md)
- I want to know whether DevCD is ready to try:
  [Release Readiness](devcd/release-readiness.md)
- I want to validate or publish a release:
  [Publishing](devcd/publishing.md)
- I want an isolated demo or CI sandbox:
  [Container Sandbox](devcd/container.md)

## Principles

- Local-first by default
- Explicit policy for every observation or action
- Vertical Slice Architecture for each product capability
- Small shared kernel, slice-owned behavior everywhere else

## Next Step

Run the guided setup in [Getting Started](getting-started.md), inspect the
Action Packet first, then open the broader Agent Passport only when the next
agent needs more than the first warm-start surface.
