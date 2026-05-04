# Event Source Recipes

Event source recipes are small local adapters that turn concrete workflow signals into DevCD events. They do not run tools, upload data, or synchronize remotely. A recipe should emit policy-safe metadata by default and mark raw or sensitive material so the policy layer can deny storage/export and expose only a safe withheld-context summary.

## Pytest Failure Recipe

The first recipe turns a local pytest failure report into DevCD events for agent handoff:

- a `task/test_failure` metadata event that can update work state, blockers, recent attempts, and suggested next action;
- a `task/test_output` sensitive event when raw stdout or stderr is present, so raw test output is policy-gated and not persisted by default.

The recipe lives in `devcd.slices.events.recipes` and is intentionally a library function. It does not require a VS Code extension, CI integration, GitHub app, or remote service.

### Example Input

See `examples/event-source-recipes/pytest-failure/input.json`:

```json
{
  "command": "pytest tests/test_checkout.py -q",
  "exit_code": 1,
  "timestamp": "2026-05-04T12:00:00Z",
  "failures": [
    {
      "nodeid": "tests/test_checkout.py::test_total",
      "file_path": "tests/test_checkout.py",
      "line": 42
    }
  ],
  "stderr": "E   AssertionError: PRIVATE_TEST_OUTPUT"
}
```

### Example DevCD Events

See `examples/event-source-recipes/pytest-failure/events.jsonl`:

```json
{"source":"task","type":"test_failure","timestamp":"2026-05-04T12:00:00Z","payload":{"recipe":"pytest_failure","command":"pytest tests/test_checkout.py -q","exit_code":1,"failure_count":1,"failed_nodeids":["tests/test_checkout.py::test_total"],"first_failure":{"nodeid":"tests/test_checkout.py::test_total","file_path":"tests/test_checkout.py","line":42},"reason":"pytest failed: tests/test_checkout.py::test_total","suggested_next_action":"Rerun pytest tests/test_checkout.py::test_total -q and inspect tests/test_checkout.py:42"}}
{"source":"task","type":"test_output","timestamp":"2026-05-04T12:00:00Z","payload":{"recipe":"pytest_failure","output":"E   AssertionError: PRIVATE_TEST_OUTPUT"},"sensitivity":"sensitive"}
```

The first event is metadata and may be shown in a policy-allowed context brief. The second event carries raw output and is denied by the default policy. The handoff packet can then show `Last failure` and `Suggested next action` while the raw pytest output appears only as withheld context.

### Python Usage

```python
from devcd.slices.events.recipes import PytestFailure, PytestFailureRecipeInput, events_from_pytest_failure

events = events_from_pytest_failure(
    PytestFailureRecipeInput(
        command="pytest tests/test_checkout.py -q",
        exit_code=1,
        failures=[PytestFailure(nodeid="tests/test_checkout.py::test_total")],
        stderr="E   AssertionError: PRIVATE_TEST_OUTPUT",
    )
)
```

Feed the resulting events through `StateEngine.accept_event(...)` so normal policy, ledger, memory, and ambient-context behavior applies.