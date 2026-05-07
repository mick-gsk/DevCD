# Internal Benchmark Runbook

Status: Internal-only. Not a product KPI and not a public CLI feature.

Purpose: Reproducibly compare a cold-start run against a DevCD-assisted run using local capture metadata.

## Scope And Rules

- Use this only for internal evaluation.
- Keep runs local-first and policy-compliant.
- Do not present these numbers as public product metrics.
- Use identical task prompts, model family, and tool permissions for both arms.

## Prerequisites

- Repository root active.
- Dev dependencies installed.
- Fresh or known runtime ledger.

Optional reset for a clean trial:

```powershell
Remove-Item -Path .devcd/events.jsonl -Force -ErrorAction SilentlyContinue
```

## Trial Design

Two session labels are required:

- Baseline session label: cold
- Treatment session label: devcd

Recommended minimum:

- At least 10 tasks total.
- Mixed bugfix and small feature tasks.
- Same timebox per task.

## Capture During Runs

For each task step, capture attempt metadata with the session label.

Baseline example:

```powershell
python -m devcd capture --kind attempt --summary "cold task attempt" --outcome failed --session cold
python -m devcd capture --kind attempt --summary "cold retry" --outcome succeeded --session cold
```

Treatment example:

```powershell
python -m devcd capture --kind attempt --summary "devcd task attempt" --outcome succeeded --session devcd
python -m devcd capture --kind decision --summary "used action packet guidance" --session devcd
```

## Run The Internal Benchmark Script

JSON output:

```powershell
python scripts/internal_agentic_benchmark.py --baseline-session cold --treatment-session devcd --config devcd.toml --json
```

Text output:

```powershell
python scripts/internal_agentic_benchmark.py --baseline-session cold --treatment-session devcd --config devcd.toml
```

## Output Interpretation

Key fields:

- success_rate_delta: treatment minus baseline.
- failed_attempts_delta: treatment minus baseline. Lower is better.
- elapsed_seconds_delta: treatment minus baseline. Lower is better.
- verdict:
  - improved: better quality and not slower.
  - mixed: quality improved but slower.
  - regressed: quality did not improve.

## Quality Checklist

- Both session labels have capture events.
- Baseline and treatment used equivalent task sets.
- No hidden prompt differences between arms.
- Full repository validation still passes after experiment:

```powershell
make check
```

## Troubleshooting

No capture events found for session:

- Ensure --session value matches exactly in capture commands and benchmark command.
- Ensure the same config and runtime directory are used for capture and benchmark execution.

Unexpected deltas:

- Verify equal task difficulty and timebox.
- Increase sample size.
- Remove outlier tasks and rerun.
