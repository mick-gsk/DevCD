# Getting Started

This guide is the shortest path from a fresh install to a visible result.

The goal is simple: start DevCD, send one event, and confirm that the daemon now
holds structured state you can query locally.

## Prerequisites

- Python 3.11+
- A local shell on Windows, macOS, or Linux

## 1. Install DevCD

```bash
pip install devcd
```

## 2. Initialize Local Configuration

```bash
devcd init
```

This creates a local `devcd.toml` with local-first defaults.

## 3. Start the Daemon

```bash
devcd run
```

By default, DevCD listens on `127.0.0.1:8765`.

## 4. Submit a First Event

Open a second terminal and send an IDE-style event:

```bash
devcd event ide file_focus --payload '{"path":"src/app.py","duration_seconds":30}'
```

## 5. Inspect the Derived State

```bash
curl http://127.0.0.1:8765/state
```

You should see a typed state response that reflects the event you just sent.

## 6. Inspect Scoped Memory

```bash
curl http://127.0.0.1:8765/memory/working
```

This confirms that DevCD is not only receiving events, but also exposing scoped
memory through its local API surface.

## Success Criteria

You are done when all of the following are true:

- `devcd run` starts without crashing
- the example event is accepted
- `GET /state` returns structured state instead of an empty or failing response
- `GET /memory/working` responds successfully

## Why This Matters

The point of this flow is not just to prove that a local daemon can run. It is
to verify the core DevCD promise: context can be observed once, stored locally,
and queried later without repeating it manually.

## Common Next Steps

- Read [Use Cases](use-cases.md) to map DevCD to real workflows
- Read [Architecture Overview](devcd/architecture.md) to understand the slice
  boundaries
- Read [Policy Layer](devcd/policy.md) if you care about explainable local
  trust boundaries

## Troubleshooting

If the daemon does not start:

- confirm Python 3.11+ is active
- confirm `devcd` is available in your shell after installation
- rerun `devcd init` to regenerate local config defaults

If the event succeeds but state looks empty:

- make sure the daemon is still running on `127.0.0.1:8765`
- resend the sample event and query `/state` again
- inspect your shell output for validation or policy errors