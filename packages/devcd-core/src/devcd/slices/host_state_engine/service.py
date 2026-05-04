from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent
from devcd.slices.host_state_engine.models import DevState, RecentAction
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.models import PolicyDecision, PolicyDecisionKind
from devcd.slices.policy_layer.service import PolicyEngine


class StateEngine:
    def __init__(
        self,
        policy_engine: PolicyEngine,
        memory_store: MemoryStore,
        event_ledger: EventLedger,
        coalesce_window_ms: int = 500,
    ) -> None:
        self._policy_engine = policy_engine
        self._memory_store = memory_store
        self._event_ledger = event_ledger
        self._state = DevState()
        self._seen_event_ids: set[str] = set()
        self._coalesce_window = timedelta(milliseconds=coalesce_window_ms)
        self._last_coalesced_key: tuple[str, str, str] | None = None
        self._last_coalesced_timestamp: datetime | None = None

    @property
    def state(self) -> DevState:
        visible_state = self._state.model_copy(deep=True)
        visible_state.recent_actions = [
            action
            for action in visible_state.recent_actions
            if self.is_source_visible(action.source)
        ]
        visible_state.source_active_map = {
            source: self.is_source_visible(source)
            for source in visible_state.source_active_map
        }
        return visible_state

    @property
    def memory_store(self) -> MemoryStore:
        return self._memory_store

    def accept_event(self, event: DevEvent) -> PolicyDecision:
        if event.event_id in self._seen_event_ids:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="duplicate event delivery was ignored",
                operation="dedupe",
                source=event.source.value,
            )

        decision = self._policy_engine.decide_observation(event)
        if not decision.allowed:
            return decision

        self._seen_event_ids.add(event.event_id)
        self._state.source_active_map[event.source.value] = self._policy_engine.is_source_visible(
            event.source.value
        )

        storage_decision = self._policy_engine.decide_local_storage(event)
        if storage_decision.allowed:
            self._event_ledger.append(event=event, decision=storage_decision)
            self._store_event_memory(event, decision, storage_decision.reason)
        self._apply_event(event=event, decision=decision)
        return decision

    def rebuild_from_ledger(self) -> None:
        for event, decision in self._event_ledger.read_records():
            self._seen_event_ids.add(event.event_id)
            self._state.source_active_map[event.source.value] = (
                self._policy_engine.is_source_visible(event.source.value)
            )
            self._store_event_memory(event, decision, decision.reason)
            self._apply_event(event=event, decision=decision)

    def is_source_visible(self, source: str | None) -> bool:
        return self._policy_engine.is_source_visible(source)

    def _store_event_memory(
        self,
        event: DevEvent,
        observation_decision: PolicyDecision,
        storage_reason: str,
    ) -> None:
        content = {
            "source": event.source.value,
            "type": event.type,
            "payload": event.payload,
            "observation_policy_reason": observation_decision.reason,
            "storage_policy_reason": storage_reason,
        }
        self._memory_store.add_working(
            content,
            source=event.source.value,
            policy_reason=storage_reason,
            timestamp=event.timestamp,
        )
        self._memory_store.add_episodic(
            content,
            source=event.source.value,
            policy_reason=storage_reason,
            timestamp=event.timestamp,
        )

    def _apply_event(self, event: DevEvent, decision: PolicyDecision) -> None:
        payload = event.payload
        if not self._coalesce_recent_action(event, decision):
            self._state.recent_actions.insert(
                0,
                RecentAction(
                    timestamp=event.timestamp,
                    source=event.source.value,
                    type=event.type,
                    summary=self._summarize_event(event.type, payload),
                    policy_reason=decision.reason,
                ),
            )
            self._state.recent_actions = self._state.recent_actions[:20]

        if event.type == "goal_update":
            self._state.current_goal = self._optional_string(payload.get("current_goal"))
            self._state.subtask = self._optional_string(payload.get("subtask"))
            self._state.confidence["current_goal"] = 1.0
            self._clear_blocker_state()
        elif event.type == "branch_change":
            branch = self._optional_string(payload.get("branch"))
            if branch is not None:
                self._state.current_goal = branch
                self._state.confidence["current_goal"] = 0.6
        elif event.type == "file_focus":
            file_path = self._optional_string(payload.get("path"))
            duration_seconds = self._optional_float(payload.get("duration_seconds"), default=1.0)
            if file_path is not None:
                self._state.attention_score[file_path] = (
                    self._state.attention_score.get(file_path, 0.0) + duration_seconds
                )
                self._state.subtask = file_path
                self._state.confidence["subtask"] = 0.5
        elif event.type == "test_fail":
            self._state.blocked_by = self._optional_string(
                payload.get("reason"), default="test failure needs investigation"
            )
            self._state.interruptibility = "low"
            self._ensure_next_action("investigate failing tests")

    def _coalesce_recent_action(self, event: DevEvent, decision: PolicyDecision) -> bool:
        coalesce_key = self._coalesce_key(event)
        if coalesce_key is None or not self._state.recent_actions:
            self._last_coalesced_key = coalesce_key
            self._last_coalesced_timestamp = event.timestamp if coalesce_key is not None else None
            return False

        within_window = (
            self._last_coalesced_key == coalesce_key
            and self._last_coalesced_timestamp is not None
            and event.timestamp - self._last_coalesced_timestamp <= self._coalesce_window
        )
        if not within_window:
            self._last_coalesced_key = coalesce_key
            self._last_coalesced_timestamp = event.timestamp
            return False

        self._state.recent_actions[0] = RecentAction(
            timestamp=event.timestamp,
            source=event.source.value,
            type=event.type,
            summary=self._summarize_event(event.type, event.payload),
            policy_reason=decision.reason,
        )
        self._last_coalesced_timestamp = event.timestamp
        return True

    def _coalesce_key(self, event: DevEvent) -> tuple[str, str, str] | None:
        if event.type not in {"file_focus", "cursor_move"}:
            return None

        target = self._optional_string(event.payload.get("path"))
        if target is None:
            return None
        return (event.source.value, event.type, target)

    def _ensure_next_action(self, suggestion: str) -> None:
        if suggestion not in self._state.next_best_actions:
            self._state.next_best_actions.append(suggestion)

    def _clear_blocker_state(self) -> None:
        self._state.blocked_by = None
        self._state.interruptibility = "high"
        self._state.next_best_actions = []

    def _summarize_event(self, event_type: str, payload: dict[str, Any]) -> str:
        target = payload.get("path") or payload.get("branch") or payload.get("ticket_id")
        if isinstance(target, str) and target:
            return f"{event_type}: {target}"
        return event_type

    def _optional_string(self, value: Any, default: str | None = None) -> str | None:
        if isinstance(value, str) and value.strip():
            return value
        return default

    def _optional_float(self, value: Any, default: float) -> float:
        if isinstance(value, int | float):
            return float(value)
        return default
