# Agent Landscape

This page records the product decision behind DevCD's agent-facing surfaces. It is based on current public documentation for GitHub Copilot coding agent, Claude Code, OpenAI Codex, and their MCP/instruction/memory surfaces.

## Current signal

Modern coding agents already execute work:

- GitHub Copilot coding agent can research a repository, plan a task, change code on a branch, run tests or linters in a GitHub Actions environment, and open or update a pull request.
- Claude Code can read a codebase, edit files, run commands, create commits and pull requests, use MCP, run subagents, resume prior sessions, and work across terminal, IDE, desktop, web, and scheduled surfaces.
- OpenAI Codex exposes the same broad shape for coding automation: repository instructions, skills, hooks, MCP, approvals, security boundaries, and GitHub integration.
- MCP is becoming the shared integration layer for resources and tools, but each host chooses its own loading rules, trust prompts, scopes, output limits, and persistence behavior.

The weak point is not raw execution. The weak point is continuity across surfaces:

- Cloud coding agents usually work in task, branch, PR, or ephemeral execution boundaries.
- IDE and terminal agents can resume their own sessions, but that memory is local to the tool and not a runtime-neutral contract.
- Instruction files such as `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` are context, not a reliable state system or hard policy layer.
- Tool-specific auto memory can be useful, but it is scoped to one agent runtime and can be unavailable to another runtime or cloud environment.
- MCP can expose context, but untrusted tools, output-size pressure, auth scopes, and host-specific behavior make policy and summarization part of the product, not an afterthought.

## DevCD decision

DevCD should remain the local continuity layer for AI agents, not become an executor.

That means the product should prioritize:

- A first action for any fresh agent: read `devcd agentic action-packet` or the read-only `devcd://context/action-packet` MCP resource before asking the user to recap.
- A policy-filtered continuity contract: current goal, next action, evidence, blockers, do-not-repeat warnings, and withheld-context summaries with policy reasons.
- Runtime-neutral consumption: CLI, HTTP, and MCP expose the same agent-facing contract without requiring a specific model, vendor, editor, or cloud environment.
- Local-first storage and policy gates: no remote export and no state-changing runner start without explicit policy.
- Demonstrable golden paths: checked-in JSONL fixtures should prove that Agent B can resume Agent A's failed work without raw private payloads.

DevCD should avoid:

- Competing with Copilot, Claude Code, Codex, or OpenClaw as the primary code executor.
- Adding remote task dispatch as a default behavior.
- Treating instruction files as sufficient memory.
- Emitting hidden payloads when policy says context was withheld.
- Making users manually perform continuity bookkeeping after onboarding.

## Golden path

The smallest proof is the Action Packet demo:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl
```

The fixture encodes a failed attempt, a next action, a do-not-repeat warning, and a sensitive note. The resulting packet tells the next agent what to do, what failed, and what was withheld, without exposing the sensitive note payload.

This is the product shape to deepen before adding more execution: prove that a fresh agent can start warm, safely, and without re-asking the user for context.

## Sources reviewed

- GitHub Docs: Copilot coding agent, custom instructions, Copilot Memory, MCP, custom agents, hooks, and skills.
- Anthropic Docs: Claude Code overview, memory, common workflows, MCP, scopes, resources, output limits, tool search, and managed MCP configuration.
- OpenAI Docs: Codex coding agent, AGENTS.md, MCP, skills, subagents, hooks, approvals, security, and GitHub integration.
