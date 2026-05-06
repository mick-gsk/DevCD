# DevCD Reality Testing Scorecard

Date:
Tester:
Machine/OS:
Repo branch/commit:
DevCD version:

## Session Goals

- [ ] Verify real-world functional correctness
- [ ] Evaluate practical handoff quality
- [ ] Validate policy/security boundaries

## Scenario Matrix

| Scenario | Commands | Expected Signal | Actual Result | Pass/Fail | Notes |
| --- | --- | --- | --- | --- | --- |
| Baseline smoke | `devcd --version`, `devcd smoke --compact` | CLI available, smoke pass |  |  |  |
| Onboarding preview/apply | `devcd onboard --preview`, `devcd onboard --yes` | Clear plan then successful local setup |  |  |  |
| Warm-start handoff | `devcd agentic action-packet`, `devcd context passport` | Usable next action and continuity state |  |  |  |
| Live ingestion | `devcd run`, `devcd event ...` | Event accepted and visible in context |  |  |  |
| Control plane | `devcd context control`, `devcd context budget` | Clear included/withheld/budget guidance |  |  |  |
| Recovery path | `devcd doctor`, `devcd doctor --fix`, `devcd run`, `devcd doctor` | Reproducible diagnosis + recovery |  |  |  |
| Policy boundary | `devcd agentic run --runner codex --json` | Deny by default |  |  |  |
| MCP integration | `devcd integrations openclaw --smoke-test` | Read-only shape pass |  |  |  |

## Quality Metrics

### 1) Utility (30%)

- Time to first useful action in fresh session (minutes):
- Recap-style questions needed (count):
- Rating (0-100):

### 2) Reliability (25%)

- Scenario pass rate (%):
- Workaround count:
- Rating (0-100):

### 3) Recovery (20%)

- Degraded state clearly reported? (yes/no):
- Recovery reproducible? (yes/no):
- Rating (0-100):

### 4) Policy Fidelity (15%)

- Deny-by-default observed? (yes/no):
- Withheld summaries safe and useful? (yes/no):
- Any leakage observed? (yes/no):
- Rating (0-100):

### 5) Integration Readiness (10%)

- OpenClaw smoke test pass? (yes/no):
- MCP shape stable? (yes/no):
- Rating (0-100):

## Weighted Score

```text
Total = Utility*0.30 + Reliability*0.25 + Recovery*0.20 + Policy*0.15 + Integration*0.10
```

Utility:
Reliability:
Recovery:
Policy:
Integration:
Total:

## Findings

### Top Strengths

1.
2.
3.

### Top Gaps

1.
2.
3.

### Severity Triage

- P0 (security/policy boundary):
- P1 (core workflow blocked):
- P2 (guidance/usability drift):
- P3 (minor polish):

## Decision

- [ ] Go for broader real-world usage
- [ ] Go with focused stabilization
- [ ] No-Go until blockers are fixed

Next actions:

1.
2.
3.
