from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from devcd.slices.ambient_context.models import (
    AgentContextSurface,
    BlockerSignal,
    ContextBrief,
    ContextFeedback,
    ContextFeedbackKind,
    ContextMemoryItem,
    ContextQualityReport,
    DetailLevel,
    EvidenceItem,
    FreshnessState,
    FreshnessStatus,
    GitContext,
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
    SurfaceKind,
    WithheldContext,
    WorkState,
)
from devcd.slices.events.models import DevEvent, EventSensitivity, EventSource
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.models import MemoryEntry, MemoryScope
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine

_ALL_STATE_AREAS = (
    "summary",
    "active_goal",
    "active_intent",
    "relevant_artifacts",
    "git_context",
    "open_loops",
    "recent_attempts",
    "blockers",
    "suggested_next_steps",
)


@dataclass(frozen=True)
class ContextSurfaceDefinition:
    kind: SurfaceKind
    detail_level: DetailLevel
    allowed_state_areas: tuple[str, ...]
    allowed_memory_scopes: tuple[MemoryScope, ...]
    withheld_fields: tuple[str, ...] = ()
    max_relevant_artifacts: int | None = None


_LEGACY_LOCAL_SURFACES = {
    SurfaceKind.HTTP,
    SurfaceKind.CLI,
    SurfaceKind.ARTIFACT,
    SurfaceKind.MCP,
    SurfaceKind.VSCODE,
    SurfaceKind.OTHER,
}


_CONTEXT_SURFACES: dict[SurfaceKind, ContextSurfaceDefinition] = {
    SurfaceKind.CODING_AGENT: ContextSurfaceDefinition(
        kind=SurfaceKind.CODING_AGENT,
        detail_level=DetailLevel.STANDARD,
        allowed_state_areas=_ALL_STATE_AREAS,
        allowed_memory_scopes=(MemoryScope.WORKING, MemoryScope.EPISODIC),
    ),
    SurfaceKind.REVIEW_AGENT: ContextSurfaceDefinition(
        kind=SurfaceKind.REVIEW_AGENT,
        detail_level=DetailLevel.STANDARD,
        allowed_state_areas=(
            "summary",
            "active_goal",
            "relevant_artifacts",
            "git_context",
            "open_loops",
            "recent_attempts",
        ),
        allowed_memory_scopes=(MemoryScope.WORKING, MemoryScope.EPISODIC),
        max_relevant_artifacts=8,
    ),
    SurfaceKind.DEBUGGING_AGENT: ContextSurfaceDefinition(
        kind=SurfaceKind.DEBUGGING_AGENT,
        detail_level=DetailLevel.DIAGNOSTIC,
        allowed_state_areas=_ALL_STATE_AREAS,
        allowed_memory_scopes=(MemoryScope.WORKING, MemoryScope.EPISODIC),
    ),
    SurfaceKind.SUBAGENT: ContextSurfaceDefinition(
        kind=SurfaceKind.SUBAGENT,
        detail_level=DetailLevel.MINIMAL,
        allowed_state_areas=(
            "summary",
            "active_goal",
            "active_intent",
            "relevant_artifacts",
            "blockers",
            "suggested_next_steps",
        ),
        allowed_memory_scopes=(MemoryScope.WORKING,),
        max_relevant_artifacts=3,
    ),
    SurfaceKind.PUBLIC_DEMO: ContextSurfaceDefinition(
        kind=SurfaceKind.PUBLIC_DEMO,
        detail_level=DetailLevel.MINIMAL,
        allowed_state_areas=("summary",),
        allowed_memory_scopes=(),
        withheld_fields=(
            "active_goal",
            "active_intent",
            "relevant_artifacts.identifier",
            "git_context.branch",
            "git_context.latest_commit",
            "git_context.latest_commit_summary",
            "open_loops",
            "recent_attempts",
            "blockers",
            "suggested_next_steps",
        ),
        max_relevant_artifacts=1,
    ),
}


