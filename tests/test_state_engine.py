from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
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


def test_duplicate_event_id_is_denied_without_reapplying_state() -> None:
    engine = build_engine()
    event = DevEvent(
        event_id="dup-1",
        source=EventSource.IDE,
        type="file_focus",
        payload={"path": "src/app.py", "duration_seconds": 2},
    )

    first_decision = engine.accept_event(event)
    second_decision = engine.accept_event(event)

    assert first_decision.allowed
    assert not second_decision.allowed
    assert second_decision.operation == "dedupe"
    assert engine.state.attention_score["src/app.py"] == 2
    assert len(engine.state.recent_actions) == 1


def test_file_focus_events_are_coalesced_within_window() -> None:
    engine = build_engine()
    started_at = datetime(2026, 5, 4, 12, 0, tzinfo=UTC)

    first_event = DevEvent(
        event_id="focus-1",
        source=EventSource.IDE,
        type="file_focus",
        timestamp=started_at,
        payload={"path": "src/app.py", "duration_seconds": 2},
    )
    second_event = DevEvent(
        event_id="focus-2",
        source=EventSource.IDE,
        type="file_focus",
        timestamp=started_at + timedelta(milliseconds=200),
        payload={"path": "src/app.py", "duration_seconds": 3},
    )

    engine.accept_event(first_event)
    engine.accept_event(second_event)

    assert engine.state.attention_score["src/app.py"] == 5
    assert len(engine.state.recent_actions) == 1
    assert engine.state.recent_actions[0].summary == "file_focus: src/app.py"


def test_branch_focus_and_failure_events_populate_work_state_fields() -> None:
    engine = build_engine()

    engine.accept_event(
        DevEvent(
            event_id="branch-1",
            source=EventSource.GIT,
            type="branch_change",
            payload={"branch": "feature/context-daemon"},
        )
    )
    engine.accept_event(
        DevEvent(
            event_id="focus-3",
            source=EventSource.IDE,
            type="file_focus",
            payload={"path": "src/app.py", "duration_seconds": 4},
        )
    )
    engine.accept_event(
        DevEvent(
            event_id="fail-1",
            source=EventSource.GIT,
            type="test_failure",
            payload={"reason": "unit tests failed"},
        )
    )

    assert engine.state.current_goal == "feature/context-daemon"
    assert engine.state.subtask == "src/app.py"
    assert engine.state.blocked_by == "unit tests failed"
    assert engine.state.interruptibility == "low"
    assert "investigate failing tests" in engine.state.next_best_actions
    assert engine.state.source_active_map == {"git": True, "ide": True}
    assert len(engine.state.recent_actions) == 3


def test_success_event_clears_failure_blocker_state() -> None:
    engine = build_engine()

    engine.accept_event(
        DevEvent(
            event_id="fail-2",
            source=EventSource.GIT,
            type="test_failure",
            payload={"reason": "unit tests failed"},
        )
    )
    engine.accept_event(
        DevEvent(
            event_id="pass-1",
            source=EventSource.GIT,
            type="test_passed",
            payload={"suite": "unit"},
        )
    )

    assert engine.state.blocked_by is None
    assert engine.state.interruptibility == "high"
    assert engine.state.next_best_actions == []


def test_state_rebuilds_from_ledger_after_restart(tmp_path: Path) -> None:
    ledger_path = tmp_path / "events.jsonl"
    first_engine = StateEngine(
        policy_engine=PolicyEngine.default(),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger(ledger_path),
    )
    first_engine.accept_event(
        DevEvent(
            event_id="restart-1",
            source=EventSource.GIT,
            type="branch_change",
            payload={"branch": "feature/restart"},
        )
    )

    restarted_engine = StateEngine(
        policy_engine=PolicyEngine.default(),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger(ledger_path),
    )
    restarted_engine.rebuild_from_ledger()

    assert restarted_engine.state.current_goal == "feature/restart"
    assert restarted_engine.state.recent_actions[0].summary == "branch_change: feature/restart"


def test_truncated_ledger_tail_is_ignored_during_rebuild(tmp_path: Path) -> None:
    ledger_path = tmp_path / "events.jsonl"
    valid_engine = StateEngine(
        policy_engine=PolicyEngine.default(),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger(ledger_path),
    )
    valid_engine.accept_event(
        DevEvent(
            event_id="restart-2",
            source=EventSource.GIT,
            type="branch_change",
            payload={"branch": "feature/truncated"},
        )
    )
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write('{"event": ')

    restarted_engine = StateEngine(
        policy_engine=PolicyEngine.default(),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger(ledger_path),
    )
    restarted_engine.rebuild_from_ledger()

    assert restarted_engine.state.current_goal == "feature/truncated"


def test_disabled_source_is_hidden_from_state_and_memory_views_after_rebuild(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "events.jsonl"
    visible_engine = StateEngine(
        policy_engine=PolicyEngine.default(),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger(ledger_path),
    )
    visible_engine.accept_event(
        DevEvent(
            event_id="hidden-1",
            source=EventSource.IDE,
            type="file_focus",
            payload={"path": "src/hidden.py", "duration_seconds": 2},
        )
    )

    hidden_engine = StateEngine(
        policy_engine=PolicyEngine(
            allow_observation=True,
            allow_local_storage=True,
            allow_remote_export=False,
            allow_actions=False,
            enabled_sources={"git", "task", "notes", "system"},
            allowed_data_classes={"metadata"},
        ),
        memory_store=MemoryStore.with_default_ttl(),
        event_ledger=EventLedger(ledger_path),
    )
    hidden_engine.rebuild_from_ledger()

    assert hidden_engine.state.recent_actions == []
    assert hidden_engine.state.source_active_map == {"ide": False}
    assert (
        hidden_engine.memory_store.list_by_scope(
            MemoryScope.WORKING,
            hidden_engine.is_source_visible,
        )
        == []
    )
