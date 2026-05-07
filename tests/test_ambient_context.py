from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from devcd.slices.ambient_context.models import (
    AgentContextSurface,
    BlockerSignal,
    ContextBrief,
    ContextFeedbackKind,
    ContextMemoryItem,
    ContinuityArtifact,
    ContinuityAttempt,
    ContinuityBlocker,
    ContinuityDecision,
    ContinuityIntent,
    ContinuityPacket,
    ContinuityPreference,
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
from devcd.slices.ambient_context.service import (
    AmbientContextService,
    continuity_packet_from_context_brief,
    get_context_pack,
    list_context_packs,
    render_agent_handoff_packet_json,
    render_context_brief_json,
    render_context_brief_markdown,
    render_context_packs_json,
    render_continuity_packet_json,
    render_continuity_packet_markdown,
)
from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSource
from devcd.slices.events.recipes import (
    PytestFailure,
    PytestFailureRecipeInput,
    ResearchFailedAttempt,
    ResearchNoteMetadata,
    ResearchSessionRecipeInput,
    ResearchSource,
    events_from_pytest_failure,
    events_from_research_session,
)
from devcd.slices.git_source.service import GitEventSource
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine


def test_ambient_context_test_module_is_available() -> None:
    assert True


def test_foundational_models_capture_policy_safe_evidence() -> None:
    timestamp = datetime(2026, 5, 4, 12, 0, tzinfo=UTC)

    evidence = EvidenceItem(
        source="ide",
        event_type="file_focus",
        summary="file_focus: packages/devcd-core/src/devcd/cli.py",
        timestamp=timestamp,
        policy_reason="observation is allowed by the default local policy",
    )
    freshness = FreshnessState(status=FreshnessStatus.CURRENT, last_seen_at=timestamp)
    policy = PolicySummary(
        allowed=True,
        operation="export",
        reason="local context export is allowed by policy",
        included_sources=["ide"],
        withheld_sources=[],
        included_data_classes=["metadata"],
        withheld_data_classes=[],
    )
    withheld = WithheldContext(kind="source", reason="browser source is not enabled")

    assert evidence.event_type == "file_focus"
    assert freshness.status is FreshnessStatus.CURRENT
    assert policy.allowed is True
    assert withheld.kind == "source"


def test_agent_context_surface_defaults_to_standard_http() -> None:
    surface = AgentContextSurface()

    assert surface.kind == "http"
    assert surface.name == "local-client"
    assert surface.detail_level == "standard"
    assert surface.requested_sources == []
    assert surface.requested_data_classes == ["metadata"]


def test_ambient_context_service_accepts_existing_slice_services(tmp_path) -> None:
    policy_engine = PolicyEngine.default()
    memory_store = MemoryStore.with_default_ttl()
    event_ledger = EventLedger(tmp_path / "events.jsonl")
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)

    service = AmbientContextService(
        state_engine=state_engine,
        memory_store=memory_store,
        policy_engine=policy_engine,
    )

    assert service.state_engine is state_engine


def test_context_feedback_is_stored_locally_without_note_text(tmp_path) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)

    feedback = service.record_feedback(
        brief_id="brief-123",
        kind=ContextFeedbackKind.MISSING,
        note="Add the failing test name to the handoff.",
    )
    quality = service.get_context_quality()

    assert feedback.brief_id == "brief-123"
    assert feedback.kind is ContextFeedbackKind.MISSING
    assert feedback.note is None
    assert feedback.note_withheld is True
    assert feedback.withheld_context[0].category == "payload_content"
    assert quality.feedback == [feedback]
    assert (tmp_path / "context-feedback.jsonl").exists()


def test_context_brief_surfaces_policy_safe_quality_notes_without_feedback_text(tmp_path) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)
    service.record_feedback(
        brief_id="brief-123",
        kind=ContextFeedbackKind.MISSING,
        note="Add the private failing test name to the handoff.",
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))
    markdown = render_context_brief_markdown(brief)
    contract = json.loads(render_context_brief_json(brief))

    assert "brief-123: missing feedback recorded; note withheld by policy." in (
        brief.context_quality_notes
    )
    assert any("missing feedback" in note for note in brief.context_quality_notes)
    assert "## context_quality_notes" in markdown
    assert "brief-123: missing feedback recorded; note withheld by policy." in markdown
    assert contract["context_quality_notes"] == brief.context_quality_notes
    assert "private failing test name" not in markdown
    assert "private failing test name" not in json.dumps(contract)


def test_context_quality_report_computes_deterministic_summary(tmp_path) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)
    baseline = service.get_context_quality()

    service.record_feedback(
        brief_id="brief-123",
        kind=ContextFeedbackKind.MISSING,
        note="Add the private failing test name to the handoff.",
    )
    service.record_feedback(
        brief_id="brief-123",
        kind=ContextFeedbackKind.STALE,
        note="This is based on an old branch.",
    )

    quality = service.get_context_quality()

    assert baseline.score == 1.0
    assert quality.score < baseline.score
    assert quality.category_counts == {
        "missing": 1,
        "stale": 1,
        "wrong": 0,
        "too_broad": 0,
        "too_sensitive": 0,
    }
    assert quality.summary_notes == [
        "1 missing feedback item indicates the next packet lacks expected context.",
        "1 stale feedback item indicates visible context may be outdated.",
    ]
    assert quality.risk_notes == [
        "Context may be incomplete because missing feedback was recorded.",
        "Context may be stale because stale feedback was recorded.",
    ]
    assert quality.suggested_next_actions == [
        "Ask the user which missing context should be recorded before the next handoff."
    ]


def test_feedback_adjusts_next_passport_confidence_and_actions(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={"current_goal": "Ship quality-aware passports"},
        )
    )
    service.record_feedback(
        brief_id="brief-123",
        kind=ContextFeedbackKind.MISSING,
        note="The private repro command is missing.",
    )
    service.record_feedback(
        brief_id="brief-123",
        kind=ContextFeedbackKind.STALE,
        note="The selected file changed after this brief.",
    )

    packet = service.create_continuity_packet(
        AgentContextSurface(kind="coding-agent", name="copilot"),
    )
    contract = json.loads(render_continuity_packet_json(packet))
    markdown = render_continuity_packet_markdown(packet)

    assert packet.intent is not None
    assert packet.confidence < packet.intent.confidence
    assert any("missing feedback" in note for note in packet.context_quality_notes)
    assert any("stale feedback" in note for note in packet.context_quality_notes)
    assert any("missing context" in step for step in packet.suggested_next_steps)
    assert "private repro command" not in markdown
    assert "private repro command" not in json.dumps(contract)
    assert contract["context_quality_notes"] == packet.context_quality_notes
    assert "## context_quality_notes" in markdown


