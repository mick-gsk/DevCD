# DevCD Architecture

DevCD is a local daemon with three explicit responsibilities: observe developer events, update an in-memory work-state tree, and expose state/memory to trusted local clients.

The MVP trust boundary is loopback-only plus a local bearer token. Requests that do not target loopback hosts or do not present the configured token are denied before state, memory, or ledger behavior runs.

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
```

## Runtime Flow

```text
source event -> auth + loopback check -> policy decision -> ledger append -> state update -> memory update
```

The MVP keeps the state tree in memory and appends storage-approved events to a local JSON Lines ledger. Later versions can replace the persistence adapter with SQLite without changing the slice contracts.

On startup, DevCD replays ledger records to rebuild visible state and repopulate working and episodic memory. A truncated trailing JSONL line is ignored so interrupted writes do not corrupt restart recovery.

Runtime settings are loaded from `devcd.toml` or `DEVCD_` environment variables. Defaults are local-first: observation enabled, local storage enabled, remote export disabled, actions disabled.

High-frequency IDE events such as `file_focus` and `cursor_move` are coalesced within a short configured window before they fan out into recent actions. This keeps the visible state stable while preserving aggregated attention signals.

Read-time visibility for disabled sources is decided in `policy_layer` and consumed by state and memory reads. Audit metadata may remain in the ledger for retention and replay purposes, while active `/state` and `/memory/*` responses hide disabled-source context.

## Vertical Slice Rules

- A slice owns its public models and service behavior.
- Cross-slice calls go through public service interfaces.
- Shared kernel code must stay framework-light and deterministic.
- Policy decisions are part of the domain flow, not middleware decoration.
