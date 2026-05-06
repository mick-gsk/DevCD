# Real-World Testing Playbook

This playbook defines a repeatable way to evaluate DevCD under real local
conditions on Windows. It is designed for a half-day run and answers two
questions:

1. Does DevCD function correctly?
2. How good is DevCD in practical agent workflows?

Use this together with the score template in
`examples/reality-testing/scorecard-template.md`.

## Scope

- Environment: local Windows developer machine
- Timebox: about 4 hours
- Focus: real workflows, not synthetic unit-level behavior
- Exclusions: hosted/cloud deployment and long soak tests

## Entry Criteria

Before the session starts, confirm:

- Python and DevCD CLI are installed.
- Workspace is on a known branch and in a known git state.
- You can run local commands in PowerShell.

Recommended baseline commands:

```powershell
devcd --version
devcd smoke --compact
```

## Test Phases

### Phase A: Baseline and Warm-Start

Goal: prove the first-run and handoff path works quickly.

Commands:

```powershell
devcd welcome
devcd onboard --preview
devcd onboard --yes
devcd agentic action-packet
devcd context passport
```

Expected signals:

- Clear next-step guidance in `welcome` and onboarding output.
- Action Packet contains a usable next action.
- Passport reflects current continuity without needing a recap.

Stop conditions:

- Onboard cannot prepare local workspace.
- Action Packet is not usable after onboarding.

### Phase B: Live Runtime and Control Plane

Goal: verify daemon mode, ingestion, and context transparency.

Commands:

```powershell
devcd run
devcd event ide test_passed --payload '{"suite":"reality","case":"live-loop"}'
devcd context control
devcd context budget
```

Expected signals:

- Daemon starts on loopback.
- Event is accepted and reflected in context surfaces.
- Control/budget output is understandable and actionable.

Stop conditions:

- Event ingestion succeeds but context surfaces do not update.
- Control plane does not explain visible/withheld boundaries.

### Phase C: Recovery and Resilience

Goal: prove degraded-mode behavior and clean recovery.

Commands:

```powershell
devcd status
devcd doctor
devcd doctor --fix
devcd run
devcd doctor
```

Expected signals:

- Degraded state is explicit when daemon is down.
- `doctor --fix` applies only safe local repairs.
- Full pass returns after daemon restart.

Stop conditions:

- Recovery path is unclear or non-reproducible.

### Phase D: Policy and Security Boundaries

Goal: validate local-first and deny-by-default behavior.

Commands:

```powershell
devcd agentic run --runner codex --json
devcd integrations openclaw --smoke-test
```

Expected signals:

- Runner start is denied by default unless explicitly configured.
- MCP integration remains read-only and shape checks pass.

Critical failure conditions:

- Unexpected remote export behavior.
- Unexpected write-capable MCP surface.
- Sensitive/raw payload leakage into user-facing context outputs.

### Phase E: Simulated Agent Handoff

Goal: measure practical handoff quality, not only technical correctness.

Procedure:

1. End one working session with `devcd handoff` or `devcd capture` metadata.
2. Start a fresh session using only `devcd agentic action-packet` and
   `devcd context passport`.
3. Measure time to first useful action and number of recap-style questions.

Pass signal:

- Fresh session starts productively from packet/passport without full recap.

## Quality Score (0-100)

Score DevCD with weighted dimensions:

- 30% Utility: Fresh session reaches first useful action quickly.
- 25% Reliability: Scenario pass rate without manual workarounds.
- 20% Recovery: Degraded mode and recovery are reproducible.
- 15% Policy fidelity: deny/withheld/read-only behavior is correct.
- 10% Integration readiness: MCP/OpenClaw smoke path is stable.

Formula:

```text
Total = Utility*0.30 + Reliability*0.25 + Recovery*0.20 + Policy*0.15 + Integration*0.10
```

Interpretation:

- 90-100: production-like confidence for local workflows
- 75-89: strong pre-alpha behavior with focused polish needs
- 60-74: usable but requires stabilization before broad adoption
- below 60: address blockers before wider rollout

## Minimal Evidence Pack

Collect these artifacts per run:

- Command log (executed commands + key outputs)
- Completed scorecard
- Top 3 strengths
- Top 3 improvements
- Go/No-Go recommendation for broader team usage

## Verification Gates

Run these before closing the session:

```powershell
make check
make smoke
make docs
```

Use `make distribution` when evaluating release readiness in the same cycle.