def test_continuity_packet_includes_context_budget_and_session_contract(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={"current_goal": "Ship curated context budgets"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.IDE,
            type="file_focus",
            timestamp=datetime(2026, 5, 5, 10, 1, tzinfo=UTC),
            payload={"path": "packages/devcd-core/src/devcd/slices/ambient_context/service.py"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 5, 10, 2, tzinfo=UTC),
            payload={
                "reason": "budget report missing from passport",
                "suggested_next_action": "Add the context budget fields first",
            },
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.NOTES,
            type="note_update",
            timestamp=datetime(2026, 5, 5, 10, 3, tzinfo=UTC),
            payload={"title": "PRIVATE_NOTE_PAYLOAD"},
            sensitivity="sensitive",
        )
    )

    packet = service.create_continuity_packet(
        AgentContextSurface(kind="coding-agent", name="copilot"),
        include_empty_guidance=True,
    )
    body = json.loads(render_continuity_packet_json(packet))

    assert body["session_contract"] == {
        "next_action": "Add the context budget fields first",
        "definition_of_done": "Run make check and leave the workspace in a clean state.",
        "verification_command": "make check",
        "clean_state_required": True,
        "sync_warning_ab": 0.5,
        "switch_recommended_ab": 0.7,
    }
    assert body["context_budget"]["reference_count"] == len(body["context_references"])
    assert body["context_budget"]["withheld_context_count"] == 1
    assert body["context_budget"]["estimated_tokens"] > 0
    assert body["context_budget"]["sync_warning_ab"] == 0.5
    assert body["context_budget"]["switch_recommended_ab"] == 0.7
    assert {reference["kind"] for reference in body["context_references"]} >= {
        "intent",
        "artifact",
        "blocker",
    }
    assert all(reference["include_reason"] for reference in body["context_references"])
    assert all(
        reference["load_hint"] != "inline_raw_payload" for reference in body["context_references"]
    )
    assert "PRIVATE_NOTE_PAYLOAD" not in json.dumps(body)


def test_all_feedback_categories_surface_safe_packet_quality_notes(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={"current_goal": "Check all feedback categories"},
        )
    )
    for kind in ContextFeedbackKind:
        service.record_feedback(
            brief_id="brief-123",
            kind=kind,
            note=f"SECRET raw note for {kind.value}",
        )

    packet = service.create_continuity_packet(AgentContextSurface(kind="coding-agent"))
    dumped = packet.model_dump_json()

    assert packet.confidence < 0.9
    assert all(
        any(f"{kind.value} feedback" in note for note in packet.context_quality_notes)
        for kind in ContextFeedbackKind
    )
    assert "SECRET raw note" not in dumped


def test_sensitive_context_feedback_note_is_withheld(tmp_path) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)

    feedback = service.record_feedback(
        brief_id="brief-123",
        kind=ContextFeedbackKind.TOO_SENSITIVE,
        note="This note contains private incident details.",
    )

    assert feedback.note is None
    assert feedback.note_withheld is True
    assert feedback.withheld_context[0].category == "sensitivity"
    assert "sensitive" in feedback.policy_reason
    assert service.get_context_quality().feedback[0].note is None


def test_long_context_feedback_note_is_withheld_by_policy(tmp_path) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)

    feedback = service.record_feedback(
        brief_id="brief-123",
        kind=ContextFeedbackKind.WRONG,
        note="x" * 600,
    )

    assert feedback.note is None
    assert feedback.note_withheld is True
    assert feedback.withheld_context[0].category == "payload_content"
    assert "full-text" in feedback.policy_reason


def test_work_state_models_capture_intent_artifacts_loops_attempts_and_blockers() -> None:
    timestamp = datetime(2026, 5, 4, 12, 0, tzinfo=UTC)
    evidence = EvidenceItem(
        source="task",
        event_type="goal_update",
        summary="goal_update",
        timestamp=timestamp,
        policy_reason="observation is allowed by the default local policy",
    )
    intent = IntentLine(
        summary="Implement ambient context kernel",
        evidence=[evidence],
        updated_at=timestamp,
        confidence=0.9,
        status=IntentStatus.ACTIVE,
    )
    artifact = RelevantArtifact(
        kind="file",
        identifier="packages/devcd-core/src/devcd/slices/ambient_context/service.py",
        summary="file_focus: packages/devcd-core/src/devcd/slices/ambient_context/service.py",
        source="ide",
        relevance=0.8,
        last_seen_at=timestamp,
        policy_reason="observation is allowed by the default local policy",
    )
    open_loop = OpenLoop(
        id="failure:test failure needs investigation",
        summary="test failure needs investigation",
        kind=OpenLoopKind.FAILURE,
        evidence=[evidence],
        status=OpenLoopStatus.OPEN,
        confidence=0.8,
        created_at=timestamp,
        updated_at=timestamp,
    )
    attempt = RecentAttempt(
        timestamp=timestamp,
        source="task",
        type="test_failure",
        summary="test_failure",
        outcome="failure",
        policy_reason="observation is allowed by the default local policy",
    )
    blocker = BlockerSignal(
        summary="test failure needs investigation",
        evidence=[evidence],
        confidence=0.8,
        detected_at=timestamp,
    )

    work_state = WorkState(
        active_intent=intent,
        candidate_intents=[intent],
        relevant_artifacts=[artifact],
        open_loops=[open_loop],
        recent_attempts=[attempt],
        blockers=[blocker],
        freshness=FreshnessState(status=FreshnessStatus.CURRENT, last_seen_at=timestamp),
        confidence=0.9,
        policy_summary=PolicySummary(
            allowed=True,
            operation="export",
            reason="local context export is allowed by policy",
            included_sources=["task", "ide"],
            withheld_sources=[],
            included_data_classes=["metadata"],
            withheld_data_classes=[],
        ),
        generated_at=timestamp,
    )

    assert work_state.active_intent is not None
    assert work_state.active_intent.status is IntentStatus.ACTIVE
    assert work_state.relevant_artifacts[0].kind == "file"
    assert work_state.open_loops[0].kind is OpenLoopKind.FAILURE
    assert work_state.recent_attempts[0].outcome == "failure"
    assert work_state.blockers[0].confidence == 0.8


