from __future__ import annotations

from typing import Any

from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent
from devcd.slices.host_state_engine.models import DevState, RecentAction
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.models import PolicyDecision
from devcd.slices.policy_layer.service import PolicyEngine


class StateEngine:
    def __init__(
        self,
        policy_engine: PolicyEngine,
        memory_store: MemoryStore,
        event_ledger: EventLedger,
    ) -> None:
        self._policy_engine = policy_engine
        self._memory_store = memory_store
        self._event_ledger = event_ledger
        self._state = DevState()

    @property
    def state(self) -> DevState:
        return self._state

    @property
    def memory_store(self) -> MemoryStore:
        return self._memory_store

    def accept_event(self, event: DevEvent) -> PolicyDecision:
        decision = self._policy_engine.decide_observation(event)
        if not decision.allowed:
            return decision

        storage_decision = self._policy_engine.decide_local_storage(event)
        if storage_decision.allowed:
            self._event_ledger.append(event=event, decision=storage_decision)
            self._memory_store.add_working(
                {
                    "source": event.source.value,
                    "type": event.type,
                    "payload": event.payload,
                    "observation_policy_reason": decision.reason,
                    "storage_policy_reason": storage_decision.reason,
                }
            )
        self._apply_event(event=event, decision=decision)
        return decision

    def _apply_event(self, event: DevEvent, decision: PolicyDecision) -> None:
        payload = event.payload
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
        elif event.type == "file_focus":
            file_path = self._optional_string(payload.get("path"))
            duration_seconds = self._optional_float(payload.get("duration_seconds"), default=1.0)
            if file_path is not None:
                self._state.attention_score[file_path] = (
                    self._state.attention_score.get(file_path, 0.0) + duration_seconds
                )
        elif event.type == "test_fail":
            self._state.blocked_by = self._optional_string(
                payload.get("reason"), default="test failure needs investigation"
            )
            self._state.interruptibility = "low"

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
