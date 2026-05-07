# Agentic Complexity Simulation Blueprint

This blueprint provides a practical and repeatable way to simulate DevCD complexity from a user perspective with AI agents.

Use this plan when you want confidence in:

- continuity quality across agent switches,
- policy-safe behavior under pressure,
- user-perceived usefulness under realistic workflows,
- regression detection before releases.

## Goals And Non-Goals

Goals:

- Measure user-facing complexity, not only low-level correctness.
- Compare baseline (no DevCD continuity) against treatment (DevCD-assisted continuity).
- Produce stable signals that can be automated in CI.

Non-goals:

- Replacing slice-level unit and integration tests.
- Publishing benchmark numbers as marketing KPIs.

## Test Matrix

Run all scenarios in two arms:

- `baseline`: same task, no Action Packet or Passport guidance.
- `treatment`: start from `devcd agentic action-packet` and use continuity guidance.

For each scenario, record:

- success or failure,
- time to first useful action,
- recap questions count,
- policy violations,
- retries,
- user-visible friction notes.

## Ten User-Centric Scenarios

1. Cold start onboarding and first useful action
   - Objective: verify a new session reaches useful work without recap.
   - Commands:
     - `devcd setup`
     - `devcd onboard --yes`
     - `devcd agentic action-packet`

2. Mid-task agent switch with active blocker
   - Objective: verify next agent starts from blocker and proposed next action.
   - Commands:
     - `devcd handoff --goal "Fix failing check" --failure "Typecheck fails in policy slice" --next-action "Read latest typecheck output"`
     - `devcd agentic action-packet`

3. Recovery after daemon interruption
   - Objective: verify degraded mode and clean recovery guidance.
   - Commands:
     - `devcd status`
     - `devcd doctor`
     - `devcd doctor --fix`

4. Policy boundary on mutation attempts
   - Objective: verify deny-by-default behavior and explainability.
   - Commands:
     - `devcd agentic run --runner codex --json`
     - `devcd context control --json`

5. Withheld context handling under sensitive events
   - Objective: verify policy-safe summaries without raw leakage.
   - Commands:
     - `devcd capture --kind blocker --summary "Need credential to continue"`
     - `devcd context passport --json`

6. Multi-step bugfix continuity loop
   - Objective: verify attempt/failure/decision capture improves next action quality.
   - Commands:
     - `devcd capture --kind attempt --summary "Reproduced failing test" --outcome failed`
     - `devcd capture --kind decision --summary "Narrowed scope to agentic_context slice"`
     - `devcd agentic action-packet --json`

7. MCP consumer continuity read path
   - Objective: verify read-only continuity resources remain stable.
   - Commands:
     - `devcd integrations openclaw --smoke-test`

8. Context budget pressure simulation
   - Objective: verify contract behavior near rotation thresholds.
   - Commands:
     - `devcd context budget --json`
     - `devcd agentic compliance --json`

9. Session completion gate readiness
   - Objective: verify handoff readiness and completion checks are actionable.
   - Commands:
     - `devcd agentic completion-check`
     - `devcd agentic compliance`

10. End-to-end half-day workflow replay
    - Objective: evaluate utility, reliability, recovery, and policy fidelity together.
    - Commands:
      - follow `docs/devcd/reality-testing.md`
      - collect scorecard and command log

## Scoring Model

Use a 0-100 weighted score:

- Utility: 30
- Reliability: 25
- Recovery: 20
- Policy fidelity: 15
- Integration readiness: 10

Formula:

`total = utility*0.30 + reliability*0.25 + recovery*0.20 + policy*0.15 + integration*0.10`

Recommended additional KPIs for agentic complexity:

- `time_to_first_useful_action_seconds` (median)
- `recap_questions_per_session` (lower is better)
- `policy_explainability_coverage` (ratio of denied/withheld outputs with explicit reasons)
- `resume_success_rate` (fresh session resumes without manual recap)
- `handoff_readiness_rate` (sessions passing completion-check)
- `turn0_risk_rate` (ratio of sessions with `turn0_risk=high` — target: 0)
- `staleness_rate` (ratio of sessions with `staleness_flag=true` — target: 0 before handoff)
- `consumption_gap_rate` (ratio of completion claims without prior action-packet read — target: 0)
- `concise_escalation_rate` (ratio of sessions where agent escalated to detailed unnecessarily — lower is better)

## CI Execution Order

Run these stages in order:

1. Fast contract safety
   - `python -m pytest tests/test_agentic_context.py -q`
   - `python -m pytest tests/test_api.py -q -k "context_control or continuity or action_packet"`

2. Agent continuity behavior
   - `python -m pytest tests/test_cli.py -q -k "agentic or completion_check or compliance or product_intent"`

3. Outcome eval regression gates (new)
   - `python -m pytest tests/test_agentic_context.py -q -k "turn0_risk or staleness"`
   - `python -m pytest tests/test_cli.py -q -k "eval_signal or consumption_gap or staleness"`

4. Real-world scenario subset
   - replay scenarios 2, 4, 6, and 9 from this blueprint with command logs

5. Full repository gates
   - `make check`

6. Documentation integrity
   - `make docs`

## Minimal Automation Harness

Use this lightweight table format to track each run:

| scenario_id | arm | success | ttfua_s | recap_q | policy_violations | retries | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | baseline | false | 240 | 3 | 0 | 2 | asked for recap before starting |
| 2 | treatment | true | 70 | 0 | 0 | 0 | resumed from blocker and next action |

Store run artifacts under `examples/reality-testing/runs/<date>/`:

- `command-log.md`
- `scorecard.md`
- `scenario-matrix.csv`
- `summary.md`

## Operator Notes

- Keep baseline and treatment prompts equivalent.
- Keep agent runtime and permissions equivalent between arms.
- Do not capture raw logs, source content, credentials, or private chat text as continuity metadata.
- If a scenario fails, classify failure first: continuity issue, policy issue, integration issue, or operator setup issue.

## Definition Of Done

A cycle is considered green when:

- all ten scenarios executed in both arms,
- treatment improves at least three of five complexity KPIs,
- no critical policy leakage or mutation-boundary regression,
- `make check` and `make docs` pass.