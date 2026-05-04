from __future__ import annotations

from devcd.slices.events.models import DevEvent, EventSensitivity, EventSource
from devcd.slices.policy_layer.service import PolicyEngine


def test_default_policy_denies_remote_export_and_actions() -> None:
    policy = PolicyEngine.default()

    export_decision = policy.decide_remote_export("https://example.invalid")
    action_decision = policy.decide_action("commit")

    assert not export_decision.allowed
    assert export_decision.operation == "export"
    assert "local-first" in export_decision.reason
    assert not action_decision.allowed
    assert action_decision.operation == "action"
    assert "observe-only" in action_decision.reason


def test_policy_denies_events_from_disabled_source() -> None:
    policy = PolicyEngine(
        allow_observation=True,
        allow_local_storage=True,
        allow_remote_export=False,
        allow_actions=False,
        enabled_sources={"git"},
        allowed_data_classes={"metadata"},
    )

    decision = policy.decide_observation(
        DevEvent(source=EventSource.IDE, type="file_focus", payload={"path": "src/app.py"})
    )

    assert not decision.allowed
    assert decision.operation == "observe"
    assert decision.source == "ide"
    assert "not enabled" in decision.reason


def test_policy_denies_fulltext_payload_and_disallowed_data_class() -> None:
    policy = PolicyEngine.default()

    fulltext_decision = policy.decide_observation(
        DevEvent(source=EventSource.NOTES, type="note_update", payload={"body": "private"})
    )
    data_class_decision = policy.decide_observation(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            payload={"branch": "feature/context-daemon"},
            data_class="secret",
        )
    )

    assert not fulltext_decision.allowed
    assert fulltext_decision.operation == "observe"
    assert "metadata-only" in fulltext_decision.reason
    assert not data_class_decision.allowed
    assert data_class_decision.data_class == "secret"
    assert "data class" in data_class_decision.reason


def test_policy_denies_sensitive_events_with_explainable_reason() -> None:
    policy = PolicyEngine.default()

    decision = policy.decide_observation(
        DevEvent(
            source=EventSource.NOTES,
            type="note_update",
            payload={"title": "Private note"},
            sensitivity=EventSensitivity.SENSITIVE,
        )
    )

    assert not decision.allowed
    assert decision.operation == "observe"
    assert decision.data_class == "metadata"
    assert "sensitive events" in decision.reason


def test_browser_source_is_opt_in_by_default() -> None:
    policy = PolicyEngine.default()

    decision = policy.decide_observation(
        DevEvent(
            source=EventSource.BROWSER,
            type="url_focus",
            payload={"url": "https://example.invalid"},
        )
    )

    assert not decision.allowed
    assert decision.source == "browser"
    assert "not enabled" in decision.reason