def test_work_state_derives_current_goal_artifact_attempt_and_open_loop(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Implement ambient context kernel"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.IDE,
            type="file_focus",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={
                "path": "packages/devcd-core/src/devcd/slices/ambient_context/service.py",
                "duration_seconds": 90,
            },
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 2, tzinfo=UTC),
            payload={"reason": "context brief omits open loop evidence"},
        )
    )

    work_state = service.get_work_state()

    assert work_state.active_intent is not None
    assert work_state.active_intent.summary == "Implement ambient context kernel"
    assert work_state.relevant_artifacts[0].identifier.endswith("ambient_context/service.py")
    assert work_state.recent_attempts[0].outcome == "failure"
    assert work_state.open_loops[0].summary == "context brief omits open loop evidence"
    assert work_state.blockers[0].summary == "context brief omits open loop evidence"
    assert work_state.policy_summary.included_sources == ["ide", "task"]


def test_work_state_derives_relevant_artifact_from_artifact_ref(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.IDE,
            type="artifact_ref",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={
                "path": "packages/devcd-core/src/devcd/cli.py",
                "summary": "CLI entrypoint",
            },
        )
    )

    packet = service.create_continuity_packet(AgentContextSurface(kind="coding-agent"))

    assert packet.artifacts[0].identifier == "packages/devcd-core/src/devcd/cli.py"
    assert packet.artifacts[0].summary == "artifact_ref: CLI entrypoint"


def test_work_state_derives_blocker_from_blocker_event(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="blocker",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={"summary": "Agent has no shell access"},
        )
    )

    packet = service.create_continuity_packet(AgentContextSurface(kind="coding-agent"))

    assert packet.blockers[0].summary == "Agent has no shell access"


def test_work_state_marks_old_goal_stale_after_branch_change(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Old task"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 4, 13, 0, tzinfo=UTC),
            payload={"branch": "002-ambient-context-kernel"},
        )
    )

    work_state = service.get_work_state()

    assert work_state.active_intent is not None
    assert work_state.active_intent.summary == "002-ambient-context-kernel"
    assert any(intent.status is IntentStatus.STALE for intent in work_state.candidate_intents)


def test_work_state_excludes_policy_denied_sources(tmp_path) -> None:
    policy_engine = PolicyEngine(
        allow_observation=True,
        allow_local_storage=True,
        allow_remote_export=False,
        allow_actions=False,
        enabled_sources={"git"},
        allowed_data_classes={"metadata"},
    )
    memory_store = MemoryStore.with_default_ttl()
    event_ledger = EventLedger(tmp_path / "events.jsonl")
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)
    service = AmbientContextService(state_engine, memory_store, policy_engine)

    denied = state_engine.accept_event(
        DevEvent(
            source=EventSource.IDE,
            type="file_focus",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"path": "secret.py"},
        )
    )

    work_state = service.get_work_state()

    assert not denied.allowed
    assert work_state.relevant_artifacts == []
    assert work_state.policy_summary.withheld_sources == ["ide"]


def test_context_brief_model_contains_surface_summary_and_policy_decision() -> None:
    timestamp = datetime(2026, 5, 4, 12, 0, tzinfo=UTC)
    brief = ContextBrief(
        surface=AgentContextSurface(kind="cli", name="copilot"),
        summary="Working on Implement ambient context kernel.",
        active_intent=None,
        relevant_artifacts=[],
        open_loops=[],
        recent_attempts=[],
        suggested_next_steps=[],
        withheld=[],
        policy_decision=PolicySummary(
            allowed=True,
            operation="export",
            reason="local context export is allowed by policy",
            included_sources=[],
            withheld_sources=[],
            included_data_classes=["metadata"],
            withheld_data_classes=[],
        ),
        generated_at=timestamp,
    )

    assert brief.surface.kind == "cli"
    assert brief.policy_decision.allowed is True


def test_context_brief_includes_current_work_state(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Implement ambient context kernel"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))

    assert brief.active_intent is not None
    assert brief.active_intent.summary == "Implement ambient context kernel"
    assert "Implement ambient context kernel" in brief.summary
    assert brief.policy_decision.allowed is True


def test_context_brief_records_withheld_data_class_reason(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Implement ambient context kernel"},
        )
    )

    brief = service.create_context_brief(
        AgentContextSurface(kind="cli", requested_data_classes=["secret"])
    )

    assert brief.policy_decision.allowed is False
    assert brief.policy_decision.withheld_data_classes == ["secret"]
    assert brief.withheld[0].kind == "data_class"


def test_context_brief_avoids_invented_intent_when_confidence_is_low(tmp_path) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)

    brief = service.create_context_brief(AgentContextSurface(kind="cli"))

    assert brief.active_intent is None
    assert "No active intent" in brief.summary
    assert brief.relevant_artifacts == []


