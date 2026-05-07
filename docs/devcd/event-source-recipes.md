# Event Source Recipes

Event source recipes are small local adapters that turn concrete workflow signals into DevCD events. They do not run tools, upload data, or synchronize remotely. A recipe should emit policy-safe metadata by default and mark raw or sensitive material so the policy layer can deny storage/export and expose only a safe withheld-context summary.

## Pytest Failure Recipe

The first recipe turns a local pytest failure report into DevCD events for agent handoff:

- a `task/test_failure` metadata event that can update work state, blockers, recent attempts, and suggested next action;
- a `task/test_output` sensitive event when raw stdout or stderr is present, so raw test output is policy-gated and not persisted by default.

The recipe lives in `devcd.slices.events.recipes` and is intentionally a library function. It does not require a VS Code extension, CI integration, GitHub app, or remote service.

The same converter is exposed through the local CLI:

```bash
devcd recipe pytest-failure --input examples/event-source-recipes/pytest-failure/input.json
```

The command prints DevCD JSONL events to stdout. It marks raw stdout/stderr as a
sensitive `task/test_output` event so normal policy handling can withhold raw
output from handoff packets.

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

## Manual Event Classes For Continuity Curation

DevCD also supports explicit event classes on normal `POST /event` submissions
for continuity curation workflows. These are metadata-only and developer-triggered.
DevCD does not auto-emit them from chat text or command output.

- `event_class: "dead_end"` marks a non-retriable approach and requires payload
  fields: `approach_summary`, `reason`, `related_goal`.
- `event_class: "goal.done_when"` records explicit completion criteria and
  requires payload field: `done_when`.

When policy allows storage, these event classes flow into memory-layer context
so Action Packets can expose `rejected_paths` and a verification-aware
`session_contract`.

## Research Session Recipe

The research-session recipe turns a local research export into DevCD events for the Research Context Pack. It accepts structured metadata as the safe path: research goal, reviewed source titles and references, source type, note titles or summaries, hypotheses, decisions, failed attempts, why attempts failed, and a suggested next step.

Raw note text, article text, transcript text, and full content can be present in the input, but the recipe emits those as sensitive/full-text events so the default policy withholds them from agent-facing output. The recipe does not scrape browsers, import private notes directly, call remote APIs, or add telemetry.

```bash
devcd recipe research-session --input examples/event-source-recipes/research-session/input.json --output research-events.jsonl
devcd context handoff-demo --events research-events.jsonl --surface research-agent --pack research
```

For the live Agent Passport path, feed the emitted events through normal local ingestion so DevCD records policy decisions in the configured ledger, then run:

```bash
devcd context passport --surface research-agent --pack research
```

The checked-in input at `examples/event-source-recipes/research-session/input.json` includes synthetic raw text fields to demonstrate withholding. Those raw fields must not appear in the Research Continuity Packet.