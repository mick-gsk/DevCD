from __future__ import annotations

from datetime import UTC, datetime

import pytest

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
from devcd.slices.ambient_context.service import (
    AmbientContextService,
    render_context_brief_markdown,
)
from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSource
from devcd.slices.events.recipes import (
    PytestFailure,
    PytestFailureRecipeInput,
    events_from_pytest_failure,
)
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
    assert "pytest failed: tests/test_checkout.py::test_total" in markdown
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
    service = AmbientContextService(state_engine, memory_store, policy_engine)
    return service, state_engine