def test_context_brief_contains_agent_handoff_fields_and_policy_boundaries(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Ship the Agent-Handoff MVP"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.IDE,
            type="file_focus",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={
                "path": "packages/devcd-core/src/devcd/slices/ambient_context/service.py",
                "duration_seconds": 120,
            },
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 4, 12, 2, tzinfo=UTC),
            payload={"repo": ".", "branch": "main"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="commit",
            timestamp=datetime(2026, 5, 4, 12, 3, tzinfo=UTC),
            payload={"repo": ".", "sha": "abc1234", "message": "fix failing state test"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 4, tzinfo=UTC),
            payload={"reason": "make check failed on ContextBrief.git_context"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.BROWSER,
            type="url_focus",
            timestamp=datetime(2026, 5, 4, 12, 5, tzinfo=UTC),
            payload={"url": "https://internal.invalid/private-ticket"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))

    assert brief.active_goal == "Ship the Agent-Handoff MVP"
    assert brief.git_context.branch == "main"
    assert brief.git_context.latest_commit == "abc1234"
    assert brief.git_context.latest_commit_summary == "fix failing state test"
    assert brief.relevant_artifacts[0].identifier.endswith("ambient_context/service.py")
    assert brief.recent_attempts[0].outcome == "failure"
    assert brief.blockers[0].summary == "make check failed on ContextBrief.git_context"
    assert brief.suggested_next_steps[0].summary.startswith("Investigate")
    assert brief.policy_decision.allowed is True
    assert brief.withheld_context[0].category == "source"
    assert brief.withheld_context[0].policy_reason == "source is not enabled by policy"
    assert "browser url_focus signal was withheld" in brief.withheld_context[0].safe_summary
    assert "safe replacement" in brief.withheld_context[0].safe_summary
    assert any("browser url_focus signal was withheld" in item for item in brief.agent_limitations)
    assert any("cannot see" in item for item in brief.agent_limitations)


def test_context_brief_prefers_live_git_context_over_stale_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"repo": str(tmp_path), "branch": "feature/devcd-core"},
        )
    )

    def fake_collect_snapshot_events(self: GitEventSource, repo_path: Path) -> list[DevEvent]:
        assert repo_path == tmp_path
        return [
            DevEvent(
                source=EventSource.GIT,
                type="branch_change",
                payload={"repo": str(repo_path), "branch": "main"},
            ),
            DevEvent(
                source=EventSource.GIT,
                type="commit",
                payload={
                    "repo": str(repo_path),
                    "sha": "abc1234",
                    "message": "live git snapshot",
                },
            ),
        ]

    monkeypatch.setattr(GitEventSource, "collect_snapshot_events", fake_collect_snapshot_events)
    service = AmbientContextService(
        state_engine,
        service.memory_store,
        service.policy_engine,
        feedback_path=tmp_path / "context-feedback.jsonl",
        repo_path=tmp_path,
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))

    assert brief.git_context.branch == "main"
    assert brief.git_context.latest_commit == "abc1234"
    assert brief.git_context.latest_commit_summary == "live git snapshot"


def test_context_brief_derives_agent_resurrection_context(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Restore the agent handoff after context loss"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.IDE,
            type="file_focus",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={"path": "packages/devcd-core/src/devcd/slices/ambient_context/service.py"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 2, tzinfo=UTC),
            payload={"reason": "make check failed: missing resurrection sections"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="fix_attempt",
            timestamp=datetime(2026, 5, 4, 12, 3, tzinfo=UTC),
            payload={"summary": "Added only a Last failure section to the markdown renderer"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 4, tzinfo=UTC),
            payload={
                "reason": "make check still fails: do_not_repeat is absent",
                "suggested_next_action": "Add a first-class resurrection context before rendering",
            },
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.NOTES,
            type="note_update",
            timestamp=datetime(2026, 5, 4, 12, 5, tzinfo=UTC),
            payload={"title": "SECRET_TOKEN=do-not-print"},
            sensitivity="sensitive",
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))
    markdown = render_context_brief_markdown(brief)

    assert brief.resurrection.current_goal == "Restore the agent handoff after context loss"
    assert brief.resurrection.last_attempt is not None
    assert brief.resurrection.last_attempt.type == "test_failure"
    assert brief.resurrection.last_failure == "make check still fails: do_not_repeat is absent"
    assert (
        brief.resurrection.last_attempted_fix
        == "Added only a Last failure section to the markdown renderer"
    )
    assert "happened after the attempted fix" in brief.resurrection.why_attempt_failed
    assert [item.path for item in brief.resurrection.do_not_repeat] == [
        "Do not repeat the last attempted fix unchanged: Added only a Last failure section "
        "to the markdown renderer"
    ]
    assert brief.resurrection.do_not_repeat[0].rationale is not None
    assert (
        brief.resurrection.suggested_next_action
        == "Add a first-class resurrection context before rendering"
    )
    assert (
        "Original chat history is not available in the handoff packet."
        in brief.resurrection.unknowns
    )
    assert "## do_not_repeat" in markdown
    assert "## unknowns" in markdown
    assert "SECRET_TOKEN" not in markdown


def test_resurrection_context_keeps_failure_history_after_later_success(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Finish the continuity handoff"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="fix_attempt",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={"summary": "Only renamed the renderer heading"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 2, tzinfo=UTC),
            payload={"reason": "handoff JSON still omits why_attempt_failed"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="fix_success",
            timestamp=datetime(2026, 5, 4, 12, 3, tzinfo=UTC),
            payload={"summary": "Added why_attempt_failed to the JSON contract"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))

    assert brief.resurrection.last_attempt is not None
    assert brief.resurrection.last_attempt.outcome == "success"
    assert (
        brief.resurrection.last_attempt.summary == "Added why_attempt_failed to the JSON contract"
    )
    assert brief.resurrection.last_failure == "handoff JSON still omits why_attempt_failed"
    assert [item.path for item in brief.resurrection.do_not_repeat] == [
        "Do not repeat the last attempted fix unchanged: Only renamed the renderer heading"
    ]
    assert "appears resolved by" in brief.resurrection.why_attempt_failed
    assert "Added why_attempt_failed to the JSON contract" in brief.resurrection.why_attempt_failed
    assert (
        brief.resurrection.suggested_next_action
        == "Continue from the successful attempt: Added why_attempt_failed to the JSON contract"
    )


def test_context_brief_ignores_low_signal_setup_goal_updates(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Ship a robust continuity packet"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={"current_goal": "Prepare workspace continuity"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))

    assert brief.active_goal == "Ship a robust continuity packet"


def test_resurrection_context_generates_do_not_repeat_for_failed_attempt(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="fix_failure",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={
                "summary": "Retried the stale renderer-only patch",
                "why_attempt_failed": "The patch only changed markdown and skipped JSON output.",
                "suggested_next_action": "Update the continuity contract and renderer together",
            },
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))

    assert brief.resurrection.last_attempt is not None
    assert brief.resurrection.last_attempt.outcome == "failure"
    assert brief.resurrection.last_failure == "Retried the stale renderer-only patch"
    assert [item.path for item in brief.resurrection.do_not_repeat] == [
        "Do not repeat the failed attempt unchanged: Retried the stale renderer-only patch"
    ]
    assert (
        brief.resurrection.why_attempt_failed
        == "The patch only changed markdown and skipped JSON output."
    )
    assert (
        brief.resurrection.suggested_next_action
        == "Update the continuity contract and renderer together"
    )


def test_resurrection_context_uses_latest_relevant_failure(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"reason": "older failure should remain history"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={
                "reason": "latest failure should drive continuity",
                "suggested_next_action": "Rerun the latest targeted test",
            },
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))

    assert brief.resurrection.last_failure == "latest failure should drive continuity"
    assert brief.resurrection.suggested_next_action == "Rerun the latest targeted test"
    assert "older failure" not in (brief.resurrection.why_attempt_failed or "")


