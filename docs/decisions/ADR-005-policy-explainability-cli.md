---
id: ADR-005
status: proposed
date: 2026-05-04
supersedes: null
---

# Product-Facing Policy Explainability CLI

## Context

DevCD already records policy reasons and withholds sensitive context, but the
policy layer is mostly visible as internal model fields. Users and agents need a
stable local interface that explains why context is visible or withheld without
revealing the raw sensitive payload that caused a denial.

## Decision

Add product-facing policy explainability to the existing policy layer and CLI:

- `devcd policy explain <decision-id>` reads a local ledger decision and renders
  a safe explanation.
- `devcd policy simulate --surface <surface> --event <file>` evaluates an event
  against the local policy for the selected context surface without mutating the
  state engine, memory store, or event ledger.
- Both commands support machine-readable JSON output and human-readable output.
- Denied or withheld context explanations include the policy reason, category,
  and a safe replacement summary when one can be produced from source/type
  metadata.

The implementation remains local-first. Simulation only validates the input
event and calls policy decisions in memory; it does not append to the ledger,
store memory, or apply host state.

## Non-Goals

- Do not add remote export, telemetry, or action execution.
- Do not add a second policy engine or move surface ownership out of existing
  slices.
- Do not expose raw sensitive payload values in explainability output.
- Do not make simulation an audit log entry unless a future accepted ADR adds
  an explicit audit requirement.

## Alternatives Considered

1. Expose explainability only through HTTP endpoints. This would require a
   running daemon and token for local diagnostics, making the first product
   surface less ergonomic.
2. Reuse `context handoff-demo` only. That explains final agent context, but it
   does not explain a single policy decision or simulate a pending event.
3. Add a small policy CLI backed by typed policy-layer report models. This keeps
   the boundary narrow and makes behavior testable without state mutation.

## Consequences

The policy layer gains typed report models for explanations and simulation
results. Newly recorded policy decisions include identifiers, while older ledger
records remain model-readable but may not be addressable through `explain` if no
decision identifier was recorded. Users receive a safe explanation of withheld
context, while agents can consume the same result as JSON.

## Validation

Implementation must add or update these checks:

```bash
pytest tests/test_policy_layer.py::test_policy_simulation_denies_sensitive_event_with_safe_summary -v
pytest tests/test_cli.py::test_policy_simulate_outputs_json_and_human_explanation -v
pytest tests/test_cli.py::test_policy_explain_reads_decision_from_ledger_as_json_and_text -v
make check
```

Expected outcomes:

- a sensitive event fixture simulated for a context surface is denied and
  represented as withheld;
- explain and simulate outputs name policy reason, affected category, and safe
  replacement information;
- simulation reports that it does not mutate state;
- the full repository check continues to pass.