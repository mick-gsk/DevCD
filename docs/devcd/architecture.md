# DevCD Architecture

DevCD is the local continuity layer underneath a mixed agent stack. The
architecture exists to make one outcome reliable: the next agent should resume
from visible work state instead of starting cold.

Under that product surface, DevCD has three explicit responsibilities: observe
developer events, update an in-memory work-state tree, and expose
policy-filtered state and memory to trusted local clients.

If you are evaluating whether DevCD is serious enough to build on, the key
architectural point is this: Action Packet, Agent Passport, CLI, HTTP, and
read-only MCP all come from the same local event and policy pipeline rather than
from separate prompt-assembly paths.

The MVP trust boundary is loopback-only plus a local bearer token. Requests that do not target loopback hosts or do not present the configured token are denied before state, memory, or ledger behavior runs.

## Why This Matters

- You get one continuity model instead of one per agent runtime.
- Policy applies before context is rendered, not after prompt assembly.
- The same local ledger can drive a short warm-start surface and a deeper
  inspectable passport.
- Extension work stays additive because the slice boundaries are explicit.

## Monorepo Layout

```text
packages/devcd-core/src/devcd/
  kernel/                  shared primitives only
  slices/
    events/                normalized event contract
    host_state_engine/     state tree and API routes
    memory_layer/          working, episodic, semantic memory
    policy_layer/          observation/action authorization
    git_source/            Git branch and commit event collection
    ambient_context/       derived work-state and agent context briefs
```

## Runtime Flow

```text
source event -> auth + loopback check -> policy decision -> ledger append -> state update -> memory update -> ambient context derivation
```

The MVP keeps the state tree in memory and appends storage-approved events to a local JSON Lines ledger. Later versions can replace the persistence adapter with SQLite without changing the slice contracts.

That separation matters because DevCD is not trying to be another agent runtime.
It is trying to stay a stable local source of continuity even when the agent,
model, or interface changes around it.

On startup, DevCD replays ledger records to rebuild visible state and repopulate working and episodic memory. A truncated trailing JSONL line is ignored so interrupted writes do not corrupt restart recovery.

Runtime settings are loaded from `devcd.toml` or `DEVCD_` environment variables. Defaults are local-first: observation enabled, local storage enabled, remote export disabled, actions disabled.

High-frequency IDE events such as `file_focus` and `cursor_move` are coalesced within a short configured window before they fan out into recent actions. This keeps the visible state stable while preserving aggregated attention signals.

Read-time visibility for disabled sources is decided in `policy_layer` and consumed by state and memory reads. Audit metadata may remain in the ledger for retention and replay purposes, while active `/state` and `/memory/*` responses hide disabled-source context.

## Ambient Context Kernel

The ambient context slice owns DevCD's derived work-state model: active intent, relevant artifacts, open loops, recent attempts, blocker signals, proactive suggestions, freshness, confidence, and policy-gated context surfaces for agents. It consumes events, host state, memory, and policy decisions through public slice services; it does not own raw observation, storage, or policy enforcement.

This is where the warm-start surfaces become usable. Ambient context takes the
raw event stream and turns it into the smaller objects that matter to a fresh
agent: Action Packet, Agent Passport, Continuity Packet, context references,
budget guidance, and session contract.

Agent surfaces ask for context through `/context/work-state` and `/context/brief`. Suggestions are advisory only: dismissal records a local cooldown, but DevCD does not perform the suggested action. Retained context can be inspected, corrected, or deleted through `/context/memory` so users can control which local facts influence future work states and briefs.

## Vertical Slice Rules

- A slice owns its public models and service behavior.
- Cross-slice calls go through public service interfaces.
- Shared kernel code must stay framework-light and deterministic.
- Policy decisions are part of the domain flow, not middleware decoration.

For serious adopters, this keeps the product legible: continuity logic lives in
the continuity slices, policy lives in the policy slice, and protocol adapters
such as MCP stay thin.