class AmbientContextService:
    def __init__(
        self,
        state_engine: StateEngine,
        memory_store: MemoryStore,
        policy_engine: PolicyEngine,
        feedback_path: Path | None = None,
    ) -> None:
        self.state_engine = state_engine
        self.memory_store = memory_store
        self.policy_engine = policy_engine
        self.feedback_path = feedback_path or Path(".devcd/context-feedback.jsonl")
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
        suggested_actions = self._suggested_next_actions_from_memory(working_memory)
        suggestions = self._suggestions_from_blockers(blockers, suggested_actions)
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

    def record_feedback(
        self,
        brief_id: str,
        kind: str | ContextFeedbackKind,
        note: str,
    ) -> ContextFeedback:
        feedback_kind = ContextFeedbackKind(kind)
        control_reason = self._context_control_reason("record_feedback")
        note_event = DevEvent(
            source=EventSource.NOTES,
            type="context_feedback",
            payload=self._feedback_payload(
                brief_id=brief_id,
                feedback_kind=feedback_kind,
                note=note,
            ),
            sensitivity=EventSensitivity.SENSITIVE
            if feedback_kind is ContextFeedbackKind.TOO_SENSITIVE
            else EventSensitivity.NORMAL,
        )
        observation_decision = self.policy_engine.decide_observation(note_event)
        storage_decision = self.policy_engine.decide_local_storage(note_event)
        withheld: list[WithheldContext] = []
        stored_note: str | None = note
        note_decision = (
            observation_decision if not observation_decision.allowed else storage_decision
        )
        if not note_decision.allowed:
            explanation = self.policy_engine.explain_decision(note_decision, note_event)
            stored_note = None
            withheld.append(
                WithheldContext(
                    kind="feedback_note",
                    reason=explanation.reason,
                    category=explanation.category,
                    policy_reason=explanation.reason,
                    safe_summary=explanation.safe_summary,
                )
            )

        feedback = ContextFeedback(
            brief_id=brief_id,
            kind=feedback_kind,
            note=stored_note,
            note_withheld=stored_note is None,
            withheld_context=withheld,
            policy_reason=(
                f"{control_reason}; {observation_decision.reason}; {storage_decision.reason}"
            ),
        )
        self._append_feedback(feedback)
        return feedback

    def get_context_quality(self) -> ContextQualityReport:
        return ContextQualityReport(feedback=self._read_feedback())

    def _feedback_payload(
        self,
        *,
        brief_id: str,
        feedback_kind: ContextFeedbackKind,
        note: str,
    ) -> dict[str, str]:
        payload = {"brief_id": brief_id, "kind": feedback_kind.value}
        if feedback_kind is not ContextFeedbackKind.TOO_SENSITIVE:
            payload["text"] = note
        return payload

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

    def _append_feedback(self, feedback: ContextFeedback) -> None:
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        with self.feedback_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(feedback.model_dump(mode="json"), sort_keys=True))
            handle.write("\n")

    def _read_feedback(self) -> list[ContextFeedback]:
        if not self.feedback_path.exists():
            return []
        feedback_items: list[ContextFeedback] = []
        for line in self.feedback_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                feedback_items.append(ContextFeedback.model_validate_json(line))
            except ValueError:
                continue
        return feedback_items

    def create_context_brief(self, surface: AgentContextSurface | None = None) -> ContextBrief:
        requested_surface = surface or AgentContextSurface()
        surface_definition = self._surface_definition(requested_surface)
        resolved_surface = self._resolve_surface(requested_surface, surface_definition)
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
        surface_memory = self._memory_for_surface(surface_definition)
        withheld = list(self._withheld_context(work_state, export_decision))
        withheld.extend(self._surface_withheld_context(work_state, surface_definition))
        active_goal = (
            self._active_goal_for_surface(surface_definition, surface_memory, work_state)
            if self._surface_allows(surface_definition, "active_goal", export_decision.allowed)
            else None
        )
        git_context = (
            self._git_context_from_memory(surface_memory)
            if self._surface_allows(surface_definition, "git_context", export_decision.allowed)
            else GitContext()
        )
        relevant_artifacts = (
            self._limit_artifacts(work_state.relevant_artifacts, surface_definition)
            if self._surface_allows(
                surface_definition,
                "relevant_artifacts",
                export_decision.allowed,
            )
            else []
        )
        open_loops = (
            work_state.open_loops
            if self._surface_allows(surface_definition, "open_loops", export_decision.allowed)
            else []
        )
        recent_attempts = (
            work_state.recent_attempts
            if self._surface_allows(surface_definition, "recent_attempts", export_decision.allowed)
            else []
        )
        blockers = (
            work_state.blockers
            if self._surface_allows(surface_definition, "blockers", export_decision.allowed)
            else []
        )
        suggested_next_steps = (
            work_state.suggestions
            if self._surface_allows(
                surface_definition,
                "suggested_next_steps",
                export_decision.allowed,
            )
            else []
        )
        policy_reason = self._surface_policy_reason(export_decision.reason, surface_definition)
        policy_summary = PolicySummary(
            allowed=export_decision.allowed,
            operation=export_decision.operation,
            reason=policy_reason,
            included_sources=work_state.policy_summary.included_sources
            if export_decision.allowed
            else [],
            withheld_sources=work_state.policy_summary.withheld_sources,
            included_data_classes=[data_class] if export_decision.allowed else [],
            withheld_data_classes=[] if export_decision.allowed else [data_class],
        )
        return ContextBrief(
            surface=resolved_surface,
            summary=self._brief_summary_for_surface(
                work_state,
                surface_definition,
                export_decision.allowed,
            ),
            active_goal=active_goal,
            active_intent=work_state.active_intent
            if self._surface_allows(surface_definition, "active_intent", export_decision.allowed)
            else None,
            relevant_artifacts=relevant_artifacts,
            git_context=git_context,
            open_loops=open_loops,
            recent_attempts=recent_attempts,
            blockers=blockers,
            suggested_next_steps=suggested_next_steps,
            withheld_context=withheld,
            withheld=withheld,
            agent_limitations=self._agent_limitations(
                active_goal=active_goal,
                git_context=git_context,
                withheld=withheld,
                export_allowed=export_decision.allowed,
            ),
            policy_decision=policy_summary,
        )

    def _surface_definition(
        self,
        surface: AgentContextSurface,
    ) -> ContextSurfaceDefinition:
        definition = _CONTEXT_SURFACES.get(surface.kind)
        if definition is not None:
            return definition
        if surface.kind in _LEGACY_LOCAL_SURFACES:
            return ContextSurfaceDefinition(
                kind=surface.kind,
                detail_level=surface.detail_level,
                allowed_state_areas=_ALL_STATE_AREAS,
                allowed_memory_scopes=(MemoryScope.WORKING,),
            )
        raise ValueError(f"unknown context surface: {surface.kind}")

    def _resolve_surface(
        self,
        surface: AgentContextSurface,
        definition: ContextSurfaceDefinition,
    ) -> AgentContextSurface:
        return surface.model_copy(
            update={
                "detail_level": definition.detail_level,
                "allowed_state_areas": list(definition.allowed_state_areas),
                "allowed_memory_scopes": [
                    scope.value for scope in definition.allowed_memory_scopes
                ],
                "withheld_fields": list(definition.withheld_fields),
            }
        )

    def _memory_for_surface(
        self,
        definition: ContextSurfaceDefinition,
    ) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for scope in definition.allowed_memory_scopes:
            entries.extend(
                self.memory_store.list_by_scope(
                    scope,
                    self.state_engine.is_source_visible,
                )
            )
        return entries

    def _surface_allows(
        self,
        definition: ContextSurfaceDefinition,
        state_area: str,
        export_allowed: bool,
    ) -> bool:
        return export_allowed and state_area in definition.allowed_state_areas

    def _active_goal_for_surface(
        self,
        definition: ContextSurfaceDefinition,
        entries: list[MemoryEntry],
        work_state: WorkState,
    ) -> str | None:
        if definition.kind is SurfaceKind.SUBAGENT and work_state.active_intent is not None:
            return work_state.active_intent.summary
        return self._active_goal_from_memory(entries)

    def _limit_artifacts(
        self,
        artifacts: list[RelevantArtifact],
        definition: ContextSurfaceDefinition,
    ) -> list[RelevantArtifact]:
        if definition.max_relevant_artifacts is None:
            return artifacts
        return artifacts[: definition.max_relevant_artifacts]

    def _surface_policy_reason(
        self,
        export_reason: str,
        definition: ContextSurfaceDefinition,
    ) -> str:
        allowed_scopes = ", ".join(scope.value for scope in definition.allowed_memory_scopes)
        if not allowed_scopes:
            allowed_scopes = "none"
        return (
            f"{export_reason}; surface '{definition.kind.value}' allows state areas "
            f"{', '.join(definition.allowed_state_areas)} and memory scopes {allowed_scopes}"
        )

    def _brief_summary_for_surface(
        self,
        work_state: WorkState,
        definition: ContextSurfaceDefinition,
        export_allowed: bool,
    ) -> str:
        if not export_allowed:
            return "No context is visible because the requested export was denied by policy."
        if (
            "active_goal" not in definition.allowed_state_areas
            and "active_intent" not in definition.allowed_state_areas
        ):
            return f"Visible context is limited by the '{definition.kind.value}' context surface."
        return self._brief_summary(work_state)

    def _surface_withheld_context(
        self,
        work_state: WorkState,
        definition: ContextSurfaceDefinition,
    ) -> list[WithheldContext]:
        withheld: list[WithheldContext] = []
        for field in definition.withheld_fields:
            if not self._field_has_visible_value(field, work_state):
                continue
            policy_reason = (
                f"field '{field}' is withheld by the '{definition.kind.value}' context surface"
            )
            withheld.append(
                WithheldContext(
                    kind="sensitive_field",
                    reason=policy_reason,
                    category="sensitive_field",
                    policy_reason=policy_reason,
                    safe_summary="A sensitive field was withheld; no raw value is exposed.",
                )
            )

        sensitive_base_fields = {
            field.split(".", maxsplit=1)[0] for field in definition.withheld_fields
        }
        for state_area in _ALL_STATE_AREAS:
            if state_area in definition.allowed_state_areas or state_area in sensitive_base_fields:
                continue
            if not self._field_has_visible_value(state_area, work_state):
                continue
            policy_reason = (
                f"state area '{state_area}' is outside the '{definition.kind.value}' "
                "context surface"
            )
            withheld.append(
                WithheldContext(
                    kind="state_area",
                    reason=policy_reason,
                    category="state_area",
                    policy_reason=policy_reason,
                    safe_summary="A broader state area was withheld for this surface.",
                )
            )
        return withheld

    def _field_has_visible_value(self, field: str, work_state: WorkState) -> bool:
        root = field.split(".", maxsplit=1)[0]
        if root in {"active_goal", "active_intent"}:
            return work_state.active_intent is not None
        if root == "relevant_artifacts":
            return bool(work_state.relevant_artifacts)
        if root == "git_context":
            return any(action.source == "git" for action in work_state.recent_attempts)
        if root == "open_loops":
            return bool(work_state.open_loops)
        if root == "recent_attempts":
            return bool(work_state.recent_attempts)
        if root == "blockers":
            return bool(work_state.blockers)
        if root == "suggested_next_steps":
            return bool(work_state.suggestions)
        return False

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
        seen_sources: set[str] = set()
        for item in self._withheld_context_metadata():
            category = self._string_from_content(item, "category") or "context"
            source = self._string_from_content(item, "source") or "unknown"
            if category == "source":
                seen_sources.add(source)
            policy_reason = self._string_from_content(item, "policy_reason") or "withheld by policy"
            yield WithheldContext(
                kind=category,
                reason=policy_reason,
                category=category,
                policy_reason=policy_reason,
                safe_summary=self._string_from_content(item, "safe_summary")
                or "Context was withheld; no safe replacement is available.",
            )
        for source in work_state.policy_summary.withheld_sources:
            if source in seen_sources:
                continue
            policy_reason = f"source '{source}' is not visible"
            yield WithheldContext(
                kind="source",
                reason=policy_reason,
                category="source",
                policy_reason=policy_reason,
                safe_summary=f"{source} source is withheld; no event metadata is visible.",
            )
        if not export_decision.allowed:
            yield WithheldContext(
                kind="data_class",
                reason=export_decision.reason,
                category="data_class",
                policy_reason=export_decision.reason,
                safe_summary="Metadata-only context may be requested instead.",
            )

    def _withheld_context_metadata(self) -> list[dict[str, Any]]:
        metadata = self.state_engine.state.metadata.get("withheld_context", [])
        if not isinstance(metadata, list):
            return []
        return [item for item in metadata if isinstance(item, dict)]

    def _agent_limitations(
        self,
        *,
        active_goal: str | None,
        git_context: GitContext,
        withheld: list[WithheldContext],
        export_allowed: bool,
    ) -> list[str]:
        limitations: list[str] = []
        if active_goal is None:
            limitations.append("The agent does not know an active goal from visible context.")
        if git_context.branch is None and git_context.latest_commit is None:
            limitations.append("The agent does not know branch or latest commit metadata.")
        for item in withheld:
            category = item.category or item.kind or "context"
            reason = item.policy_reason or item.reason or "withheld by policy"
            safe_summary = item.safe_summary or "No safe replacement is available."
            limitations.append(
                f"The agent cannot see {category} context withheld by policy ({reason}); "
                f"safe summary: {safe_summary}"
            )
        if not export_allowed:
            limitations.append(
                "The agent cannot see the requested data class because export was denied by policy."
            )
        return limitations or ["No policy-withheld or unknown context is known for this brief."]

    def _active_goal_from_memory(self, entries: list[MemoryEntry]) -> str | None:
        latest_goal = self._latest_payload_value(
            entries,
            event_type="goal_update",
            key="current_goal",
        )
        if latest_goal is None:
            return None
        return latest_goal[0]

    def _git_context_from_memory(self, entries: list[MemoryEntry]) -> GitContext:
        branch = self._latest_payload_value(entries, event_type="branch_change", key="branch")
        commit_sha = self._latest_payload_value(entries, event_type="commit", key="sha")
        commit_message = self._latest_payload_value(entries, event_type="commit", key="message")
        repo = self._latest_payload_value(entries, event_type="branch_change", key="repo")
        return GitContext(
            branch=branch[0] if branch is not None else None,
            latest_commit=commit_sha[0] if commit_sha is not None else None,
            latest_commit_summary=commit_message[0] if commit_message is not None else None,
            repository=repo[0] if repo is not None else None,
        )

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
        suggested_actions: dict[str, str],
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
            suggested_action = suggested_actions.get(blocker.summary)
            suggestions.append(
                ProactiveSuggestion(
                    id=suggestion_id,
                    summary=suggested_action or f"Investigate {blocker.summary}",
                    rationale=(
                        f"Last failure was '{blocker.summary}'."
                        if suggested_action is not None
                        else "Repeated failure evidence suggests the current blocker is "
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

    def _suggested_next_actions_from_memory(self, entries: list[MemoryEntry]) -> dict[str, str]:
        suggestions: dict[str, str] = {}
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if self._string_from_content(entry.content, "type") != "test_failure":
                continue
            reason = self._payload_value(entry.content, "reason")
            suggested_action = self._payload_value(entry.content, "suggested_next_action")
            if isinstance(reason, str) and isinstance(suggested_action, str):
                suggestions.setdefault(reason, suggested_action)
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


def render_context_brief_markdown(brief: ContextBrief) -> str:
    lines = ["# DevCD Agent Handoff Brief", ""]
    lines.extend(["## brief_id", brief.id, ""])

    lines.extend(["## active_goal", brief.active_goal or "No active goal available.", ""])

    lines.extend(["## relevant_artifacts"])
    if brief.relevant_artifacts:
        for artifact in brief.relevant_artifacts:
            lines.append(f"- {artifact.kind}: {artifact.identifier} - {artifact.summary}")
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## git_context"])
    lines.append(f"- branch: {brief.git_context.branch or 'unknown'}")
    lines.append(f"- latest_commit: {brief.git_context.latest_commit or 'unknown'}")
    lines.append(f"- latest_commit_summary: {brief.git_context.latest_commit_summary or 'unknown'}")
    lines.append("")

    lines.extend(["## recent_attempts"])
    if brief.recent_attempts:
        for attempt in brief.recent_attempts[:5]:
            lines.append(
                f"- {attempt.outcome}: {attempt.summary} ({attempt.source}/{attempt.type})"
            )
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## Last failure"])
    if brief.blockers:
        lines.append(f"- {brief.blockers[0].summary}")
    else:
        last_failure = next(
            (attempt for attempt in brief.recent_attempts if attempt.outcome == "failure"),
            None,
        )
        last_failure_summary = (
            f"- {last_failure.summary}" if last_failure is not None else "- None detected."
        )
        lines.append(last_failure_summary)
    lines.append("")

    lines.extend(["## Suggested next action"])
    if brief.suggested_next_steps:
        lines.append(f"- {brief.suggested_next_steps[0].summary}")
    else:
        lines.append("- Continue from the active goal using visible artifacts and attempts.")
    lines.append("")

    lines.extend(["## blockers"])
    if brief.blockers:
        for blocker in brief.blockers:
            lines.append(f"- {blocker.summary}")
    else:
        lines.append("- None detected.")
    lines.append("")

    lines.extend(["## suggested_next_steps"])
    if brief.suggested_next_steps:
        for suggestion in brief.suggested_next_steps:
            lines.append(f"- {suggestion.summary}: {suggestion.rationale}")
    else:
        lines.append("- Continue from the active goal using visible artifacts and attempts.")
    lines.append("")

    lines.extend(["## withheld_context"])
    if brief.withheld_context:
        for withheld in brief.withheld_context:
            lines.append(f"- category: {withheld.category or withheld.kind}")
            lines.append(f"  policy_reason: {withheld.policy_reason or withheld.reason}")
            safe_summary = withheld.safe_summary or "No safe replacement available."
            lines.append(f"  safe_summary: {safe_summary}")
    else:
        lines.append("- None withheld for this brief.")
    lines.append("")

    lines.extend(["## agent_limitations"])
    for limitation in brief.agent_limitations:
        lines.append(f"- {limitation}")
    lines.append("")

    lines.extend(["## policy_decision"])
    lines.append(f"- allowed: {str(brief.policy_decision.allowed).lower()}")
    lines.append(f"- operation: {brief.policy_decision.operation}")
    lines.append(f"- reason: {brief.policy_decision.reason}")
    return "\n".join(lines) + "\n"
