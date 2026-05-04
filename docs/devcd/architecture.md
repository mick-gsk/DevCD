# DevCD Architecture

DevCD is a local daemon with three explicit responsibilities: observe developer events, update an in-memory work-state tree, and expose state/memory to trusted local clients.

## Monorepo Layout

```text
packages/devcd-core/src/devcd/
  kernel/                  shared primitives only
  slices/
    events/                normalized event contract
    host_state_engine/     state tree and API routes
    memory_layer/          working, episodic, semantic memory
    policy_layer/          observation/action authorization
```

## Runtime Flow

```text
source event -> policy decision -> ledger append -> state update -> memory update
```

The MVP keeps the state tree in memory and appends accepted events to a local JSON Lines ledger. Later versions can replace the persistence adapter with SQLite without changing the slice contracts.

## Vertical Slice Rules

- A slice owns its public models and service behavior.
- Cross-slice calls go through public service interfaces.
- Shared kernel code must stay framework-light and deterministic.
- Policy decisions are part of the domain flow, not middleware decoration.
