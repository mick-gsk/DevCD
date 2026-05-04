from __future__ import annotations

import json
from pathlib import Path

from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSensitivity, EventSource
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.models import MemoryScope
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine


def build_engine() -> StateEngine:
    return StateEngine(
        policy_engine=PolicyEngine.default(),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger.disabled(),
    )


def test_file_focus_event_updates_attention_score() -> None:
    engine = build_engine()
    event = DevEvent(
        source=EventSource.IDE,
        type="file_focus",
        payload={"path": "src/app.py", "duration_seconds": 12},
    )

    decision = engine.accept_event(event)

    assert decision.allowed
    assert engine.state.attention_score["src/app.py"] == 12
    assert engine.state.recent_actions[0].policy_reason == decision.reason


def test_sensitive_event_is_denied_and_not_stored() -> None:
    engine = build_engine()
    event = DevEvent(
        source=EventSource.NOTES,
        type="note_update",
        payload={"body": "private"},
        sensitivity=EventSensitivity.SENSITIVE,
    )

    decision = engine.accept_event(event)

    assert not decision.allowed
    assert engine.state.recent_actions == []
    assert engine.memory_store.list_by_scope(MemoryScope.WORKING) == []


def test_accepted_event_is_written_to_jsonl_ledger(tmp_path: Path) -> None:
    ledger_path = tmp_path / "events.jsonl"
    engine = StateEngine(
        policy_engine=PolicyEngine.default(),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger(ledger_path),
    )
    event = DevEvent(
        source=EventSource.GIT,
        type="branch_change",
        payload={"branch": "feature/context-daemon"},
    )

    decision = engine.accept_event(event)
    record = json.loads(ledger_path.read_text(encoding="utf-8").splitlines()[0])

    assert decision.allowed
    assert record["event"]["type"] == "branch_change"
    assert record["policy_decision"]["reason"] == "local storage is allowed by policy"


def test_storage_policy_can_disable_ledger_and_memory(tmp_path: Path) -> None:
    ledger_path = tmp_path / "events.jsonl"
    engine = StateEngine(
        policy_engine=PolicyEngine(
            allow_observation=True,
            allow_local_storage=False,
            allow_remote_export=False,
            allow_actions=False,
        ),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger(ledger_path),
    )
    event = DevEvent(
        source=EventSource.IDE,
        type="file_focus",
        payload={"path": "src/app.py", "duration_seconds": 3},
    )

    decision = engine.accept_event(event)

    assert decision.allowed
    assert engine.state.attention_score["src/app.py"] == 3
    assert not ledger_path.exists()
    assert engine.memory_store.list_by_scope(MemoryScope.WORKING) == []