def test_context_brief_explains_sensitive_withheld_signal_without_payload(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.NOTES,
            type="note_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"title": "Private credentials note"},
            sensitivity="sensitive",
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))

    assert brief.withheld_context[0].category == "sensitivity"
    assert "sensitive events" in brief.withheld_context[0].policy_reason
    assert "Private credentials" not in brief.withheld_context[0].safe_summary
    assert "notes note_update signal was withheld" in brief.withheld_context[0].safe_summary
    assert any("notes note_update signal was withheld" in item for item in brief.agent_limitations)
    assert all("Private credentials" not in item for item in brief.agent_limitations)


def test_coding_agent_surface_sees_allowed_context_with_policy_reasoning(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Implement context surfaces"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.IDE,
            type="file_focus",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={"path": "packages/devcd-core/src/devcd/slices/ambient_context/service.py"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 4, 12, 2, tzinfo=UTC),
            payload={"branch": "main"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="coding-agent"))

    assert brief.surface.kind == "coding-agent"
    assert brief.surface.allowed_state_areas == [
        "summary",
        "active_goal",
        "active_intent",
        "relevant_artifacts",
        "git_context",
        "open_loops",
        "recent_attempts",
        "blockers",
        "suggested_next_steps",
    ]
    assert brief.surface.allowed_memory_scopes == ["working", "episodic"]
    assert brief.active_goal == "Implement context surfaces"
    assert brief.relevant_artifacts[0].identifier.endswith("ambient_context/service.py")
    assert brief.git_context.branch == "main"
    assert brief.policy_decision.allowed is True
    assert "coding-agent" in brief.policy_decision.reason


def test_public_demo_surface_withholds_sensitive_details_and_explains_policy(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    private_goal = "Fix private customer incident ACME-123"
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": private_goal},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={"branch": "private/customer-acme-123"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 2, tzinfo=UTC),
            payload={"reason": "private customer regression"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.IDE,
            type="file_focus",
            timestamp=datetime(2026, 5, 4, 12, 3, tzinfo=UTC),
            payload={"path": "customers/acme/private_fix.py"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="public-demo"))
    dumped = brief.model_dump_json()

    assert brief.active_goal is None
    assert brief.active_intent is None
    assert brief.git_context.branch is None
    assert brief.relevant_artifacts == []
    assert brief.recent_attempts == []
    assert private_goal not in dumped
    assert "private/customer-acme-123" not in dumped
    assert "private customer regression" not in dumped
    assert "customers/acme/private_fix.py" not in dumped
    assert brief.policy_decision.allowed is True
    assert "public-demo" in brief.policy_decision.reason
    assert any(item.kind == "sensitive_field" for item in brief.withheld_context)
    assert any("public-demo" in item.policy_reason for item in brief.withheld_context)


@pytest.mark.parametrize(
    ("surface_kind", "detail_level"),
    [
        ("coding-agent", "standard"),
        ("review-agent", "standard"),
        ("debugging-agent", "diagnostic"),
        ("subagent", "minimal"),
        ("public-demo", "minimal"),
    ],
)
def test_product_context_surfaces_resolve_to_testable_definitions(
    tmp_path,
    surface_kind: str,
    detail_level: str,
) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)

    brief = service.create_context_brief(AgentContextSurface(kind=surface_kind))

    assert brief.surface.kind == surface_kind
    assert brief.surface.detail_level == detail_level
    assert brief.surface.allowed_state_areas
    assert "surface" in brief.policy_decision.reason


def test_context_pack_registry_contains_developer_and_research_packs() -> None:
    packs = list_context_packs()

    assert [pack.id for pack in packs] == ["developer", "research"]
    assert all(not pack.remote_export_enabled_by_default for pack in packs)

    developer = get_context_pack("developer")
    research = get_context_pack("research")

    assert developer.display_name == "Developer Context"
    assert {event.source for event in developer.supported_events} >= {
        "ide",
        "git",
        "task",
        "notes",
    }
    assert "coding-agent" in developer.supported_surfaces
    assert developer.renderer_metadata["continuity_packet"]["legacy_handoff_contract"] is True

    research_event_types = {
        event_type
        for supported_event in research.supported_events
        for event_type in supported_event.event_types
    }
    assert research.display_name == "Research Context"
    assert {"source_review", "hypothesis", "decision", "failed_attempt"}.issubset(
        research_event_types
    )
    assert "research-agent" in research.supported_surfaces
    assert research.renderer_metadata["continuity_packet"]["default_context_pack"] == "research"


def test_context_pack_registry_json_is_stable_and_policy_safe() -> None:
    first = render_context_packs_json()
    second = render_context_packs_json()

    assert first == second
    body = json.loads(first)
    assert [pack["id"] for pack in body] == ["developer", "research"]
    assert all(pack["remote_export_enabled_by_default"] is False for pack in body)
    assert body[0]["supported_events"] == sorted(
        body[0]["supported_events"], key=lambda event: event["source"]
    )


def test_subagent_surface_gets_focused_context_without_unnecessary_breadth(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Implement context surfaces"},
        )
    )
    for index in range(5):
        state_engine.accept_event(
            DevEvent(
                source=EventSource.IDE,
                type="file_focus",
                timestamp=datetime(2026, 5, 4, 12, index + 1, tzinfo=UTC),
                payload={"path": f"packages/devcd-core/src/devcd/slices/file_{index}.py"},
            )
        )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 4, 12, 6, tzinfo=UTC),
            payload={"branch": "wide-context-branch"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 7, tzinfo=UTC),
            payload={"reason": "focused blocker"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="subagent"))

    assert brief.surface.detail_level == "minimal"
    assert brief.surface.allowed_memory_scopes == ["working"]
    assert brief.active_goal == "wide-context-branch"
    assert len(brief.relevant_artifacts) == 3
    assert brief.git_context.branch is None
    assert brief.recent_attempts == []
    assert brief.open_loops == []
    assert brief.blockers[0].summary == "focused blocker"
    assert any(item.kind == "state_area" for item in brief.withheld_context)


