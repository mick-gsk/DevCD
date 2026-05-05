# Getting Started

This guide is the shortest path from a fresh checkout to a visible result.

The fastest product proof is agent continuity: DevCD can generate a local
handoff packet with the current goal, latest failure, stale attempted fix to
avoid, suggested next action, and policy-safe withheld-context summaries.

## Prerequisites

- Python 3.11+
- A local shell on Windows, macOS, or Linux

## 1. Install DevCD

DevCD is pre-alpha. Until a PyPI release is published, install it from a local
checkout:

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
```

## 2. See Agent Continuity In Under Five Minutes

Run the checked-in before/after fixture without starting a daemon:

```bash
devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl
```

Then inspect the machine-readable packet:

```bash
devcd context handoff-demo --events examples/agent-resurrection/sample-events.jsonl --json
```

The JSON contract is documented at `schemas/devcd-agent-handoff-packet.schema.json`; the expected resurrection packet is checked in at `examples/agent-resurrection/handoff-packet.json`.

To turn a local pytest failure report into DevCD events, use the recipe CLI:

```bash
devcd recipe pytest-failure --input examples/event-source-recipes/pytest-failure/input.json
```

## 3. Initialize Local Configuration

```bash
devcd init
```

This creates a local `devcd.toml` with local-first defaults.

## 4. Start the Daemon

```bash
devcd run
```

By default, DevCD listens on `127.0.0.1:8765`.

The daemon requires a local bearer token. If `api_token` is not configured,
DevCD writes one to `.devcd/token` on startup. CLI commands automatically read
`DEVCD_TOKEN` or `.devcd/token` for loopback API calls; direct `curl` calls need
the token header explicitly.

```bash
TOKEN="$(cat .devcd/token)"
```

PowerShell:

```powershell
$env:DEVCD_TOKEN = Get-Content .devcd/token
```

Before or after starting the daemon, you can ask DevCD for a local readiness
snapshot:

```bash
devcd status
devcd doctor
```

`devcd status` reports the daemon endpoint, token source, local workspace,
event/state summary, policy mode, memory path, handoff availability, MCP
availability, and the next suggested command. `devcd doctor` runs the same
local-first readiness checks with concrete next steps; use `devcd doctor --json`
when another local tool needs machine-readable output.

## 5. Submit a First Event

Open a second terminal and send an IDE-style event:

```bash
devcd event ide file_focus --payload '{"path":"src/app.py","duration_seconds":30}'
```

PowerShell:

```powershell
devcd event ide file_focus --payload '{"path":"src/app.py","duration_seconds":30}'
```

## 6. Inspect the Derived State

```bash
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/state
```

You should see a typed state response that reflects the event you just sent.

## 7. Inspect Scoped Memory

```bash
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/memory/working
```

This confirms that DevCD is not only receiving events, but also exposing scoped
memory through its local API surface.

## 8. Ask for an Agent Context Brief

```bash
devcd context brief --surface cli --detail standard
```

The brief is the handoff point for coding agents: a policy-filtered summary of
active intent, relevant artifacts, open loops, recent attempts, and withheld
context.

## Success Criteria

You are done when all of the following are true:

- `devcd run` starts without crashing
- `devcd context handoff-demo --events examples/before-after-agent-continuity/sample-events.jsonl` shows the latest failure, do-not-repeat guidance, and withheld context
- the example event is accepted
- `GET /state` returns structured state instead of an empty or failing response
- `GET /memory/working` responds successfully
- `devcd context brief` returns a policy-filtered brief

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
- run `devcd doctor` for a local readiness report with next steps

If the event succeeds but state looks empty:

- make sure the daemon is still running on `127.0.0.1:8765`
- make sure direct HTTP requests include `Authorization: Bearer <token>`
- resend the sample event and query `/state` again
- inspect your shell output for validation or policy errors
- run `devcd status` to confirm the active workspace, event count, and latest
  event timestamp
