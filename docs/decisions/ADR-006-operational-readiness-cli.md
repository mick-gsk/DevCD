---
id: ADR-006
status: proposed
date: 2026-05-04
supersedes: null
---

# Operational Readiness CLI

## Context

DevCD has local daemon, policy, context handoff, and MCP surfaces, but a fresh
checkout does not yet have one command that tells a developer whether the local
context runtime is ready. Users need a quick local diagnosis that reports daemon
reachability, token/config state, event/state freshness, policy safety, handoff
availability, and concrete next steps without sending data anywhere.

## Decision

Add two top-level CLI commands backed by existing slice services:

- `devcd status` renders a concise local runtime snapshot for humans.
- `devcd doctor` runs local operational checks and renders human output.
- `devcd doctor --json` emits the same checks as stable machine-readable JSON.

Implementation note, 2026-05-05: these commands exist in the current codebase.
The ADR remains `proposed` until a maintainer explicitly accepts the decision.

The commands compose `DevCDSettings`, `EventLedger`, `StateEngine`,
`AmbientContextService`, `PolicyEngine`, and the read-only MCP service. They do
not introduce a new slice in the first implementation because they do not own a
new domain model; they orchestrate existing local read paths for CLI diagnosis.
If future work exposes readiness through HTTP or persists readiness history, the
logic can be extracted into an owning slice.

All checks are local-first. They do not perform remote export, telemetry, or
network calls beyond optional loopback daemon probes. State-changing checks are
limited to clearly named safe checks that run in memory or a temporary directory,
such as validating the handoff demo against local JSONL sample events.

## Non-Goals

- Do not add remote export, telemetry, or outbound network calls.
- Do not auto-start the daemon, create tokens, or mutate user configuration.
- Do not add a readiness HTTP API in this phase.
- Do not bypass existing policy, context, state, memory, or MCP boundaries.

## Alternatives Considered

1. Add a new `operational_readiness` slice immediately. This creates a clear
   ownership boundary, but it is premature while the feature only reads and
   composes existing slice services from the CLI.
2. Hide readiness under `devcd context`. That avoids a new top-level command but
   makes first-run diagnostics harder to discover.
3. Add top-level CLI commands with small typed helpers. This matches the product
   goal, keeps the first implementation focused, and preserves a future extract
   path if readiness becomes a broader product surface.

## Consequences

The CLI gains a stable operational surface that can be used by humans and local
automation. `doctor --json` becomes a contract for local tooling, so the check
objects must stay machine-readable and avoid leaking raw sensitive payloads. The
implementation must keep sensitive policy samples synthetic and local.

## Validation

Implementation must add or update these checks:

```bash
pytest tests/test_cli.py::test_status_reports_no_daemon_with_next_step -v
pytest tests/test_cli.py::test_status_reports_local_demo_state -v
pytest tests/test_cli.py::test_doctor_reports_missing_token_and_config -v
pytest tests/test_cli.py::test_doctor_json_verifies_sensitive_policy_denial -v
pytest tests/test_cli.py::test_doctor_validates_handoff_demo -v
make check
```

Expected outcomes:

- `devcd status` clearly reports unreachable daemon state without failing;
- local ledger/demo state is summarized when present;
- `devcd doctor` reports missing config/token with actionable next steps;
- sensitive sample policy denial is verified without exposing payload content;
- the handoff sample JSONL remains valid and can generate a local handoff;
- the full repository check continues to pass.
