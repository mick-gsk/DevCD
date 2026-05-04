from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from devcd.slices.ambient_context.models import (
    AgentContextSurface,
    BlockerSignal,
    ContextBrief,
    ContextMemoryItem,
    EvidenceItem,
    FreshnessState,
    FreshnessStatus,
    IntentLine,
    IntentStatus,
    MemoryCorrection,
    OpenLoop,
    OpenLoopKind,
    OpenLoopStatus,
    PolicySummary,
    ProactiveSuggestion,
    ProactiveSuggestionStatus,
    RecentAttempt,
    RelevantArtifact,
    WithheldContext,
    WorkState,
)
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.models import MemoryEntry, MemoryScope
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine


class AmbientContextService:
    def __init__(
        self,
        state_engine: StateEngine,
        memory_store: MemoryStore,
        policy_engine: PolicyEngine,
    ) -> None:
        self.state_engine = state_engine
        self.memory_store = memory_store
        self.policy_engine = policy_engine
        self._dismissed_suggestions: dict[str, ProactiveSuggestion] = {}
        self._suggestion_cooldown = timedelta(minutes=30)

    def get_work_state(self) -> WorkState:
        visible_state = self.state_engine.state
        working_memory = self.memory_store.list_by_scope(
            MemoryScope.WORKING,
            self.state_engine.is_source_visible,
        )
        evidence = self._evidence_from_memory(working_memory)
        recent_attempts = [
            RecentAttempt(
                timestamp=action.timestamp,
                source=action.source,
                type=action.type,
                summary=action.summary,
                outcome=self._outcome_for_action(action.type),
                policy_reason=action.policy_reason,
            )
            for action in visible_state.recent_actions
        ]
        active_intent = self._active_intent(working_memory, evidence)
        candidate_intents = self._candidate_intents(working_memory, evidence, active_intent)
        artifacts = self._artifacts_from_memory(working_memory)
        open_loops, blockers = self._open_loops_and_blockers(visible_state.blocked_by, evidence)
        suggestions = self._suggestions_from_blockers(blockers)
        export_decision = self.policy_engine.decide_context_export(
            surface="http",
            data_class="metadata",
        )
        included_sources = sorted(
            {action.source for action in visible_state.recent_actions}
            | {artifact.source for artifact in artifacts}
        )
        withheld_sources = sorted(
            source for source, enabled in visible_state.source_active_map.items() if not enabled
        )
        confidence = active_intent.confidence if active_intent is not None else 0.0

        return WorkState(
            active_intent=active_intent,
            candidate_intents=candidate_intents,
            relevant_artifacts=artifacts,
            open_loops=open_loops,
            recent_attempts=recent_attempts,
            blockers=blockers,
            suggestions=suggestions,
            freshness=FreshnessState(
                status=FreshnessStatus.CURRENT if evidence else FreshnessStatus.STALE,
                last_seen_at=self._latest_timestamp(evidence),
            ),
            confidence=confidence,
            policy_summary=PolicySummary(
                allowed=export_decision.allowed,
                operation=export_decision.operation,
                reason=export_decision.reason,
                included_sources=included_sources,
                withheld_sources=withheld_sources,
                included_data_classes=["metadata"] if export_decision.allowed else [],
                withheld_data_classes=[] if export_decision.allowed else ["metadata"],
            ),
        )

    def dismiss_suggestion(self, suggestion_id: str) -> ProactiveSuggestion:
        control_reason = self._context_control_reason("dismiss_suggestion")
        for suggestion in self.get_work_state().suggestions:
            if suggestion.id == suggestion_id:
                dismissed = suggestion.model_copy(
                    update={
                        "status": ProactiveSuggestionStatus.DISMISSED,
                        "suppressed_until": datetime.now(UTC) + self._suggestion_cooldown,
                        "rationale": f"{suggestion.rationale} {control_reason}",
                    }
                )
                self._dismissed_suggestions[suggestion_id] = dismissed
                return dismissed
        existing = self._dismissed_suggestions.get(suggestion_id)
        if existing is not None:
            return existing
        raise KeyError(suggestion_id)

    def list_context_memory(
        self,
        scope: str | MemoryScope | None = None,
    ) -> list[ContextMemoryItem]:
        memory_scope = MemoryScope(scope) if isinstance(scope, str) else scope
        if memory_scope is None:
            entries = self.memory_store.list_all(self.state_engine.is_source_visible)
        else:
            entries = self.memory_store.list_by_scope(
                memory_scope,
                self.state_engine.is_source_visible,
            )
        return [self._context_memory_item(entry) for entry in entries]

    def correct_context_memory_item(
        self,
        item_id: str,
        correction: MemoryCorrection,
    ) -> ContextMemoryItem:
        entry = self.memory_store.get(item_id, self.state_engine.is_source_visible)
        if entry is None:
            raise KeyError(item_id)
        control_reason = self._context_control_reason("correct_memory")

        content = dict(entry.content)
        payload = content.get("payload")
        corrected_payload = dict(payload) if isinstance(payload, dict) else {}

        event_type = self._string_from_content(content, "type")
        if event_type == "goal_update":
            corrected_payload["current_goal"] = correction.summary
        elif event_type == "branch_change":
            corrected_payload["branch"] = correction.summary
        elif event_type == "test_failure":
            corrected_payload["reason"] = correction.summary
        else:
            content["corrected_summary"] = correction.summary

        if corrected_payload:
            content["payload"] = corrected_payload
        content["correction_reason"] = correction.reason
        content["corrected_at"] = datetime.now(UTC).isoformat()
        existing_reason = entry.policy_reason or "local context memory"
        policy_reason = f"{existing_reason}; {control_reason}; corrected: {correction.reason}"
        updated = self.memory_store.update_content(
            item_id,
            content=content,
            policy_reason=policy_reason,
        )
        if updated is None:
            raise KeyError(item_id)
        return self._context_memory_item(updated)

    def delete_context_memory_item(self, item_id: str) -> None:
        if self.memory_store.get(item_id, self.state_engine.is_source_visible) is None:
            raise KeyError(item_id)
        self._context_control_reason("delete_memory")
        self.memory_store.delete(item_id)

    def create_context_brief(self, surface: AgentContextSurface | None = None) -> ContextBrief:
        resolved_surface = surface or AgentContextSurface()
        data_class = (
            resolved_surface.requested_data_classes[0]
            if resolved_surface.requested_data_classes
            else "metadata"
        )
        export_decision = self.policy_engine.decide_context_export(
            surface=resolved_surface.kind.value,
            data_class=data_class,
        )
        work_state = self.get_work_state()
        withheld = list(self._withheld_context(work_state, export_decision))
        policy_summary = PolicySummary(
            allowed=export_decision.allowed,
            operation=export_decision.operation,
            reason=export_decision.reason,
            included_sources=work_state.policy_summary.included_sources
            if export_decision.allowed
            else [],
            withheld_sources=work_state.policy_summary.withheld_sources,
            included_data_classes=[data_class] if export_decision.allowed else [],
            withheld_data_classes=[] if export_decision.allowed else [data_class],
        )
        return ContextBrief(
            surface=resolved_surface,
            summary=self._brief_summary(work_state),
            active_intent=work_state.active_intent if export_decision.allowed else None,
            relevant_artifacts=work_state.relevant_artifacts if export_decision.allowed else [],
            open_loops=work_state.open_loops if export_decision.allowed else [],
            recent_attempts=work_state.recent_attempts if export_decision.allowed else [],
            suggested_next_steps=work_state.suggestions if export_decision.allowed else [],
            withheld=withheld,
            policy_decision=policy_summary,
        )

    def _context_control_reason(self, control_name: str) -> str:
        decision = self.policy_engine.decide_context_control(control_name)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        return decision.reason

    def _evidence_from_memory(self, entries: Iterable[MemoryEntry]) -> list[EvidenceItem]:
        evidence: list[EvidenceItem] = []
        for entry in entries:
            event_type = self._string_from_content(entry.content, "type")
            evidence.append(
                EvidenceItem(
                    source=entry.source or "unknown",
                    event_type=event_type,
                    summary=self._summary_from_content(entry.content),
                    timestamp=entry.timestamp,
                    policy_reason=entry.policy_reason
                    or "local context evidence is visible by policy",
                )
            )
        return evidence

    def _withheld_context(
        self,
        work_state: WorkState,
        export_decision,
    ) -> Iterable[WithheldContext]:
        for source in work_state.policy_summary.withheld_sources:
            yield WithheldContext(kind="source", reason=f"source '{source}' is not visible")
        if not export_decision.allowed:
            yield WithheldContext(kind="data_class", reason=export_decision.reason)

    def _brief_summary(self, work_state: WorkState) -> str:
        if work_state.active_intent is None:
            return "No active intent could be inferred with enough confidence."
        return f"Working on {work_state.active_intent.summary}."

    def _active_intent(
        self,
        entries: list[MemoryEntry],
        evidence: list[EvidenceItem],
    ) -> IntentLine | None:
        latest_goal = self._latest_payload_value(
            entries, event_type="goal_update", key="current_goal"
        )
        latest_branch = self._latest_payload_value(
            entries, event_type="branch_change", key="branch"
        )
        intent_source = latest_branch or latest_goal
        if intent_source is None:
            return None

        summary, timestamp = intent_source
        event_type = "branch_change" if latest_branch is not None else "goal_update"
        return IntentLine(
            summary=summary,
            evidence=self._evidence_for_event_type(evidence, event_type),
            started_at=timestamp,
            updated_at=timestamp,
            confidence=0.9 if event_type == "goal_update" else 0.6,
            status=IntentStatus.ACTIVE,
        )

    def _candidate_intents(
        self,
        entries: list[MemoryEntry],
        evidence: list[EvidenceItem],
        active_intent: IntentLine | None,
    ) -> list[IntentLine]:
        candidates: list[IntentLine] = []
        if active_intent is not None:
            candidates.append(active_intent)
        latest_goal = self._latest_payload_value(
            entries, event_type="goal_update", key="current_goal"
        )
        latest_branch = self._latest_payload_value(
            entries, event_type="branch_change", key="branch"
        )
        if (
            latest_goal is not None
            and latest_branch is not None
            and latest_branch[1] > latest_goal[1]
        ):
            candidates.append(
                IntentLine(
                    summary=latest_goal[0],
                    evidence=self._evidence_for_event_type(evidence, "goal_update"),
                    started_at=latest_goal[1],
                    updated_at=latest_goal[1],
                    confidence=0.3,
                    status=IntentStatus.STALE,
                )
            )
        return candidates

    def _artifacts_from_memory(self, entries: list[MemoryEntry]) -> list[RelevantArtifact]:
        artifacts: list[RelevantArtifact] = []
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if self._string_from_content(entry.content, "type") != "file_focus":
                continue
            file_path = self._payload_value(entry.content, "path")
            if not isinstance(file_path, str) or not file_path:
                continue
            artifacts.append(
                RelevantArtifact(
                    kind="file",
                    identifier=file_path,
                    summary=f"file_focus: {file_path}",
                    source=entry.source or "unknown",
                    relevance=0.8,
                    last_seen_at=entry.timestamp,
                    policy_reason=entry.policy_reason
                    or "local context artifact is visible by policy",
                )
            )
        return artifacts

    def _open_loops_and_blockers(
        self,
        blocked_by: str | None,
        evidence: list[EvidenceItem],
    ) -> tuple[list[OpenLoop], list[BlockerSignal]]:
        if blocked_by is None:
            return [], []

        failure_evidence = self._evidence_for_event_type(evidence, "test_failure")
        timestamp = failure_evidence[0].timestamp if failure_evidence else datetime.now(UTC)
        loop = OpenLoop(
            id=f"failure:{blocked_by}",
            summary=blocked_by,
            kind=OpenLoopKind.FAILURE,
            evidence=failure_evidence,
            status=OpenLoopStatus.OPEN,
            confidence=0.8,
            created_at=timestamp,
            updated_at=timestamp,
        )
        blocker = BlockerSignal(
            summary=blocked_by,
            evidence=failure_evidence,
            confidence=0.8,
            detected_at=timestamp,
        )
        return [loop], [blocker]

    def _suggestions_from_blockers(
        self,
        blockers: list[BlockerSignal],
    ) -> list[ProactiveSuggestion]:
        suggestions: list[ProactiveSuggestion] = []
        now = datetime.now(UTC)
        for blocker in blockers:
            if blocker.confidence < 0.7:
                continue
            suggestion_id = f"blocker-{self._slug(blocker.summary)}"
            dismissed = self._dismissed_suggestions.get(suggestion_id)
            if (
                dismissed is not None
                and dismissed.suppressed_until is not None
                and dismissed.suppressed_until > now
            ):
                continue
            suggestions.append(
                ProactiveSuggestion(
                    id=suggestion_id,
                    summary=f"Investigate {blocker.summary}",
                    rationale=(
                        "Repeated failure evidence suggests the current blocker is "
                        f"'{blocker.summary}'."
                    ),
                    confidence=blocker.confidence,
                    evidence=blocker.evidence,
                    status=ProactiveSuggestionStatus.ACTIVE,
                    created_at=blocker.detected_at,
                )
            )
            if len(suggestions) == 3:
                break
        return suggestions

    def _slug(self, value: str) -> str:
        allowed = [character.lower() if character.isalnum() else "-" for character in value]
        return "-".join(part for part in "".join(allowed).split("-") if part)

    def _context_memory_item(self, entry: MemoryEntry) -> ContextMemoryItem:
        updated_at = self._updated_at(entry)
        return ContextMemoryItem(
            id=entry.id,
            scope=entry.scope.value,
            summary=self._summary_from_content(entry.content),
            source=entry.source,
            freshness=self._freshness_for_entry(entry),
            confidence=0.9 if "correction_reason" in entry.content else 0.75,
            policy_reason=entry.policy_reason or "local context memory is visible by policy",
            created_at=entry.timestamp,
            updated_at=updated_at,
            expires_at=entry.expires_at,
        )

    def _freshness_for_entry(self, entry: MemoryEntry) -> FreshnessState:
        now = datetime.now(UTC)
        status = (
            FreshnessStatus.EXPIRED
            if entry.expires_at is not None and entry.expires_at < now
            else FreshnessStatus.CURRENT
        )
        return FreshnessState(
            status=status,
            last_seen_at=entry.timestamp,
            expires_at=entry.expires_at,
        )

    def _updated_at(self, entry: MemoryEntry) -> datetime:
        corrected_at = entry.content.get("corrected_at")
        if isinstance(corrected_at, datetime):
            return corrected_at
        if isinstance(corrected_at, str):
            try:
                return datetime.fromisoformat(corrected_at)
            except ValueError:
                return entry.timestamp
        return entry.timestamp

    def _latest_payload_value(
        self,
        entries: list[MemoryEntry],
        *,
        event_type: str,
        key: str,
    ) -> tuple[str, datetime] | None:
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if self._string_from_content(entry.content, "type") != event_type:
                continue
            value = self._payload_value(entry.content, key)
            if isinstance(value, str) and value.strip():
                return value, entry.timestamp
        return None

    def _payload_value(self, content: dict[str, Any], key: str) -> Any:
        payload = content.get("payload")
        if not isinstance(payload, dict):
            return None
        return payload.get(key)

    def _string_from_content(self, content: dict[str, Any], key: str) -> str | None:
        value = content.get(key)
        if isinstance(value, str) and value:
            return value
        return None

    def _summary_from_content(self, content: dict[str, Any]) -> str:
        event_type = self._string_from_content(content, "type") or "event"
        payload = content.get("payload")
        if isinstance(payload, dict):
            target = (
                payload.get("path")
                or payload.get("branch")
                or payload.get("current_goal")
                or payload.get("reason")
            )
            if isinstance(target, str) and target:
                return f"{event_type}: {target}"
        corrected_summary = content.get("corrected_summary")
        if isinstance(corrected_summary, str) and corrected_summary:
            return f"{event_type}: {corrected_summary}"
        return event_type

    def _evidence_for_event_type(
        self,
        evidence: list[EvidenceItem],
        event_type: str,
    ) -> list[EvidenceItem]:
        return [item for item in evidence if item.event_type == event_type]

    def _latest_timestamp(self, evidence: list[EvidenceItem]) -> datetime:
        if not evidence:
            return datetime.now(UTC)
        return max(item.timestamp for item in evidence)

    def _outcome_for_action(
        self,
        action_type: str,
    ) -> Literal["unknown", "success", "failure", "interrupted"]:
        if action_type.endswith("failure") or action_type == "test_failure":
            return "failure"
        if action_type.endswith("success"):
            return "success"
        return "unknown"