def test_proactive_suggestion_model_captures_rationale_and_cooldown() -> None:
    timestamp = datetime(2026, 5, 4, 12, 0, tzinfo=UTC)
    evidence = EvidenceItem(
        source="task",
        event_type="test_failure",
        summary="test_failure",
        timestamp=timestamp,
        policy_reason="observation is allowed by the default local policy",
    )

    suggestion = ProactiveSuggestion(
        id="blocker:test-failure",
        summary="Investigate failing tests",
        rationale="Repeated failure evidence suggests the current blocker is test related.",
        confidence=0.8,
        evidence=[evidence],
        status=ProactiveSuggestionStatus.ACTIVE,
        created_at=timestamp,
    )

    assert suggestion.status is ProactiveSuggestionStatus.ACTIVE
    assert suggestion.confidence == 0.8
    assert suggestion.suppressed_until is None


def test_repeated_failure_generates_limited_proactive_suggestion(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    for index in range(4):
        state_engine.accept_event(
            DevEvent(
                source=EventSource.TASK,
                type="test_failure",
                timestamp=datetime(2026, 5, 4, 12, index, tzinfo=UTC),
                payload={"reason": "context brief omits open loop evidence"},
            )
        )

    work_state = service.get_work_state()

    assert 1 <= len(work_state.suggestions) <= 3
    assert work_state.suggestions[0].summary.startswith("Investigate")
    assert "current blocker" in work_state.suggestions[0].rationale
    assert work_state.suggestions[0].confidence >= 0.7


def test_pytest_failure_recipe_feeds_policy_gated_handoff_packet(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    report = PytestFailureRecipeInput(
        command="pytest tests/test_checkout.py -q",
        exit_code=1,
        timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
        failures=[
            PytestFailure(
                nodeid="tests/test_checkout.py::test_total",
                file_path="tests/test_checkout.py",
                line=42,
            )
        ],
        stderr="E   AssertionError: SECRET_TOKEN=abc123",
    )
    for event in events_from_pytest_failure(report):
        state_engine.accept_event(event)

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))
    markdown = render_context_brief_markdown(brief)
    dumped = brief.model_dump_json()

    assert "## Last failure" in markdown
    assert "## brief_id" in markdown
    assert brief.id in markdown
    assert brief.resurrection.last_attempt is not None
    assert brief.resurrection.last_attempt.type == "test_failure"
    assert brief.resurrection.last_attempt.outcome == "failure"
    assert "pytest failed: tests/test_checkout.py::test_total" in markdown
    assert "## why_attempt_failed" in markdown
    assert "## Suggested next action" in markdown
    assert "Rerun pytest tests/test_checkout.py::test_total -q" in markdown
    assert brief.blockers[0].summary == "pytest failed: tests/test_checkout.py::test_total"
    assert brief.suggested_next_steps[0].summary.startswith("Rerun pytest")
    assert brief.withheld_context[0].category == "sensitivity"
    assert "sensitive events" in brief.withheld_context[0].policy_reason
    assert "task test_output signal was withheld" in brief.withheld_context[0].safe_summary
    assert "SECRET_TOKEN" not in markdown
    assert "SECRET_TOKEN" not in dumped


def test_low_confidence_state_has_no_proactive_suggestions(tmp_path) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)

    work_state = service.get_work_state()

    assert work_state.suggestions == []


def test_dismissed_suggestion_is_suppressed_until_cooldown_expires(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"reason": "context brief omits open loop evidence"},
        )
    )
    suggestion = service.get_work_state().suggestions[0]

    dismissed = service.dismiss_suggestion(suggestion.id)
    work_state = service.get_work_state()

    assert dismissed.status is ProactiveSuggestionStatus.DISMISSED
    assert dismissed.suppressed_until is not None
    assert work_state.suggestions == []


def test_context_memory_item_model_captures_freshness_confidence_and_policy() -> None:
    timestamp = datetime(2026, 5, 4, 12, 0, tzinfo=UTC)

    item = ContextMemoryItem(
        id="memory-1",
        scope="working",
        summary="goal_update: Implement ambient context kernel",
        source="task",
        freshness=FreshnessState(status=FreshnessStatus.CURRENT, last_seen_at=timestamp),
        confidence=0.8,
        policy_reason="observation is allowed by the default local policy",
        created_at=timestamp,
        updated_at=timestamp,
        expires_at=timestamp,
    )

    assert item.scope == "working"
    assert item.freshness.status is FreshnessStatus.CURRENT
    assert item.confidence == 0.8


def test_context_memory_inspection_exposes_visible_scope_metadata(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Implement ambient context kernel"},
        )
    )

    items = service.list_context_memory(scope="working")

    assert len(items) == 1
    assert items[0].scope == "working"
    assert items[0].summary == "goal_update: Implement ambient context kernel"
    assert items[0].freshness.status is FreshnessStatus.CURRENT
    assert items[0].confidence >= 0.7
    assert "policy" in items[0].policy_reason


def test_context_memory_correction_updates_later_work_state(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Old goal"},
        )
    )
    item = service.list_context_memory(scope="working")[0]

    corrected = service.correct_context_memory_item(
        item.id,
        MemoryCorrection(summary="Corrected goal", reason="developer corrected retained context"),
    )
    work_state = service.get_work_state()

    assert corrected.summary == "goal_update: Corrected goal"
    assert "developer corrected" in corrected.policy_reason
    assert work_state.active_intent is not None
    assert work_state.active_intent.summary == "Corrected goal"


def test_context_memory_deletion_excludes_item_from_later_work_state(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Delete stale context"},
        )
    )
    item = service.list_context_memory(scope="working")[0]

    service.delete_context_memory_item(item.id)
    work_state = service.get_work_state()

    assert service.list_context_memory(scope="working") == []
    assert work_state.active_intent is None


def build_ambient_context_service(tmp_path) -> tuple[AmbientContextService, StateEngine]:
    policy_engine = PolicyEngine.default()
    memory_store = MemoryStore.with_ttl_seconds(315360000)
    event_ledger = EventLedger(tmp_path / "events.jsonl")
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)
    service = AmbientContextService(
        state_engine,
        memory_store,
        policy_engine,
        feedback_path=tmp_path / "context-feedback.jsonl",
    )
    return service, state_engine


# ---------------------------------------------------------------------------
# JSON contract tests
# ---------------------------------------------------------------------------


