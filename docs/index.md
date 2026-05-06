---
title: DevCD — Context Layer for AI Developers
---

## What DevCD Does

<div class="devcd-feature-grid">
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">⚡</div>
    <h3>Action Packet</h3>
    <p>Structured warm-start context for every new agent session. Goal, last blocker, do-not-repeat, and one next action—delivered in a single policy-filtered payload.</p>
    <a class="devcd-feature-link" href="getting-started/">Learn more →</a>
  </div>
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">🔒</div>
    <h3>Local-First Privacy</h3>
    <p>All context stays on your machine. No remote export, no telemetry, no cloud sync by default. You explicitly decide what gets shared and with whom.</p>
    <a class="devcd-feature-link" href="devcd/policy/">Policy docs →</a>
  </div>
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">📋</div>
    <h3>Policy Receipts</h3>
    <p>Every observation and every withholding is logged with a policy receipt. You always see exactly what was included in a handoff—and what stayed out.</p>
    <a class="devcd-feature-link" href="devcd/policy/">Read more →</a>
  </div>
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">🔌</div>
    <h3>MCP Server</h3>
    <p>Native Model Context Protocol server for direct agent consumption. Any MCP-capable agent can read your local DevCD context without you pasting anything.</p>
    <a class="devcd-feature-link" href="devcd/agent-consumption/">Agent docs →</a>
  </div>
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">🤝</div>
    <h3>Works With All Agents</h3>
    <p>One onboarding command configures Claude, GitHub Copilot, Codex, and OpenClaw at once. All your agents start warm from the same local context source.</p>
    <a class="devcd-feature-link" href="devcd/agent-landscape/">Agent landscape →</a>
  </div>
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">🖥️</div>
    <h3>CLI + HTTP API</h3>
    <p>Full-featured command-line interface backed by a local HTTP API. Use it interactively, in scripts, or from any tool that speaks HTTP on localhost.</p>
    <a class="devcd-feature-link" href="devcd/architecture/">Architecture →</a>
  </div>
</div>

## Works With

<div class="devcd-compat-row">
  <span class="devcd-compat-pill">Claude</span>
  <span class="devcd-compat-pill">GitHub Copilot</span>
  <span class="devcd-compat-pill">OpenAI Codex</span>
  <span class="devcd-compat-pill devcd-compat-pill--highlight">OpenClaw</span>
  <span class="devcd-compat-pill">Cursor</span>
  <span class="devcd-compat-pill">Any MCP Agent</span>
</div>

## Quick Start

<div class="devcd-qs-grid">
  <div class="devcd-qs-step">
    <div class="devcd-qs-num">1</div>
    <div class="devcd-qs-body">
      <strong>Install</strong>
      <code>pip install devcd</code>
    </div>
  </div>
  <div class="devcd-qs-step">
    <div class="devcd-qs-num">2</div>
    <div class="devcd-qs-body">
      <strong>Onboard your workspace</strong>
      <code>devcd onboard</code>
    </div>
  </div>
  <div class="devcd-qs-step">
    <div class="devcd-qs-num">3</div>
    <div class="devcd-qs-body">
      <strong>Read the Action Packet</strong>
      <code>devcd agentic action-packet</code>
    </div>
  </div>
</div>

<div class="devcd-cta-pair">
  <a class="devcd-cta devcd-cta--primary" href="getting-started/">Full Getting Started Guide →</a>
  <a class="devcd-cta devcd-cta--secondary" href="use-cases/">Browse Use Cases</a>
</div>

---

## Why DevCD

<div class="devcd-why-grid">
  <div class="devcd-why-card devcd-callout--trust">
    <strong>Trust by default</strong>
    <p>Local-first defaults, explicit policy receipts, and visible withheld-context boundaries on every handoff.</p>
  </div>
  <div class="devcd-why-card devcd-callout--safe-share">
    <strong>Safe to share</strong>
    <p>Goal, blocker, do-not-repeat, one next action, and context-load hints—nothing raw, nothing that shouldn't travel.</p>
  </div>
  <div class="devcd-why-card devcd-callout--checkpoint">
    <strong>No recap tax</strong>
    <p>The next agent reads the Action Packet instead of asking you to re-explain your last three hours of work.</p>
  </div>
</div>

If you only remember one thing: DevCD is not another agent to run. It is the layer that lets the next agent **resume** instead of restart.

→ [Read the Getting Started guide](getting-started.md) — from fresh install to warm agent session in under 5 minutes.
