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

## Automated Outcome Evaluation

The manual playbook above gives qualitative signal across the full Phase A-E
lifecycle. The automated outcome eval loop covers four specific regression-prone
failure modes that cannot be detected by unit tests alone.

Run this before any release and after changes to the agentic context, compliance, or
handoff paths.

### Four Failure Modes Under Automated Test

| Mode | What it measures | Pytest target |
| --- | --- | --- |
| Turn-0 recap risk | Does the Action Packet carry enough context that an agent can start without asking "What is your goal?" | `test_action_packet_turn0_risk_*` in `tests/test_agentic_context.py` |
| Incorrect resource choice | Does concise variant carry the required handoff fields? Does the escalation to detailed only trigger when needed? | `test_action_packet_json_includes_turn0_risk_low_after_handoff` in `tests/test_cli.py` |
| Staleness drift | Is a goal older than 24 h flagged with `staleness_flag=true` and a warning in the compliance report? | `test_action_packet_staleness_flag_*` and `test_compliance_json_shows_staleness_warning_for_old_goal` |
| False completion resistance | Does the completion gate warn when an agent claims done without having read the Action Packet in the current session? | `test_completion_check_warns_when_handoff_exists_but_packet_never_read` |

### Automated Eval Commands

Run the targeted outcome eval suite:

```powershell
python -m pytest tests/test_agentic_context.py -q -k "turn0_risk or staleness"
python -m pytest tests/test_cli.py -q -k "eval_signal or consumption_gap or staleness"
```

Run all agentic outcome tests together:

```powershell
python -m pytest tests/test_agentic_context.py tests/test_cli.py tests/test_internal_agentic_benchmark.py -q -k "agentic or completion_check or compliance or staleness or turn0 or eval_signal or consumption"
```

### Outcome Signals in JSON Output

The following signals are now present in `devcd agentic action-packet --json` and
`devcd agentic compliance --json` / `devcd agentic completion-check --json`:

**Action Packet** (`devcd agentic action-packet --json`):

- `turn0_risk`: `"low"` when goal and next action are both present, `"medium"` when only goal is
  available, `"high"` when neither is set.
- `goal_age_seconds`: seconds since the most recent goal capture event in the ledger, or `null`
  when no goal capture exists.
- `staleness_flag`: `true` when `goal_age_seconds >= 86400` (24 h).

**Compliance / Completion Gate** (`devcd agentic compliance --json`):

- `metrics.action_packet_reads`: count of `hook:action-packet.before` events — how many times
  an agent read the Action Packet in this session.
- `completion_gate.signals.turn0_risk`, `staleness_flag`, `goal_age_seconds`,
  `packet_consumed_this_session`: see above.
- `completion_gate.warnings` may include:
  - `consumption_gap`: completion claimed but no Action Packet read recorded.
  - `staleness`: goal older than 24 h with the age in hours.

## Verification Gates

Run these before closing the session:

```powershell
make check
make smoke
make docs
```

Use `make distribution` when evaluating release readiness in the same cycle.