def test_context_brief_json_contract_contains_all_required_fields(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Ship Agent-Handoff JSON Contract"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={"repo": ".", "branch": "feat/json-contract"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 2, tzinfo=UTC),
            payload={"reason": "render_context_brief_json not yet implemented"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="test"))
    contract = json.loads(render_context_brief_json(brief))

    required_fields = {
        "schema_version",
        "brief_id",
        "surface",
        "goal",
        "relevant_artifacts",
        "git_context",
        "last_attempt",
        "last_failure",
        "why_attempt_failed",
        "do_not_repeat",
        "blockers",
        "suggested_next_action",
        "policy_summary",
        "withheld_context_summary",
        "unknowns",
        "confidence",
    }
    assert required_fields.issubset(contract.keys())
    assert contract["schema_version"] == "1"
    assert contract["surface"] == "cli"
    assert contract["goal"] == "Ship Agent-Handoff JSON Contract"
    assert contract["git_context"]["branch"] == "feat/json-contract"
    assert contract["last_failure"] == "render_context_brief_json not yet implemented"
    assert contract["why_attempt_failed"] == (
        "The latest visible blocker is still unresolved: render_context_brief_json not yet "
        "implemented"
    )
    assert isinstance(contract["blockers"], list)
    assert isinstance(contract["relevant_artifacts"], list)
    assert isinstance(contract["do_not_repeat"], list)
    assert isinstance(contract["unknowns"], list)
    assert isinstance(contract["policy_summary"], dict)
    assert isinstance(contract["withheld_context_summary"], list)
    assert isinstance(contract["confidence"], float)


def test_context_brief_json_contract_contains_no_secret_payloads(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.NOTES,
            type="note_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"title": "API_KEY=super-secret-value-12345"},
            sensitivity="sensitive",
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.BROWSER,
            type="url_focus",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={"url": "https://internal.corp/secret-board"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="test"))
    json_output = render_context_brief_json(brief)

    assert "super-secret-value-12345" not in json_output
    assert "API_KEY=super-secret-value-12345" not in json_output
    assert "secret-board" not in json_output


def test_context_brief_json_and_markdown_are_consistent(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)

    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Consistency check between JSON and Markdown"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="commit",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={"repo": ".", "sha": "deadbeef", "message": "add json contract"},
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="test"))
    contract = json.loads(render_context_brief_json(brief))
    markdown = render_context_brief_markdown(brief)

    assert contract["goal"] == brief.active_goal
    assert contract["goal"] in markdown
    assert contract["schema_version"] == brief.schema_version
    assert contract["brief_id"] == brief.id
    assert brief.id in markdown
    assert contract["git_context"]["latest_commit"] == brief.git_context.latest_commit
    assert (contract["git_context"]["latest_commit"] or "unknown") in markdown


def test_context_brief_json_policy_summary_omits_included_sources(tmp_path) -> None:
    service, _state_engine = build_ambient_context_service(tmp_path)

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="test"))
    contract = json.loads(render_context_brief_json(brief))

    ps = contract["policy_summary"]
    assert "allowed" in ps
    assert "operation" in ps
    assert "reason" in ps
    assert "withheld_sources" in ps
    assert "withheld_data_classes" in ps
    # The full included_sources list is intentionally not in the contract
    assert "included_sources" not in ps


def test_context_brief_has_schema_version_and_confidence_fields() -> None:
    policy = PolicySummary(
        allowed=True,
        operation="export",
        reason="test",
    )
    brief = ContextBrief(
        surface=AgentContextSurface(),
        summary="test brief",
        policy_decision=policy,
    )

    assert brief.schema_version == "1"
    assert brief.confidence == 0.0


def test_agent_resurrection_fixture_maps_to_neutral_continuity_packet(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    events_path = Path("examples/agent-resurrection/sample-events.jsonl")
    schema_path = Path("schemas/devcd-continuity-packet.schema.json")

    for line in events_path.read_text(encoding="utf-8").splitlines():
        state_engine.accept_event(DevEvent.model_validate_json(line))

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))
    packet = continuity_packet_from_context_brief(brief)
    contract = packet.model_dump(mode="json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert packet.context_pack == "developer"
    assert packet.intent is not None
    assert packet.intent.summary == "Continue the resurrection demo after Agent A lost chat context"
    assert packet.artifacts[0].identifier == "tests/test_ambient_context.py"
    assert packet.attempts[0].summary == "make check still fails: do_not_repeat is absent"
    assert packet.attempts[0].outcome == "failure"
    assert packet.blockers[0].summary == "make check still fails: do_not_repeat is absent"
    assert packet.blockers[0].reason is not None
    assert "happened after the attempted fix" in packet.blockers[0].reason
    assert [item.path for item in packet.do_not_repeat] == [
        "Do not repeat the last attempted fix unchanged: Added only a Last failure section "
        "to the markdown renderer"
    ]
    assert packet.suggested_next_steps == [
        "Add a first-class resurrection context before rendering"
    ]
    assert packet.pack_metadata["git_context"]["branch"] == "main"
    assert {item.category for item in packet.withheld_context} >= {
        "sensitivity",
        "source",
        "payload_content",
    }
    assert set(schema["required"]).issubset(contract.keys())


def test_neutral_continuity_packet_can_render_existing_handoff_contract(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Ship neutral continuity packet"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 4, 12, 1, tzinfo=UTC),
            payload={
                "reason": "legacy handoff contract drifted",
                "suggested_next_action": "Render legacy packet from neutral continuity",
            },
        )
    )

    brief = service.create_context_brief(AgentContextSurface(kind="cli", name="copilot"))
    packet = continuity_packet_from_context_brief(brief)

    assert json.loads(render_agent_handoff_packet_json(packet)) == json.loads(
        render_context_brief_json(brief)
    )


def test_research_continuity_preserves_distinct_same_timestamp_attempts(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    timestamp = datetime(2026, 5, 5, 10, 0, tzinfo=UTC)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="research_goal",
            timestamp=timestamp,
            payload={"current_goal": "Compare retrieval latency studies"},
        )
    )
    for summary in (
        "Compared latency without matching dataset size",
        "Compared latency without matching source count",
    ):
        state_engine.accept_event(
            DevEvent(
                source=EventSource.NOTES,
                type="failed_attempt",
                timestamp=timestamp,
                payload={"summary": summary},
            )
        )

    brief = service.create_context_brief(AgentContextSurface(kind="research-agent", name="demo"))
    packet = service.create_continuity_packet_from_brief(brief, context_pack="research")

    summaries = [attempt.summary for attempt in packet.attempts]
    assert "Compared latency without matching dataset size" in summaries
    assert "Compared latency without matching source count" in summaries


