from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSource
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine


def test_dead_end_event_is_accepted_and_stored(tmp_path: Path) -> None:
    policy_engine = PolicyEngine.default()
    memory_store = MemoryStore.with_ttl_seconds(315360000)
    event_ledger = EventLedger(tmp_path / "events.jsonl")
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)

    event = DevEvent(
        source=EventSource.TASK,
        type="failed_attempt",
        event_class="dead_end",
        timestamp=datetime(2026, 5, 7, 12, 0, tzinfo=UTC),
        payload={
            "approach_summary": "Retry unchanged patch logic",
            "reason": "Same assertion branch failed repeatedly",
            "related_goal": "Stabilize action packet contract",
        },
    )

    decision = state_engine.accept_event(event)
    records = event_ledger.read_records()

    assert decision.allowed is True
    assert len(records) == 1
    stored_event = records[0][0]
    assert stored_event.event_class == "dead_end"
    assert stored_event.payload["approach_summary"] == "Retry unchanged patch logic"


def test_dead_end_event_requires_approach_summary_and_reason() -> None:
    with pytest.raises(ValidationError):
        DevEvent(
            source=EventSource.TASK,
            type="failed_attempt",
            event_class="dead_end",
            timestamp=datetime(2026, 5, 7, 12, 0, tzinfo=UTC),
            payload={
                "related_goal": "Stabilize action packet contract",
            },
        )
