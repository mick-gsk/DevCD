---
id: ADR-012
status: proposed
date: 2026-05-05
supersedes: null
---

# Public Alpha Agent Passport Surface

## Context

DevCD's first public alpha needs a product loop that is easier to understand
than the underlying daemon, MCP resource, event ledger, and policy machinery.
The strongest user-facing promise is that a new agent can continue from a local,
policy-filtered Agent Passport without asking the user to recap the work.

OpenClaw's adoption pattern shows that first-run success, visible product
surfaces, proof artifacts, and trust diagnostics matter as much as architecture.
DevCD already has the core pieces: agent-ready init, daemonless metadata capture,
Agent Passport rendering, context control reports, read-only MCP resources, and
OpenClaw/Hermes integration snippets. The remaining public-alpha work should
package those pieces into a coherent first-run and proof path without weakening
DevCD's local-first boundary.

This decision must also preserve earlier decisions:

- ADR-009 keeps `devcd init` as the foundational configuration entry point.
- ADR-010 keeps agent capture daemonless, metadata-only, and policy-gated.
- ADR-011 keeps Action Packets and policy-filtered handoff data as the primary
  agent-facing output, rather than a dashboard of raw local context.

## Decision

Add a public-alpha Agent Passport surface composed of small, local-first pieces:

1. `devcd onboard` may be added as a friendly first-run wrapper around existing
   `init`, agent-ready setup, doctor, quickstart, and Agent Passport guidance.
   It must not replace `devcd init` as the underlying configuration mechanism,
   and it must not silently mutate global or external agent runtime config.
2. The first visible proof path should lead users toward an Agent Passport or
   Action Packet, not toward raw JSON, raw logs, or daemon internals.
3. A future local dashboard may expose policy-filtered Agent Passport and
   context-control data over loopback HTTP, protected by the existing local
   bearer token and existing API middleware. It must remain read-only in the
   public-alpha scope.
4. Trust diagnostics should be elevated as product UX. Commands and docs should
   clearly show what DevCD saw, what it withheld, why the selected agent surface
   may see it, and that remote export remains disabled by default.
5. Ecosystem growth should begin with Context Packs, event recipes, examples,
   and contribution templates. Do not add a marketplace, remote plugin loader,
   or arbitrary extension execution path in the public-alpha scope.

## Non-Goals

- Do not make DevCD a personal AI assistant, chat gateway, model provider,
  browser automation layer, or OpenClaw clone.
- Do not add hosted deployment or remote export as a default public-alpha path.
- Do not expose write-capable MCP tools, MCP prompts, shell execution, browser
  automation, or memory mutation through MCP.
- Do not start local agent runners from MCP.
- Do not capture raw file contents, raw logs, full chat transcripts, private
  notes, browser payloads, or secrets through onboarding or dashboard flows.
- Do not silently edit Copilot, Claude, Codex, OpenClaw, Cursor, or other global
  runtime configuration outside the current workspace.
- Do not introduce a third-party plugin registry or executable extension loader
  without a separate ADR.

## Consequences

The alpha product story becomes easier to test and share: install DevCD, run a
guided local setup, produce an Agent Passport, let the next agent continue, and
inspect what context was withheld by policy.

`devcd onboard` creates a clearer user journey while keeping implementation
reuse high. It should call the same config and agent-ready helpers as `devcd
init`, and it should preserve existing files through the managed-block mechanism.

A future dashboard is allowed only as a read-only visualization of already
policy-filtered data. Any dashboard route or API model must reuse the existing
ambient context and context-control contracts unless a later ADR justifies a new
contract.

The ecosystem path remains intentionally conservative. Context Packs and event
recipes can make DevCD extensible without executing untrusted code or bypassing
policy.

## Validation

Implementation following this ADR must include focused checks for each public
surface it changes:

```bash
python -m pytest tests/test_cli.py -q
python -m pytest tests/test_api.py -q
python -m pytest tests/test_ambient_context.py -q
python -m pytest tests/test_mcp_server.py -q
make check
python -m mkdocs build --strict
```

For `devcd onboard`, tests must verify:

- a missing config is created through the existing config path;
- an existing config is preserved unless an explicit overwrite option is used;
- selected workspace agent instruction files receive only the managed DevCD
  block;
- OpenClaw setup writes only the local `.devcd/openclaw-mcp.json` snippet;
- external runtime config directories are not mutated;
- JSON output is stable enough for automation;
- the command does not require a running daemon.

For any dashboard work, tests must verify:

- routes stay protected by loopback plus local bearer token;
- rendered data is policy-filtered;
- sensitive payloads, raw logs, and secrets do not appear in responses;
- the dashboard does not expose state-changing operations.

For ecosystem work, tests and docs must verify that Context Packs and recipes
remain metadata-first and policy-gated.
