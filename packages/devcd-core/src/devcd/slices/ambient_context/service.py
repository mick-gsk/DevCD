from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from devcd.slices.ambient_context.models import (
    AgentContextSurface,
    AgentResurrectionContext,
    BlockerSignal,
    ContextBrief,
    ContextControlContinuityPreview,
    ContextControlQualitySummary,
    ContextControlReport,
    ContextFeedback,
    ContextFeedbackKind,
    ContextMemoryItem,
    ContextPack,
    ContextPackEventSupport,
    ContextQualityReport,
    ContinuityArtifact,
    ContinuityAttempt,
    ContinuityBlocker,
    ContinuityDecision,
    ContinuityIntent,
    ContinuityPacket,
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
    SurfaceKind.RESEARCH_AGENT: ContextSurfaceDefinition(
        kind=SurfaceKind.RESEARCH_AGENT,
        detail_level=DetailLevel.STANDARD,
        allowed_state_areas=(
            "summary",
            "active_goal",
            "active_intent",
            "relevant_artifacts",
            "open_loops",
            "recent_attempts",
            "blockers",
            "suggested_next_steps",
        ),
        allowed_memory_scopes=(MemoryScope.WORKING, MemoryScope.EPISODIC),
        max_relevant_artifacts=12,
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


class ContextPackRegistry:
    def __init__(self, packs: Iterable[ContextPack]) -> None:
        sorted_packs = sorted(packs, key=lambda pack: pack.id)
        seen_ids: set[str] = set()
        for pack in sorted_packs:
            if pack.id in seen_ids:
                raise ValueError(f"duplicate context pack id: {pack.id}")
            seen_ids.add(pack.id)
        self._packs_by_id = {pack.id: pack for pack in sorted_packs}

    def list_packs(self) -> list[ContextPack]:
        return [pack.model_copy(deep=True) for pack in self._packs_by_id.values()]

    def get_pack(self, pack_id: str) -> ContextPack:
        try:
            return self._packs_by_id[pack_id].model_copy(deep=True)
        except KeyError as error:
            raise KeyError(pack_id) from error


_BUILT_IN_CONTEXT_PACKS = (
    ContextPack(
        id="developer",
        display_name="Developer Context",
        description=(
            "Local developer continuity for IDE focus, Git state, tasks, tests, notes, "
            "review/debugging handoffs, and agent resurrection metadata."
        ),
        supported_events=[
            ContextPackEventSupport(source="git", event_types=["branch_change", "commit"]),
            ContextPackEventSupport(source="ide", event_types=["file_focus"]),
            ContextPackEventSupport(
                source="notes",
                event_types=["context_feedback", "note_update", "prompt_injection", "user_hint"],
            ),
            ContextPackEventSupport(
                source="task",
                event_types=[
                    "code_change",
                    "fix_attempt",
                    "fix_failure",
                    "fix_success",
                    "goal_update",
                    "patch_apply",
                    "test_failure",
                    "test_output",
                ],
            ),
        ],
        supported_surfaces=[
            "artifact",
            "cli",
            "coding-agent",
            "debugging-agent",
            "http",
            "mcp",
            "public-demo",
            "review-agent",
            "subagent",
            "vscode",
        ],
        default_sensitivity="metadata-only developer workflow context",
        policy_notes=[
            "Remote export is disabled by default.",
            "Actions are denied by the default observe-only policy.",
            "Sensitive events, full-text payloads, and disabled sources are withheld.",
        ],
        renderer_metadata={
            "continuity_packet": {
                "default_context_pack": "developer",
                "legacy_handoff_contract": True,
                "pack_metadata_keys": ["git_context", "resurrection"],
            }
        },
    ),
    ContextPack(
        id="research",
        display_name="Research Context",
        description=(
            "Local research continuity for source review metadata, browser and note "
            "metadata, hypotheses, decisions, and failed attempts."
        ),
        supported_events=[
            ContextPackEventSupport(source="browser", event_types=["research_focus", "url_focus"]),
            ContextPackEventSupport(
                source="notes",
                event_types=[
                    "decision",
                    "failed_attempt",
                    "hypothesis",
                    "note_update",
                    "source_review",
                ],
            ),
            ContextPackEventSupport(
                source="task",
                event_types=["failed_attempt", "hypothesis_check", "research_goal"],
            ),
        ],
        supported_surfaces=["cli", "mcp", "public-demo", "research-agent", "subagent"],
        default_sensitivity="metadata-only research continuity context",
        policy_notes=[
            "Remote export is disabled by default.",
            "Raw source text, private notes, and full browser payloads are withheld by policy.",
            "The pack declares local metadata only and does not load remote connectors.",
        ],
        renderer_metadata={
            "continuity_packet": {
                "default_context_pack": "research",
                "artifact_kinds": ["source", "note", "browser_reference"],
                "decision_kinds": ["hypothesis", "decision"],
                "attempt_event_types": ["failed_attempt", "hypothesis_check"],
            }
        },
    ),
)

_CONTEXT_PACK_REGISTRY = ContextPackRegistry(_BUILT_IN_CONTEXT_PACKS)

_EMPTY_PASSPORT_NEXT_STEPS = (
    "Initialize local config: devcd init",
    "Start the local daemon: devcd run",
    "Agents with shell access capture continuity metadata themselves: "
    'devcd capture --kind goal --summary "Describe the task"',
    "Agents without shell access read DevCD only; Do not ask the user to perform "
    "DevCD bookkeeping.",
    "Regenerate this passport: devcd context passport",
)

_EMPTY_PASSPORT_UNKNOWN = "No local ledger events are visible in this passport yet."

_EMPTY_CONTROL_NEXT_STEPS = (
    "devcd init",
    "devcd run",
    'devcd capture --kind goal --summary "Describe the task"',
    "Agents without shell access read DevCD only; Do not ask the user to perform "
    "DevCD bookkeeping.",
    "devcd context control",
)

_QUALITY_PENALTIES: dict[ContextFeedbackKind, float] = {
    ContextFeedbackKind.MISSING: 0.18,
    ContextFeedbackKind.WRONG: 0.2,
    ContextFeedbackKind.STALE: 0.15,
    ContextFeedbackKind.TOO_BROAD: 0.1,
    ContextFeedbackKind.TOO_SENSITIVE: 0.12,
}

_MISSING_CONTEXT_NEXT_ACTION = (
    "Ask the user which missing context should be recorded before the next handoff."
)


def list_context_packs() -> list[ContextPack]:
    return _CONTEXT_PACK_REGISTRY.list_packs()


def get_context_pack(pack_id: str) -> ContextPack:
    return _CONTEXT_PACK_REGISTRY.get_pack(pack_id)


def render_context_packs_json() -> str:
    return json.dumps(
        [pack.model_dump(mode="json") for pack in list_context_packs()],
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )


def render_context_control_report_json(report: ContextControlReport) -> str:
    return report.model_dump_json(indent=2)


def render_context_control_report_text(report: ContextControlReport) -> str:
    lines = [
        "DevCD context control",
        f"Active goal: {report.active_goal or 'none'}",
        f"Surface: {report.selected_surface or 'unknown'}",
        f"Pack: {report.selected_pack or 'unknown'}",
        f"Confidence: {report.confidence:.2f}",
        "",
        "Visible sources",
    ]
    lines.extend(_bullet_lines(report.visible_sources, empty="None visible under current policy."))
    lines.extend(["", "Withheld sources"])
    if report.withheld_sources:
        for withheld in report.withheld_sources:
            category = withheld.category or withheld.kind
            reason = withheld.policy_reason or withheld.reason
            safe_summary = withheld.safe_summary or "No safe replacement available."
            lines.append(f"- {category}: {reason}")
            lines.append(f"  safe_summary: {safe_summary}")
    else:
        lines.append("- None known for this report.")
    lines.extend(["", "Data classes"])
    lines.append(
        "- included: "
        + (", ".join(report.included_data_classes) if report.included_data_classes else "none")
    )
    lines.append(
        "- withheld: "
        + (", ".join(report.withheld_data_classes) if report.withheld_data_classes else "none")
    )
    lines.extend(["", "Memory counts"])
    for scope, count in sorted(report.memory_counts_by_scope.items()):
        lines.append(f"- {scope}: {count}")
    lines.extend(["", "Recent timeline"])
    if report.recent_timeline_summary:
        for attempt in report.recent_timeline_summary:
            lines.append(
                f"- {attempt.outcome}: {attempt.summary} ({attempt.source}/{attempt.type})"
            )
    else:
        lines.append("- No recent visible events.")
    lines.extend(["", "Latest policy reasons"])
    lines.extend(_bullet_lines(report.latest_policy_reasons, empty="No policy reasons recorded."))
    preview = report.continuity_packet_preview
    lines.extend(
        [
            "",
            "Continuity Packet preview",
            f"- goal: {preview.active_goal or 'none'}",
            f"- artifacts: {preview.artifact_count}",
            f"- attempts: {preview.attempt_count}",
            f"- blockers: {preview.blocker_count}",
            f"- withheld_context: {preview.withheld_context_count}",
        ]
    )
    if preview.suggested_next_steps:
        lines.append("- suggested_next_steps:")
        lines.extend(f"  - {step}" for step in preview.suggested_next_steps)
    if preview.unknowns:
        lines.append("- unknowns:")
        lines.extend(f"  - {unknown}" for unknown in preview.unknowns)
    lines.extend(["", "Context quality"])
    if report.context_quality_summary is None:
        lines.append("- No context quality summary available.")
    else:
        quality = report.context_quality_summary
        lines.append(f"- feedback_count: {quality.feedback_count}")
        lines.append(f"- phase: {quality.phase}")
        lines.append(f"- ranking_or_scoring: {quality.ranking_or_scoring}")
        lines.append(f"- score: {quality.score:.2f}")
        if quality.category_counts:
            lines.append("- category_counts:")
            for category, count in quality.category_counts.items():
                lines.append(f"  - {category}: {count}")
        lines.extend(_bullet_lines(quality.latest_notes, empty="No context feedback recorded."))
        if quality.risk_notes:
            lines.append("- risk_notes:")
            lines.extend(f"  - {note}" for note in quality.risk_notes)
        if quality.suggested_next_actions:
            lines.append("- suggested_next_actions:")
            lines.extend(f"  - {action}" for action in quality.suggested_next_actions)
    lines.extend(["", "Next commands"])
    lines.extend(_bullet_lines(report.next_commands, empty="devcd doctor"))
    return "\n".join(lines)


def _bullet_lines(values: list[str], *, empty: str) -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- {value}" for value in values]


def _dedupe_strings(values: Iterable[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped


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
        return self._context_quality_report(self._read_feedback())

    def create_context_control_report(
        self,
        surface: AgentContextSurface | None = None,
        *,
        context_pack: str = "developer",
        include_empty_guidance: bool = True,
    ) -> ContextControlReport:
        pack = get_context_pack(context_pack)
        requested_surface = surface or AgentContextSurface(
            kind=SurfaceKind.CODING_AGENT,
            name="devcd-control",
        )
        work_state = self.get_work_state()
        brief = self.create_context_brief(requested_surface)
        packet = self.create_continuity_packet_from_brief(brief, context_pack=pack.id)
        if include_empty_guidance:
            packet = _with_empty_passport_guidance(packet)
        quality = self.get_context_quality()
        visible_sources = sorted(
            set(work_state.policy_summary.included_sources)
            | set(brief.policy_decision.included_sources)
        )
        withheld_sources = self._dedupe_withheld_context(brief.withheld_context)
        included_data_classes = sorted(
            set(work_state.policy_summary.included_data_classes)
            | set(brief.policy_decision.included_data_classes)
        )
        withheld_data_classes = sorted(
            set(work_state.policy_summary.withheld_data_classes)
            | set(brief.policy_decision.withheld_data_classes)
        )
        return ContextControlReport(
            active_goal=brief.active_goal,
            selected_pack=pack.id,
            selected_surface=brief.surface.kind.value,
            confidence=brief.confidence,
            visible_sources=visible_sources,
            withheld_sources=withheld_sources,
            included_data_classes=included_data_classes,
            withheld_data_classes=withheld_data_classes,
            memory_counts_by_scope=self._memory_counts_by_scope(),
            recent_timeline_summary=work_state.recent_attempts[:8],
            latest_policy_reasons=self._latest_policy_reasons(
                work_state=work_state,
                brief=brief,
                withheld=withheld_sources,
            ),
            continuity_packet_preview=ContextControlContinuityPreview(
                context_pack=packet.context_pack,
                surface=packet.surface,
                active_goal=packet.intent.summary if packet.intent is not None else None,
                confidence=packet.confidence,
                artifact_count=len(packet.artifacts),
                attempt_count=len(packet.attempts),
                blocker_count=len(packet.blockers),
                withheld_context_count=len(packet.withheld_context),
                suggested_next_steps=packet.suggested_next_steps[:5],
                unknowns=packet.unknowns[:5],
            ),
            context_quality_summary=ContextControlQualitySummary(
                feedback_count=len(quality.feedback),
                phase=quality.phase,
                ranking_or_scoring=quality.ranking_or_scoring,
                score=quality.score,
                category_counts=quality.category_counts,
                latest_notes=brief.context_quality_notes[:5],
                risk_notes=quality.risk_notes[:5],
                suggested_next_actions=quality.suggested_next_actions[:5],
            ),
            next_commands=self._context_control_next_commands(
                surface=brief.surface.kind.value,
                context_pack=pack.id,
                has_visible_context=_continuity_packet_has_visible_context(packet),
            ),
        )

    def create_continuity_packet_from_brief(
        self,
        brief: ContextBrief,
        *,
        context_pack: str = "developer",
    ) -> ContinuityPacket:
        get_context_pack(context_pack)
        packet = continuity_packet_from_context_brief(brief, context_pack=context_pack)
        if context_pack != "research":
            return packet

        surface_definition = self._surface_definition(brief.surface)
        entries = self._memory_for_surface(surface_definition)
        return self._research_continuity_packet(packet, entries)

    def create_continuity_packet(
        self,
        surface: AgentContextSurface | None = None,
        *,
        context_pack: str = "developer",
        include_empty_guidance: bool = False,
    ) -> ContinuityPacket:
        brief = self.create_context_brief(surface)
        packet = self.create_continuity_packet_from_brief(
            brief,
            context_pack=context_pack,
        )
        if include_empty_guidance:
            return _with_empty_passport_guidance(packet)
        return packet

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
        quality = self.get_context_quality()
        suggested_next_steps = self._quality_suggestions(
            quality=quality,
            existing=suggested_next_steps,
        )
        resurrection = self._resurrection_context(
            entries=surface_memory,
            active_goal=active_goal,
            blockers=blockers,
            suggested_next_steps=suggested_next_steps,
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
            resurrection=resurrection,
            withheld_context=withheld,
            withheld=withheld,
            agent_limitations=self._agent_limitations(
                active_goal=active_goal,
                git_context=git_context,
                withheld=withheld,
                export_allowed=export_decision.allowed,
            ),
            context_quality_notes=self._context_quality_notes(quality),
            policy_decision=policy_summary,
            confidence=round(work_state.confidence * quality.score, 2),
        )

    def _context_quality_report(
        self,
        feedback_items: list[ContextFeedback],
    ) -> ContextQualityReport:
        category_counts = {kind.value: 0 for kind in ContextFeedbackKind}
        for feedback in feedback_items:
            category_counts[feedback.kind.value] += 1
        penalty = sum(
            _QUALITY_PENALTIES[kind] * category_counts[kind.value] for kind in ContextFeedbackKind
        )
        summary_notes = self._quality_summary_notes(category_counts)
        risk_notes = self._quality_risk_notes(category_counts)
        suggested_next_actions = (
            [_MISSING_CONTEXT_NEXT_ACTION]
            if category_counts[ContextFeedbackKind.MISSING.value] > 0
            else []
        )
        return ContextQualityReport(
            feedback=feedback_items,
            score=round(max(0.0, 1.0 - penalty), 2),
            category_counts=category_counts,
            summary_notes=summary_notes,
            risk_notes=risk_notes,
            suggested_next_actions=suggested_next_actions,
            withheld_feedback_count=sum(1 for feedback in feedback_items if feedback.note_withheld),
        )

    def _quality_summary_notes(self, category_counts: dict[str, int]) -> list[str]:
        labels = {
            ContextFeedbackKind.MISSING: (
                "missing feedback item indicates the next packet lacks expected context",
                "missing feedback items indicate the next packet lacks expected context",
            ),
            ContextFeedbackKind.WRONG: (
                "wrong feedback item indicates visible context may be incorrect",
                "wrong feedback items indicate visible context may be incorrect",
            ),
            ContextFeedbackKind.STALE: (
                "stale feedback item indicates visible context may be outdated",
                "stale feedback items indicate visible context may be outdated",
            ),
            ContextFeedbackKind.TOO_BROAD: (
                "too_broad feedback item indicates the next packet may include too much context",
                "too_broad feedback items indicate the next packet may include too much context",
            ),
            ContextFeedbackKind.TOO_SENSITIVE: (
                "too_sensitive feedback item indicates the next packet may expose "
                "sensitive context",
                "too_sensitive feedback items indicate the next packet may expose "
                "sensitive context",
            ),
        }
        notes: list[str] = []
        for kind in ContextFeedbackKind:
            count = category_counts[kind.value]
            if count == 0:
                continue
            singular, plural = labels[kind]
            label = singular if count == 1 else plural
            notes.append(f"{count} {label}.")
        return notes

    def _quality_risk_notes(self, category_counts: dict[str, int]) -> list[str]:
        risk_notes: list[str] = []
        if category_counts[ContextFeedbackKind.MISSING.value] > 0:
            risk_notes.append("Context may be incomplete because missing feedback was recorded.")
        if category_counts[ContextFeedbackKind.WRONG.value] > 0:
            risk_notes.append("Context may be incorrect because wrong feedback was recorded.")
        if category_counts[ContextFeedbackKind.STALE.value] > 0:
            risk_notes.append("Context may be stale because stale feedback was recorded.")
        if category_counts[ContextFeedbackKind.TOO_BROAD.value] > 0:
            risk_notes.append("Context may be too broad because too_broad feedback was recorded.")
        if category_counts[ContextFeedbackKind.TOO_SENSITIVE.value] > 0:
            risk_notes.append(
                "Context may be too sensitive because too_sensitive feedback was recorded."
            )
        return risk_notes

    def _quality_suggestions(
        self,
        *,
        quality: ContextQualityReport,
        existing: list[ProactiveSuggestion],
    ) -> list[ProactiveSuggestion]:
        suggestions = list(existing)
        seen = {suggestion.summary for suggestion in suggestions}
        for action in quality.suggested_next_actions:
            if action in seen or len(suggestions) == 3:
                continue
            suggestions.append(
                ProactiveSuggestion(
                    id=f"context-quality-{self._slug(action)}",
                    summary=action,
                    rationale="Local context feedback marked required context as missing.",
                    confidence=quality.score,
                    status=ProactiveSuggestionStatus.ACTIVE,
                    created_at=quality.generated_at,
                )
            )
            seen.add(action)
        return suggestions

    def _context_quality_notes(self, quality: ContextQualityReport) -> list[str]:
        notes: list[str] = []
        notes.extend(quality.summary_notes)
        notes.extend(quality.risk_notes)
        for feedback in quality.feedback[-5:]:
            note_state = (
                "note withheld by policy" if feedback.note_withheld else "note stored locally"
            )
            notes.append(
                f"{feedback.brief_id}: {feedback.kind.value} feedback recorded; {note_state}."
            )
        return notes

    def _memory_counts_by_scope(self) -> dict[str, int]:
        return {
            scope.value: len(
                self.memory_store.list_by_scope(
                    scope,
                    self.state_engine.is_source_visible,
                )
            )
            for scope in MemoryScope
        }

    def _dedupe_withheld_context(
        self,
        withheld: list[WithheldContext],
    ) -> list[WithheldContext]:
        deduped: list[WithheldContext] = []
        seen: set[tuple[str, str, str]] = set()
        for item in withheld:
            key = (
                item.category or item.kind,
                item.policy_reason or item.reason,
                item.safe_summary,
            )
            if key in seen:
                continue
            deduped.append(item)
            seen.add(key)
        return deduped

    def _latest_policy_reasons(
        self,
        *,
        work_state: WorkState,
        brief: ContextBrief,
        withheld: list[WithheldContext],
    ) -> list[str]:
        reasons = [work_state.policy_summary.reason, brief.policy_decision.reason]
        reasons.extend(attempt.policy_reason for attempt in work_state.recent_attempts[:5])
        reasons.extend(item.policy_reason or item.reason for item in withheld[:5])
        return _dedupe_strings(reason for reason in reasons if reason)

    def _context_control_next_commands(
        self,
        *,
        surface: str,
        context_pack: str,
        has_visible_context: bool,
    ) -> list[str]:
        if not has_visible_context:
            return list(_EMPTY_CONTROL_NEXT_STEPS)
        return [
            f"devcd context passport --surface {surface} --pack {context_pack}",
            "devcd context memory",
            "devcd context quality",
            "devcd doctor",
        ]

    def _surface_definition(
        self,
        surface: AgentContextSurface,
    ) -> ContextSurfaceDefinition:
        definition = _CONTEXT_SURFACES.get(surface.kind)
        if definition is not None:
            return definition
        if surface.kind is SurfaceKind.MCP:
            return ContextSurfaceDefinition(
                kind=surface.kind,
                detail_level=surface.detail_level,
                allowed_state_areas=_ALL_STATE_AREAS,
                allowed_memory_scopes=(MemoryScope.WORKING, MemoryScope.EPISODIC),
            )
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
        latest_goal = self._latest_payload_value_any(
            entries,
            (
                ("goal_update", "current_goal"),
                ("research_goal", "current_goal"),
                ("research_goal", "goal"),
            ),
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

    def _resurrection_context(
        self,
        *,
        entries: list[MemoryEntry],
        active_goal: str | None,
        blockers: list[BlockerSignal],
        suggested_next_steps: list[ProactiveSuggestion],
    ) -> AgentResurrectionContext:
        last_failure = self._latest_failure_context(entries, blockers)
        failure_timestamp = last_failure.timestamp if last_failure else None
        last_attempt = self._latest_attempt_context(entries)
        last_fix = self._latest_fix_before_failure(entries, failure_timestamp)
        resolving_attempt = self._latest_success_after_failure(entries, failure_timestamp)
        explicit_do_not_repeat = self._explicit_do_not_repeat(entries, last_failure)
        do_not_repeat = explicit_do_not_repeat
        if not do_not_repeat and last_fix is not None and last_failure is not None:
            do_not_repeat = [f"Do not repeat the last attempted fix unchanged: {last_fix.summary}"]
        elif (
            not do_not_repeat
            and last_failure is not None
            and self._is_failure_event_type(last_failure.type)
        ):
            do_not_repeat = [f"Do not repeat the failed attempt unchanged: {last_failure.summary}"]

        explicit_suggested_next_action = self._explicit_suggested_next_action(
            entries,
            last_failure,
        )
        suggested_next_action = None
        if resolving_attempt is not None:
            suggested_next_action = (
                f"Continue from the successful attempt: {resolving_attempt.summary}"
            )
        elif explicit_suggested_next_action is not None:
            suggested_next_action = explicit_suggested_next_action
        elif suggested_next_steps:
            suggested_next_action = suggested_next_steps[0].summary
        elif last_failure is not None:
            suggested_next_action = f"Investigate {last_failure.summary}"

        why_attempt_failed = self._why_attempt_failed(
            entries,
            last_failure,
            last_fix,
            resolving_attempt,
        )
        unknowns = ["Original chat history is not available in the handoff packet."]
        if last_fix is None:
            unknowns.append("No prior attempted fix is visible in policy-allowed context.")
        if not blockers and last_failure is None:
            unknowns.append("No unresolved failure is visible in policy-allowed context.")

        return AgentResurrectionContext(
            current_goal=active_goal,
            last_attempt=last_attempt,
            last_failure=last_failure.summary if last_failure is not None else None,
            last_attempted_fix=last_fix.summary if last_fix is not None else None,
            why_attempt_failed=why_attempt_failed,
            why_it_failed=why_attempt_failed,
            do_not_repeat=do_not_repeat,
            suggested_next_action=suggested_next_action,
            unknowns=unknowns,
        )

    def _latest_failure_context(
        self,
        entries: list[MemoryEntry],
        blockers: list[BlockerSignal],
    ) -> RecentAttempt | None:
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            event_type = self._string_from_content(entry.content, "type")
            if event_type is None or not self._is_failure_event_type(event_type):
                continue
            reason = self._payload_value(entry.content, "reason")
            attempt_summary = self._attempt_summary(entry.content)
            if isinstance(reason, str) and reason:
                summary = reason
            elif attempt_summary is not None:
                summary = attempt_summary
            else:
                summary = self._summary_from_content(entry.content)
            return self._recent_attempt_from_entry(entry, event_type, summary)
        if blockers:
            return RecentAttempt(
                timestamp=blockers[0].detected_at,
                source="state",
                type="blocker",
                summary=blockers[0].summary,
                outcome="failure",
                policy_reason="visible blocker signal is allowed by policy",
            )
        return None

    def _latest_attempt_context(self, entries: list[MemoryEntry]) -> RecentAttempt | None:
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            event_type = self._string_from_content(entry.content, "type")
            if event_type is None or not self._is_attempt_event_type(event_type):
                continue
            summary = self._attempt_summary(entry.content)
            if summary is None:
                summary = self._summary_from_content(entry.content)
            return self._recent_attempt_from_entry(entry, event_type, summary)
        return None

    def _latest_fix_before_failure(
        self,
        entries: list[MemoryEntry],
        failure_timestamp: datetime | None,
    ) -> RecentAttempt | None:
        fix_events = {"fix_attempt", "code_change", "patch_apply", "commit"}
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if failure_timestamp is not None and entry.timestamp >= failure_timestamp:
                continue
            event_type = self._string_from_content(entry.content, "type")
            if event_type not in fix_events:
                continue
            summary = self._attempt_summary(entry.content)
            if summary is not None:
                return self._recent_attempt_from_entry(entry, event_type, summary)
        return None

    def _latest_success_after_failure(
        self,
        entries: list[MemoryEntry],
        failure_timestamp: datetime | None,
    ) -> RecentAttempt | None:
        if failure_timestamp is None:
            return None
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if entry.timestamp <= failure_timestamp:
                continue
            event_type = self._string_from_content(entry.content, "type")
            if event_type is None or self._outcome_for_action(event_type) != "success":
                continue
            summary = self._attempt_summary(entry.content)
            if summary is not None:
                return self._recent_attempt_from_entry(entry, event_type, summary)
        return None

    def _recent_attempt_from_entry(
        self,
        entry: MemoryEntry,
        event_type: str,
        summary: str,
    ) -> RecentAttempt:
        return RecentAttempt(
            timestamp=entry.timestamp,
            source=entry.source or "unknown",
            type=event_type,
            summary=summary,
            outcome=self._outcome_for_action(event_type),
            policy_reason=entry.policy_reason or "local context attempt is visible by policy",
        )

    def _is_attempt_event_type(self, event_type: str) -> bool:
        if event_type in {"code_change", "commit", "patch_apply", "test_failure"}:
            return True
        return event_type.endswith(("_attempt", "_failure", "_success"))

    def _is_failure_event_type(self, event_type: str) -> bool:
        return event_type in {"failed_attempt", "test_failure"} or event_type.endswith("failure")

    def _attempt_summary(self, content: dict[str, Any]) -> str | None:
        for key in ("summary", "change", "message", "reason", "command"):
            value = self._payload_value(content, key)
            if isinstance(value, str) and value.strip():
                return value
        summary = self._summary_from_content(content)
        return summary if summary else None

    def _explicit_do_not_repeat(
        self,
        entries: list[MemoryEntry],
        last_failure: RecentAttempt | None,
    ) -> list[str]:
        if last_failure is None:
            return []
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if entry.timestamp != last_failure.timestamp:
                continue
            value = self._payload_value(entry.content, "do_not_repeat")
            if isinstance(value, str) and value.strip():
                return [value]
            if isinstance(value, list):
                return [item for item in value if isinstance(item, str) and item.strip()]
        return []

    def _explicit_suggested_next_action(
        self,
        entries: list[MemoryEntry],
        last_failure: RecentAttempt | None,
    ) -> str | None:
        if last_failure is None:
            return None
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if entry.timestamp != last_failure.timestamp:
                continue
            value = self._payload_value(entry.content, "suggested_next_action")
            if isinstance(value, str) and value.strip():
                return value
        return None

    def _why_attempt_failed(
        self,
        entries: list[MemoryEntry],
        last_failure: RecentAttempt | None,
        last_fix: RecentAttempt | None,
        resolving_attempt: RecentAttempt | None,
    ) -> str | None:
        if last_failure is None:
            return None
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if entry.timestamp != last_failure.timestamp:
                continue
            value = self._payload_value(entry.content, "why_attempt_failed")
            if isinstance(value, str) and value.strip():
                return value
            value = self._payload_value(entry.content, "why_failed")
            if isinstance(value, str) and value.strip():
                return value
        if resolving_attempt is not None and resolving_attempt.timestamp > last_failure.timestamp:
            return (
                "The latest visible failure was followed by a successful attempt, so it "
                f"appears resolved by: {resolving_attempt.summary}"
            )
        if last_fix is not None and last_failure.timestamp > last_fix.timestamp:
            return (
                "The latest failure happened after the attempted fix, so the fix did not "
                f"resolve the blocker: {last_failure.summary}"
            )
        return f"The latest visible blocker is still unresolved: {last_failure.summary}"

    def _brief_summary(self, work_state: WorkState) -> str:
        if work_state.active_intent is None:
            return "No active intent could be inferred with enough confidence."
        return f"Working on {work_state.active_intent.summary}."

    def _active_intent(
        self,
        entries: list[MemoryEntry],
        evidence: list[EvidenceItem],
    ) -> IntentLine | None:
        latest_goal = self._latest_payload_value_any(
            entries,
            (
                ("goal_update", "current_goal"),
                ("research_goal", "current_goal"),
                ("research_goal", "goal"),
            ),
        )
        latest_branch = self._latest_payload_value(
            entries, event_type="branch_change", key="branch"
        )
        intent_source = latest_branch or latest_goal
        if intent_source is None:
            return None

        summary, timestamp, event_type = intent_source
        return IntentLine(
            summary=summary,
            evidence=self._evidence_for_event_type(evidence, event_type),
            started_at=timestamp,
            updated_at=timestamp,
            confidence=0.9 if event_type in {"goal_update", "research_goal"} else 0.6,
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
        latest_goal = self._latest_payload_value_any(
            entries,
            (
                ("goal_update", "current_goal"),
                ("research_goal", "current_goal"),
                ("research_goal", "goal"),
            ),
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
            event_type = self._string_from_content(entry.content, "type")
            if event_type == "source_review":
                artifact = self._research_source_artifact(entry)
                if artifact is not None:
                    artifacts.append(artifact)
                continue
            if event_type == "note_update":
                artifact = self._research_note_artifact(entry)
                if artifact is not None:
                    artifacts.append(artifact)
                continue
            if event_type not in {"file_focus", "artifact_ref"}:
                continue
            file_path = self._payload_value(entry.content, "path") or self._payload_value(
                entry.content,
                "artifact",
            )
            if not isinstance(file_path, str) or not file_path:
                continue
            artifact_summary = self._payload_value(entry.content, "summary")
            if not isinstance(artifact_summary, str) or not artifact_summary:
                artifact_summary = file_path
            artifacts.append(
                RelevantArtifact(
                    kind="file",
                    identifier=file_path,
                    summary=f"{event_type}: {artifact_summary}",
                    source=entry.source or "unknown",
                    relevance=0.8,
                    last_seen_at=entry.timestamp,
                    policy_reason=entry.policy_reason
                    or "local context artifact is visible by policy",
                )
            )
        return artifacts

    def _research_source_artifact(self, entry: MemoryEntry) -> RelevantArtifact | None:
        identifier = self._first_payload_string(
            entry.content,
            ("source_id", "citation_key", "doi", "url", "title"),
        )
        if identifier is None:
            return None
        kind = self._payload_value(entry.content, "kind")
        summary = self._research_payload_summary(
            entry.content,
            ("summary", "title", "claim", "finding"),
        )
        return RelevantArtifact(
            kind=kind if isinstance(kind, str) and kind.strip() else "source",
            identifier=identifier,
            summary=summary or f"source_review: {identifier}",
            source=entry.source or "unknown",
            relevance=0.85,
            last_seen_at=entry.timestamp,
            policy_reason=entry.policy_reason or "source metadata is visible by policy",
        )

    def _research_note_artifact(self, entry: MemoryEntry) -> RelevantArtifact | None:
        identifier = self._first_payload_string(entry.content, ("reference", "title"))
        if identifier is None:
            return None
        summary = self._research_payload_summary(entry.content, ("summary", "title"))
        return RelevantArtifact(
            kind="note",
            identifier=identifier,
            summary=summary or f"note_update: {identifier}",
            source=entry.source or "unknown",
            relevance=0.7,
            last_seen_at=entry.timestamp,
            policy_reason=entry.policy_reason or "note metadata is visible by policy",
        )

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
            event_type = self._string_from_content(entry.content, "type")
            if event_type not in {"test_failure", "failed_attempt"}:
                continue
            reason = self._payload_value(entry.content, "reason") or self._payload_value(
                entry.content, "summary"
            )
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
    ) -> tuple[str, datetime, str] | None:
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            if self._string_from_content(entry.content, "type") != event_type:
                continue
            value = self._payload_value(entry.content, key)
            if isinstance(value, str) and value.strip():
                return value, entry.timestamp, event_type
        return None

    def _latest_payload_value_any(
        self,
        entries: list[MemoryEntry],
        candidates: tuple[tuple[str, str], ...],
    ) -> tuple[str, datetime, str] | None:
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            event_type = self._string_from_content(entry.content, "type")
            for candidate_event_type, key in candidates:
                if event_type != candidate_event_type:
                    continue
                value = self._payload_value(entry.content, key)
                if isinstance(value, str) and value.strip():
                    return value, entry.timestamp, candidate_event_type
        return None

    def _first_payload_string(
        self,
        content: dict[str, Any],
        keys: tuple[str, ...],
    ) -> str | None:
        for key in keys:
            value = self._payload_value(content, key)
            if isinstance(value, str) and value.strip():
                return value
        return None

    def _research_payload_summary(
        self,
        content: dict[str, Any],
        keys: tuple[str, ...],
    ) -> str | None:
        value = self._first_payload_string(content, keys)
        if value is not None:
            return value
        summary = self._summary_from_content(content)
        return summary if summary else None

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
                or payload.get("summary")
                or payload.get("title")
                or payload.get("source_id")
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
        if self._is_failure_event_type(action_type):
            return "failure"
        if action_type.endswith("success"):
            return "success"
        return "unknown"

    def _research_continuity_packet(
        self,
        packet: ContinuityPacket,
        entries: list[MemoryEntry],
    ) -> ContinuityPacket:
        decisions = self._dedupe_continuity_decisions(self._research_decisions(entries))
        research_attempts = self._research_attempts(entries)
        research_attempt_keys = {
            (attempt.timestamp, attempt.source, attempt.type) for attempt in research_attempts
        }
        attempts = self._dedupe_continuity_attempts(
            [
                *research_attempts,
                *[
                    attempt
                    for attempt in packet.attempts
                    if attempt.type in {"failed_attempt", "hypothesis_check"}
                    and (attempt.timestamp, attempt.source, attempt.type)
                    not in research_attempt_keys
                ],
            ]
        )
        failed_attempt = next(
            (attempt for attempt in attempts if attempt.outcome == "failure"),
            None,
        )
        blockers = packet.blockers
        if not blockers and failed_attempt is not None:
            blockers = [
                ContinuityBlocker(
                    kind="failed_approach",
                    summary=failed_attempt.summary,
                    confidence=0.8,
                    detected_at=failed_attempt.timestamp,
                    reason=failed_attempt.failure_reason,
                    policy_reason=failed_attempt.policy_reason,
                )
            ]

        do_not_repeat = packet.do_not_repeat or self._research_do_not_repeat(entries)
        suggested_next_steps = packet.suggested_next_steps or self._research_suggested_next_steps(
            entries
        )
        unknowns = [
            unknown
            for unknown in packet.unknowns
            if unknown != "No prior attempted fix is visible in policy-allowed context."
        ]
        pack_metadata = dict(packet.pack_metadata)
        pack_metadata["research"] = {
            "current_hypothesis": self._current_research_hypothesis(decisions),
            "reviewed_source_count": sum(
                1 for artifact in packet.artifacts if artifact.kind == "source"
            ),
        }
        return packet.model_copy(
            update={
                "decisions": decisions,
                "attempts": attempts,
                "blockers": blockers,
                "do_not_repeat": do_not_repeat,
                "suggested_next_steps": suggested_next_steps,
                "unknowns": unknowns,
                "pack_metadata": pack_metadata,
            }
        )

    def _research_decisions(self, entries: list[MemoryEntry]) -> list[ContinuityDecision]:
        decisions: list[ContinuityDecision] = []
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            event_type = self._string_from_content(entry.content, "type")
            if event_type not in {"hypothesis", "decision"}:
                continue
            summary = self._research_payload_summary(
                entry.content,
                ("summary", "hypothesis", "decision", "title"),
            )
            if summary is None:
                continue
            decisions.append(
                ContinuityDecision(
                    kind=event_type,
                    summary=summary,
                    source=entry.source or "unknown",
                    decided_at=entry.timestamp,
                    policy_reason=(
                        entry.policy_reason or "research decision metadata is visible by policy"
                    ),
                )
            )
        return decisions

    def _research_attempts(self, entries: list[MemoryEntry]) -> list[ContinuityAttempt]:
        attempts: list[ContinuityAttempt] = []
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            event_type = self._string_from_content(entry.content, "type")
            if event_type not in {"failed_attempt", "hypothesis_check"}:
                continue
            summary = self._attempt_summary(entry.content)
            if summary is None:
                continue
            outcome = self._research_attempt_outcome(entry.content, event_type)
            failure_reason = self._first_payload_string(
                entry.content,
                ("why_attempt_failed", "why_failed", "failure_reason", "reason"),
            )
            attempts.append(
                ContinuityAttempt(
                    timestamp=entry.timestamp,
                    source=entry.source or "unknown",
                    type=event_type,
                    summary=summary,
                    outcome=outcome,
                    failure_reason=failure_reason if outcome == "failure" else None,
                    policy_reason=(
                        entry.policy_reason or "research attempt metadata is visible by policy"
                    ),
                )
            )
        return attempts

    def _research_attempt_outcome(
        self,
        content: dict[str, Any],
        event_type: str,
    ) -> Literal["unknown", "success", "failure", "interrupted"]:
        if event_type == "failed_attempt":
            return "failure"
        outcome = self._payload_value(content, "outcome")
        if outcome == "success":
            return "success"
        if outcome == "failure":
            return "failure"
        if outcome == "interrupted":
            return "interrupted"
        if outcome == "unknown":
            return "unknown"
        return "unknown"

    def _research_do_not_repeat(self, entries: list[MemoryEntry]) -> list[str]:
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            value = self._payload_value(entry.content, "do_not_repeat")
            if isinstance(value, str) and value.strip():
                return [value]
            if isinstance(value, list):
                return [item for item in value if isinstance(item, str) and item.strip()]
        return []

    def _research_suggested_next_steps(self, entries: list[MemoryEntry]) -> list[str]:
        for entry in sorted(entries, key=lambda item: item.timestamp, reverse=True):
            value = self._first_payload_string(
                entry.content,
                ("suggested_next_action", "suggested_next_step", "next_step"),
            )
            if value is not None:
                return [value]
        return []

    def _current_research_hypothesis(self, decisions: list[ContinuityDecision]) -> str | None:
        hypothesis = next(
            (decision for decision in decisions if decision.kind == "hypothesis"),
            None,
        )
        return hypothesis.summary if hypothesis is not None else None

    def _dedupe_continuity_attempts(
        self,
        attempts: list[ContinuityAttempt],
    ) -> list[ContinuityAttempt]:
        deduped: list[ContinuityAttempt] = []
        seen: set[tuple[datetime, str, str, str]] = set()
        for attempt in attempts:
            key = (attempt.timestamp, attempt.source, attempt.type, attempt.summary)
            if key in seen:
                continue
            deduped.append(attempt)
            seen.add(key)
        return deduped

    def _dedupe_continuity_decisions(
        self,
        decisions: list[ContinuityDecision],
    ) -> list[ContinuityDecision]:
        deduped: list[ContinuityDecision] = []
        seen: set[tuple[datetime, str, str, str]] = set()
        for decision in decisions:
            key = (decision.decided_at, decision.kind, decision.source, decision.summary)
            if key in seen:
                continue
            deduped.append(decision)
            seen.add(key)
        return deduped


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

    lines.extend(["## Last attempt"])
    if brief.resurrection.last_attempt is not None:
        attempt = brief.resurrection.last_attempt
        lines.append(f"- {attempt.outcome}: {attempt.summary} ({attempt.source}/{attempt.type})")
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## Last failure"])
    if brief.resurrection.last_failure:
        lines.append(f"- {brief.resurrection.last_failure}")
    elif brief.blockers:
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

    lines.extend(["## Last attempted fix"])
    lines.append(f"- {brief.resurrection.last_attempted_fix or 'None visible.'}")
    lines.append("")

    lines.extend(["## why_attempt_failed"])
    lines.append(f"- {brief.resurrection.why_attempt_failed or 'Unknown from visible context.'}")
    lines.append("")

    lines.extend(["## do_not_repeat"])
    if brief.resurrection.do_not_repeat:
        for item in brief.resurrection.do_not_repeat:
            lines.append(f"- {item}")
    else:
        lines.append("- No repeated failed fix pattern is visible.")
    lines.append("")

    lines.extend(["## Suggested next action"])
    if brief.resurrection.suggested_next_action:
        lines.append(f"- {brief.resurrection.suggested_next_action}")
    elif brief.suggested_next_steps:
        lines.append(f"- {brief.suggested_next_steps[0].summary}")
    else:
        lines.append("- Continue from the active goal using visible artifacts and attempts.")
    lines.append("")

    lines.extend(["## unknowns"])
    if brief.resurrection.unknowns:
        for unknown in brief.resurrection.unknowns:
            lines.append(f"- {unknown}")
    else:
        lines.append("- No unknowns were inferred from visible context.")
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

    lines.extend(["## context_quality_notes"])
    if brief.context_quality_notes:
        for note in brief.context_quality_notes:
            lines.append(f"- {note}")
    else:
        lines.append("- No context feedback recorded.")
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


def render_context_brief_json(brief: ContextBrief) -> str:
    """Return the brief as a machine-readable JSON contract (no sensitive payloads)."""
    return render_agent_handoff_packet_json(continuity_packet_from_context_brief(brief))


def render_continuity_packet_json(packet: ContinuityPacket) -> str:
    return packet.model_dump_json(indent=2)


def render_continuity_packet_markdown(packet: ContinuityPacket) -> str:
    if packet.context_pack == "research":
        return _render_research_continuity_packet_markdown(packet)
    return _render_generic_continuity_packet_markdown(packet)


def _render_research_continuity_packet_markdown(packet: ContinuityPacket) -> str:
    lines = ["# DevCD Research Continuity Packet", ""]
    lines.extend(["## packet_id", packet.id, ""])
    lines.extend(["## context_pack", packet.context_pack, ""])
    lines.extend(
        [
            "## research_goal",
            packet.intent.summary if packet.intent is not None else "No research goal visible.",
            "",
        ]
    )

    lines.extend(["## reviewed_sources"])
    source_artifacts = [artifact for artifact in packet.artifacts if artifact.kind == "source"]
    if source_artifacts:
        for artifact in source_artifacts:
            lines.append(f"- source: {artifact.identifier} - {artifact.summary}")
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## current_hypothesis"])
    hypothesis = next(
        (decision for decision in packet.decisions if decision.kind == "hypothesis"),
        None,
    )
    if hypothesis is not None:
        lines.append(f"- {hypothesis.summary}")
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## decisions"])
    non_hypothesis_decisions = [
        decision for decision in packet.decisions if decision.kind != "hypothesis"
    ]
    if non_hypothesis_decisions:
        for decision in non_hypothesis_decisions:
            lines.append(f"- {decision.kind}: {decision.summary}")
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## already_tried"])
    if packet.attempts:
        for attempt in packet.attempts[:5]:
            lines.append(
                f"- {attempt.outcome}: {attempt.summary} ({attempt.source}/{attempt.type})"
            )
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## failed_approach"])
    failed_attempt = next(
        (attempt for attempt in packet.attempts if attempt.outcome == "failure"),
        None,
    )
    if failed_attempt is not None:
        lines.append(f"- {failed_attempt.summary}")
        if failed_attempt.failure_reason:
            lines.append(f"  why_failed: {failed_attempt.failure_reason}")
    else:
        lines.append("- None detected.")
    lines.append("")

    lines.extend(["## do_not_repeat"])
    if packet.do_not_repeat:
        for item in packet.do_not_repeat:
            lines.append(f"- {item}")
    else:
        lines.append("- No failed research pattern is visible.")
    lines.append("")

    lines.extend(["## suggested_next_steps"])
    if packet.suggested_next_steps:
        for step in packet.suggested_next_steps:
            lines.append(f"- {step}")
    else:
        lines.append("- Continue from the research goal using visible source metadata.")
    lines.append("")

    lines.extend(["## unknowns"])
    if packet.unknowns:
        for unknown in packet.unknowns:
            lines.append(f"- {unknown}")
    else:
        lines.append("- No unknowns were inferred from visible context.")
    lines.append("")

    lines.extend(["## context_quality_notes"])
    if packet.context_quality_notes:
        for note in packet.context_quality_notes:
            lines.append(f"- {note}")
    else:
        lines.append("- No context feedback recorded.")
    lines.append("")

    lines.extend(["## withheld_context"])
    if packet.withheld_context:
        for withheld in packet.withheld_context:
            lines.append(f"- category: {withheld.category or withheld.kind}")
            lines.append(f"  policy_reason: {withheld.policy_reason or withheld.reason}")
            lines.append(
                f"  safe_summary: {withheld.safe_summary or 'No safe replacement available.'}"
            )
    else:
        lines.append("- None withheld for this packet.")
    lines.append("")

    lines.extend(["## policy_decision"])
    lines.append(f"- allowed: {str(packet.policy_decision.allowed).lower()}")
    lines.append(f"- operation: {packet.policy_decision.operation}")
    lines.append(f"- reason: {packet.policy_decision.reason}")
    return "\n".join(lines) + "\n"


def _render_generic_continuity_packet_markdown(packet: ContinuityPacket) -> str:
    lines = ["# DevCD Agent Passport", ""]
    lines.extend(["## packet_id", packet.id, ""])
    lines.extend(["## context_pack", packet.context_pack, ""])
    lines.extend(["## surface", packet.surface, ""])
    lines.extend(
        [
            "## goal",
            packet.intent.summary if packet.intent is not None else "No goal visible.",
            "",
        ]
    )
    lines.extend(["## artifacts"])
    if packet.artifacts:
        for artifact in packet.artifacts:
            lines.append(f"- {artifact.kind}: {artifact.identifier} - {artifact.summary}")
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## attempts"])
    if packet.attempts:
        for attempt in packet.attempts[:5]:
            lines.append(
                f"- {attempt.outcome}: {attempt.summary} ({attempt.source}/{attempt.type})"
            )
            if attempt.failure_reason:
                lines.append(f"  why_failed: {attempt.failure_reason}")
    else:
        lines.append("- None visible under current policy.")
    lines.append("")

    lines.extend(["## blockers"])
    if packet.blockers:
        for blocker in packet.blockers:
            lines.append(f"- {blocker.summary}")
            if blocker.reason:
                lines.append(f"  reason: {blocker.reason}")
    else:
        lines.append("- None detected.")
    lines.append("")

    lines.extend(["## do_not_repeat"])
    if packet.do_not_repeat:
        for item in packet.do_not_repeat:
            lines.append(f"- {item}")
    else:
        lines.append("- No repeated failed pattern is visible.")
    lines.append("")

    lines.extend(["## suggested_next_steps"])
    if packet.suggested_next_steps:
        for step in packet.suggested_next_steps:
            lines.append(f"- {step}")
    else:
        lines.append("- Continue from the visible goal, artifacts, and attempts.")
    lines.append("")

    lines.extend(["## unknowns"])
    if packet.unknowns:
        for unknown in packet.unknowns:
            lines.append(f"- {unknown}")
    else:
        lines.append("- No unknowns were inferred from visible context.")
    lines.append("")

    lines.extend(["## context_quality_notes"])
    if packet.context_quality_notes:
        for note in packet.context_quality_notes:
            lines.append(f"- {note}")
    else:
        lines.append("- No context feedback recorded.")
    lines.append("")

    lines.extend(["## withheld_context"])
    if packet.withheld_context:
        for withheld in packet.withheld_context:
            lines.append(f"- category: {withheld.category or withheld.kind}")
            lines.append(f"  policy_reason: {withheld.policy_reason or withheld.reason}")
            lines.append(
                f"  safe_summary: {withheld.safe_summary or 'No safe replacement available.'}"
            )
    else:
        lines.append("- None withheld for this packet.")
    lines.append("")

    lines.extend(["## policy_decision"])
    lines.append(f"- allowed: {str(packet.policy_decision.allowed).lower()}")
    lines.append(f"- operation: {packet.policy_decision.operation}")
    lines.append(f"- reason: {packet.policy_decision.reason}")
    return "\n".join(lines) + "\n"


def _with_empty_passport_guidance(packet: ContinuityPacket) -> ContinuityPacket:
    if _continuity_packet_has_visible_context(packet):
        return packet
    unknowns = list(packet.unknowns)
    if _EMPTY_PASSPORT_UNKNOWN not in unknowns:
        unknowns.insert(0, _EMPTY_PASSPORT_UNKNOWN)
    return packet.model_copy(
        update={
            "suggested_next_steps": list(_EMPTY_PASSPORT_NEXT_STEPS),
            "unknowns": unknowns,
        }
    )


def _continuity_packet_has_visible_context(packet: ContinuityPacket) -> bool:
    return bool(
        packet.intent is not None
        or packet.artifacts
        or packet.decisions
        or packet.attempts
        or packet.blockers
        or packet.preferences
        or packet.do_not_repeat
        or packet.withheld_context
    )


def continuity_packet_from_context_brief(
    brief: ContextBrief,
    *,
    context_pack: str = "developer",
) -> ContinuityPacket:
    intent = None
    if brief.active_goal is not None:
        intent = ContinuityIntent(
            summary=brief.active_goal,
            status=IntentStatus.ACTIVE,
            evidence=brief.active_intent.evidence if brief.active_intent is not None else [],
            started_at=brief.active_intent.started_at if brief.active_intent is not None else None,
            updated_at=brief.active_intent.updated_at
            if brief.active_intent is not None
            else brief.generated_at,
            confidence=brief.active_intent.confidence
            if brief.active_intent is not None
            else brief.confidence,
        )
    elif brief.active_intent is not None:
        intent = ContinuityIntent(
            summary=brief.active_intent.summary,
            status=brief.active_intent.status,
            evidence=brief.active_intent.evidence,
            started_at=brief.active_intent.started_at,
            updated_at=brief.active_intent.updated_at,
            confidence=brief.active_intent.confidence,
        )

    attempts: list[ContinuityAttempt] = []
    last_attempt = brief.resurrection.last_attempt or (
        brief.recent_attempts[0] if brief.recent_attempts else None
    )
    if last_attempt is not None:
        attempts.append(
            _continuity_attempt_from_recent_attempt(
                last_attempt,
                failure_reason=brief.resurrection.why_attempt_failed
                if last_attempt.outcome == "failure"
                else None,
            )
        )

    seen_attempts = {
        (attempt.timestamp, attempt.source, attempt.type, attempt.summary) for attempt in attempts
    }
    for attempt in brief.recent_attempts:
        attempt_key = (attempt.timestamp, attempt.source, attempt.type, attempt.summary)
        if attempt_key in seen_attempts:
            continue
        attempts.append(_continuity_attempt_from_recent_attempt(attempt))
        seen_attempts.add(attempt_key)

    blockers = [
        ContinuityBlocker(
            kind="failure" if blocker.summary == brief.resurrection.last_failure else "blocker",
            summary=blocker.summary,
            evidence=blocker.evidence,
            confidence=blocker.confidence,
            detected_at=blocker.detected_at,
            reason=brief.resurrection.why_attempt_failed if index == 0 else None,
            policy_reason="visible blocker signal is allowed by policy",
        )
        for index, blocker in enumerate(brief.blockers)
    ]

    return ContinuityPacket(
        schema_version=brief.schema_version,
        id=brief.id,
        context_pack=context_pack,
        surface=brief.surface.kind.value,
        intent=intent,
        artifacts=[
            ContinuityArtifact(
                kind=artifact.kind,
                identifier=artifact.identifier,
                summary=artifact.summary,
                source=artifact.source,
                relevance=artifact.relevance,
                last_seen_at=artifact.last_seen_at,
                policy_reason=artifact.policy_reason,
            )
            for artifact in brief.relevant_artifacts
        ],
        attempts=attempts,
        blockers=blockers,
        do_not_repeat=brief.resurrection.do_not_repeat,
        suggested_next_steps=_dedupe_strings(
            [
                *(
                    [brief.resurrection.suggested_next_action]
                    if brief.resurrection.suggested_next_action is not None
                    else []
                ),
                *[suggestion.summary for suggestion in brief.suggested_next_steps],
            ]
        ),
        unknowns=brief.resurrection.unknowns,
        context_quality_notes=brief.context_quality_notes,
        withheld_context=brief.withheld_context,
        policy_decision=brief.policy_decision,
        provenance=list(brief.surface.allowed_state_areas),
        pack_metadata={
            "brief_id": brief.id,
            "git_context": brief.git_context.model_dump(mode="json"),
            "resurrection": brief.resurrection.model_dump(mode="json"),
        },
        confidence=brief.confidence,
        generated_at=brief.generated_at,
    )


def _continuity_attempt_from_recent_attempt(
    attempt: RecentAttempt,
    *,
    failure_reason: str | None = None,
) -> ContinuityAttempt:
    return ContinuityAttempt(
        timestamp=attempt.timestamp,
        source=attempt.source,
        type=attempt.type,
        summary=attempt.summary,
        outcome=attempt.outcome,
        failure_reason=failure_reason,
        policy_reason=attempt.policy_reason,
    )


def render_agent_handoff_packet_json(packet: ContinuityPacket) -> str:
    """Render the current developer handoff contract from a continuity packet."""
    contract = agent_handoff_packet_from_continuity_packet(packet)
    return json.dumps(contract, indent=2, ensure_ascii=False)


def agent_handoff_packet_from_continuity_packet(packet: ContinuityPacket) -> dict[str, Any]:
    git_context = _mapping_from_pack_metadata(packet, "git_context")
    resurrection = _mapping_from_pack_metadata(packet, "resurrection")
    last_attempt = None
    if packet.attempts:
        attempt = packet.attempts[0]
        last_attempt = {
            "summary": attempt.summary,
            "outcome": attempt.outcome,
            "source": attempt.source,
            "type": attempt.type,
            "timestamp": attempt.timestamp.isoformat(),
        }

    last_failure = _optional_string(resurrection.get("last_failure"))
    if last_failure is None and packet.blockers:
        last_failure = packet.blockers[0].summary
    why_attempt_failed = _optional_string(resurrection.get("why_attempt_failed"))
    if why_attempt_failed is None and packet.blockers:
        why_attempt_failed = packet.blockers[0].reason

    return {
        "schema_version": packet.schema_version,
        "brief_id": _optional_string(packet.pack_metadata.get("brief_id")) or packet.id,
        "surface": packet.surface,
        "goal": packet.intent.summary if packet.intent is not None else None,
        "relevant_artifacts": [
            {
                "kind": artifact.kind,
                "identifier": artifact.identifier,
                "summary": artifact.summary,
                "relevance": artifact.relevance,
            }
            for artifact in packet.artifacts
        ],
        "git_context": {
            "branch": _optional_string(git_context.get("branch")),
            "latest_commit": _optional_string(git_context.get("latest_commit")),
            "latest_commit_summary": _optional_string(git_context.get("latest_commit_summary")),
            "repository": _optional_string(git_context.get("repository")),
        },
        "last_attempt": last_attempt,
        "last_failure": last_failure,
        "why_attempt_failed": why_attempt_failed,
        "do_not_repeat": packet.do_not_repeat,
        "blockers": [
            {"summary": blocker.summary, "confidence": blocker.confidence}
            for blocker in packet.blockers
        ],
        "suggested_next_action": packet.suggested_next_steps[0]
        if packet.suggested_next_steps
        else None,
        "policy_summary": {
            "allowed": packet.policy_decision.allowed,
            "operation": packet.policy_decision.operation,
            "reason": packet.policy_decision.reason,
            "withheld_sources": packet.policy_decision.withheld_sources,
            "withheld_data_classes": packet.policy_decision.withheld_data_classes,
        },
        "withheld_context_summary": [
            {
                "category": item.category or item.kind,
                "policy_reason": item.policy_reason or item.reason,
                "safe_summary": item.safe_summary or "No safe replacement available.",
            }
            for item in packet.withheld_context
        ],
        "context_quality_notes": packet.context_quality_notes,
        "unknowns": packet.unknowns,
        "confidence": packet.confidence,
    }


def _mapping_from_pack_metadata(packet: ContinuityPacket, key: str) -> dict[str, Any]:
    value = packet.pack_metadata.get(key)
    return value if isinstance(value, dict) else {}


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None
