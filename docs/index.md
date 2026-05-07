---
title: DevCD — Context Layer for AI Developers
---

<p align="center">
  <img src="assets/devcd-wordmark.svg?v=20260507" alt="DevCD" width="500">
</p>

<p align="center">
  <img src="assets/devcd-mark.svg?v=20260507" alt="DevCD mark" width="84">
  <img src="assets/devcd-social-avatar.svg?v=20260507" alt="DevCD social avatar" width="84">
</p>

<div class="devcd-section devcd-section--dark">

## ⟩ What developers say about the problem

<div class="devcd-quote-grid">
  <blockquote class="devcd-quote">
    <p>"Every new agent starts with a blank slate. You paste context. You explain what happened. You re-describe the task that was already described in three other places."</p>
    <cite>— DevCD VISION.md</cite>
  </blockquote>
  <blockquote class="devcd-quote">
    <p>"The next agent repeats failed attempts because it cannot see what already went wrong. Context is not portable, not structured, and not policy-governed."</p>
    <cite>— DevCD VISION.md</cite>
  </blockquote>
  <blockquote class="devcd-quote">
    <p>"AI agents should know what you are trying to continue without you having to tell them every time."</p>
    <cite>— Core Conviction, DevCD</cite>
  </blockquote>
</div>

</div>

<div class="devcd-section devcd-section--features">

## ⟩ What DevCD Does

<div class="devcd-feature-grid">
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">⚡</div>
    <h3>Action Packet</h3>
    <p>Structured warm-start context for every new agent session. Goal, last blocker, do-not-repeat, and one next action—in a single policy-filtered payload.</p>
    <a class="devcd-feature-link" href="getting-started/">Learn more →</a>
  </div>
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">🔒</div>
    <h3>Local-First Privacy</h3>
    <p>All context stays on your machine. No remote export, no telemetry, no cloud sync by default. You decide what gets shared and with whom.</p>
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
    <p>Native Model Context Protocol server for direct agent consumption. Any MCP-capable agent reads your local DevCD context without you pasting anything.</p>
    <a class="devcd-feature-link" href="devcd/agent-consumption/">Agent docs →</a>
  </div>
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">🤝</div>
    <h3>Works With All Agents</h3>
    <p>One command configures Claude, GitHub Copilot, Codex, and OpenClaw at once. All your agents start warm from the same local context source.</p>
    <a class="devcd-feature-link" href="devcd/agent-landscape/">Agent landscape →</a>
  </div>
  <div class="devcd-feature-card">
    <div class="devcd-feature-icon">🖥️</div>
    <h3>CLI + HTTP API</h3>
    <p>Full-featured CLI backed by a local HTTP API. Use it interactively, in scripts, or from any tool that speaks HTTP on localhost.</p>
    <a class="devcd-feature-link" href="devcd/architecture/">Architecture →</a>
  </div>
</div>

</div>

<div class="devcd-section devcd-section--compat">

## ⟩ Works With

<div class="devcd-compat-row">
  <span class="devcd-compat-pill">Claude</span>
  <span class="devcd-compat-pill">GitHub Copilot</span>
  <span class="devcd-compat-pill">OpenAI Codex</span>
  <span class="devcd-compat-pill devcd-compat-pill--highlight">OpenClaw</span>
  <span class="devcd-compat-pill">Cursor</span>
  <span class="devcd-compat-pill">Any MCP Agent</span>
</div>

</div>

<div class="devcd-section devcd-section--quickstart">

## ⟩ Quick Start

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
      <strong>Setup your workspace</strong>
      <code>devcd setup --yes</code>
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

</div>

<div class="devcd-section devcd-section--why">

## ⟩ Why DevCD

<div class="devcd-why-grid">
  <div class="devcd-why-card devcd-callout--trust">
    <strong>Trust by default</strong>
    <p>Local-first defaults, explicit policy receipts, and visible withheld-context boundaries on every handoff.</p>
  </div>
  <div class="devcd-why-card devcd-callout--checkpoint">
    <strong>No recap tax</strong>
    <p>The next agent reads the Action Packet instead of asking you to re-explain your last three hours of work.</p>
  </div>
  <div class="devcd-why-card devcd-callout--safe-share">
    <strong>Safe to share</strong>
    <p>Goal, blocker, do-not-repeat, one next action, and context-load hints—nothing raw, nothing that shouldn't travel.</p>
  </div>
</div>

<p class="devcd-section__note">DevCD is not another agent to run. It is the layer that lets the next agent <strong>resume</strong> instead of restart.</p>

<div class="devcd-cta-pair">
  <a class="devcd-cta devcd-cta--primary" href="getting-started/">Get Started — under 5 minutes →</a>
  <a class="devcd-cta devcd-cta--ghost" href="https://github.com/mick-gsk/DevCD" target="_blank" rel="noopener noreferrer">Star on GitHub</a>
</div>

</div>
