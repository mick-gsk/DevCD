from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSource, SubtaskCompletionEvent
from devcd.slices.policy_layer.models import PolicyDecision, PolicyDecisionKind


def test_event_ledger_persists_subtask_completion_event_append_only(tmp_path: Path) -> None:
    ledger_path = tmp_path / "events.jsonl"
    ledger = EventLedger(ledger_path)
    decision = PolicyDecision(
        kind=PolicyDecisionKind.ALLOW,
        reason="local storage is allowed by policy",
        operation="store",
        source="task",
        data_class="metadata",
    )

    ledger.append(
        SubtaskCompletionEvent(
            event_type="subtask_completion",
            subtask_id="task-001",
            status="complete",
            completion_marker="done",
            timestamp=datetime(2026, 5, 7, 12, 0, tzinfo=UTC),
        ),
        decision,
    )
    ledger.append(
        SubtaskCompletionEvent(
            event_type="subtask_completion",
            subtask_id="task-002",
            status="incomplete",
            completion_marker="pending",
            timestamp=datetime(2026, 5, 7, 12, 1, tzinfo=UTC),
        ),
        decision,
    )

    persisted = ledger.read_subtask_completion_events()
    lines = ledger_path.read_text(encoding="utf-8").splitlines()

    assert [event.subtask_id for event in persisted] == ["task-001", "task-002"]
    assert len(lines) == 2


def test_event_ledger_read_records_is_lenient_for_unknown_event_shapes(tmp_path: Path) -> None:
    ledger_path = tmp_path / "events.jsonl"
    unknown_record = {
        "event": {
            "event_type": "unknown_future_event",
            "payload": {"x": 1},
        },
        "policy_decision": {
            "kind": "allow",
            "reason": "local storage is allowed by policy",
            "operation": "store",
        },
    }
    valid_record = {
        "event": DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            payload={"current_goal": "Ship ledger hardening"},
            timestamp=datetime(2026, 5, 7, 12, 2, tzinfo=UTC),
        ).model_dump(mode="json"),
        "policy_decision": {
            "kind": "allow",
            "reason": "local storage is allowed by policy",
            "operation": "store",
            "source": "task",
            "data_class": "metadata",
        },
    }
    ledger_path.write_text(
        "\n".join([json.dumps(unknown_record), json.dumps(valid_record)]) + "\n",
        encoding="utf-8",
    )

    records = EventLedger(ledger_path).read_records()

    assert len(records) == 1
    assert records[0][0].type == "goal_update"