def test_research_like_continuity_packet_is_not_developer_specific() -> None:
    timestamp = datetime(2026, 5, 5, 9, 30, tzinfo=UTC)
    policy = PolicySummary(
        allowed=True,
        operation="export",
        reason="local research continuity export is allowed by policy",
        included_sources=["notes", "library"],
        included_data_classes=["metadata"],
    )

    packet = ContinuityPacket(
        id="research-packet-1",
        context_pack="research",
        surface="research-agent",
        intent=ContinuityIntent(
            summary="Evaluate whether retrieval latency changes answer quality",
            status="active",
            updated_at=timestamp,
            confidence=0.72,
        ),
        artifacts=[
            ContinuityArtifact(
                kind="source",
                identifier="doi:10.0000/example-a",
                summary="Prior study on retrieval latency",
                source="library",
                relevance=0.9,
                last_seen_at=timestamp,
                policy_reason="source metadata is allowed by policy",
            ),
            ContinuityArtifact(
                kind="note",
                identifier="notes/retrieval-latency-hypothesis.md",
                summary="Hypothesis: lower latency may improve iterative answer quality",
                source="notes",
                relevance=0.85,
                last_seen_at=timestamp,
                policy_reason="note title metadata is allowed by policy",
            ),
        ],
        decisions=[
            ContinuityDecision(
                kind="hypothesis",
                summary="Treat latency as a possible quality confound until tested",
                source="notes",
                decided_at=timestamp,
                policy_reason="decision summary is allowed by policy",
            )
        ],
        attempts=[
            ContinuityAttempt(
                timestamp=timestamp,
                source="notes",
                type="hypothesis_check",
                summary="Compared two papers without normalizing dataset size",
                outcome="failure",
                failure_reason="The attempt mixed latency effects with dataset-size effects.",
                policy_reason="attempt summary is allowed by policy",
            )
        ],
        blockers=[
            ContinuityBlocker(
                kind="missing_source",
                summary="Need a matched dataset-size source before concluding",
                confidence=0.8,
                detected_at=timestamp,
                reason="Current sources do not isolate the hypothesis.",
                policy_reason="blocker summary is allowed by policy",
            )
        ],
        preferences=[
            ContinuityPreference(
                summary="Prefer citations from local source notes before web search",
                source="notes",
                policy_reason="preference summary is allowed by policy",
            )
        ],
        do_not_repeat=["Do not compare latency studies without normalizing dataset size."],
        suggested_next_steps=["Find one source with matched dataset size and latency variation."],
        policy_decision=policy,
        generated_at=timestamp,
    )

    dumped = packet.model_dump(mode="json")

    assert dumped["context_pack"] == "research"
    assert dumped["surface"] == "research-agent"
    assert dumped["artifacts"][0]["kind"] == "source"
    assert dumped["decisions"][0]["kind"] == "hypothesis"
    assert dumped["attempts"][0]["outcome"] == "failure"
    assert dumped["blockers"][0]["kind"] == "missing_source"
    assert dumped["do_not_repeat"] == [
        {
            "path": "Do not compare latency studies without normalizing dataset size.",
            "rationale": None,
        }
    ]
    assert "git_context" not in dumped["pack_metadata"]


def test_research_session_recipe_feeds_policy_filtered_research_packet(tmp_path) -> None:
    service, state_engine = build_ambient_context_service(tmp_path)
    report = ResearchSessionRecipeInput(
        goal="Assess whether retrieval latency changes answer quality",
        timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
        reviewed_sources=[
            ResearchSource(
                title="Latency and answer quality",
                reference="doi:10.0000/example-a",
                source_type="paper",
                summary="Metadata-only source summary",
                full_text="PRIVATE_ARTICLE_TEXT",
            )
        ],
        notes=[
            ResearchNoteMetadata(
                title="Latency note",
                summary="Note metadata summary",
                raw_text="PRIVATE_NOTE_TEXT",
            )
        ],
        hypotheses=["Lower latency may improve iterative answer quality"],
        decisions=["Treat dataset size as a confound"],
        failed_attempts=[
            ResearchFailedAttempt(
                summary="Compared papers without matching source count",
                why_failed="The comparison mixed latency with source-count effects.",
                do_not_repeat="Do not compare sources without matching source count.",
            )
        ],
        suggested_next_step="Find a matched source-count comparison",
        transcript_text="PRIVATE_TRANSCRIPT_TEXT",
    )

    for event in events_from_research_session(report):
        state_engine.accept_event(event)

    brief = service.create_context_brief(AgentContextSurface(kind="research-agent", name="test"))
    packet = service.create_continuity_packet_from_brief(brief, context_pack="research")
    dumped = packet.model_dump_json()

    assert packet.context_pack == "research"
    assert packet.surface == "research-agent"
    assert packet.intent is not None
    assert packet.intent.summary == "Assess whether retrieval latency changes answer quality"
    assert any(
        artifact.identifier == "doi:10.0000/example-a"
        and artifact.summary == "Metadata-only source summary"
        for artifact in packet.artifacts
    )
    assert any(
        artifact.kind == "note" and artifact.summary == "Note metadata summary"
        for artifact in packet.artifacts
    )
    assert {decision.summary for decision in packet.decisions} == {
        "Treat dataset size as a confound",
        "Lower latency may improve iterative answer quality",
    }
    assert packet.attempts[0].summary == "Compared papers without matching source count"
    assert packet.attempts[0].failure_reason == (
        "The comparison mixed latency with source-count effects."
    )
    assert [item.path for item in packet.do_not_repeat] == [
        "Do not compare sources without matching source count."
    ]
    assert packet.suggested_next_steps == ["Find a matched source-count comparison"]
    assert {item.category for item in packet.withheld_context} >= {"payload_content"}
    assert "PRIVATE_ARTICLE_TEXT" not in dumped
    assert "PRIVATE_NOTE_TEXT" not in dumped
    assert "PRIVATE_TRANSCRIPT_TEXT" not in dumped
