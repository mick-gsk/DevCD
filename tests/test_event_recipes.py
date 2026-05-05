from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from devcd.slices.events.models import EventSensitivity, EventSource
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


def test_pytest_failure_recipe_emits_metadata_event_and_sensitive_output_event() -> None:
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
        stdout="E   AssertionError: SECRET_TOKEN=abc123",
    )

    events = events_from_pytest_failure(report)

    assert len(events) == 2
    failure_event = events[0]
    assert failure_event.source is EventSource.TASK
    assert failure_event.type == "test_failure"
    assert failure_event.sensitivity is EventSensitivity.NORMAL
    assert failure_event.data_class == "metadata"
    assert failure_event.payload == {
        "recipe": "pytest_failure",
        "command": "pytest tests/test_checkout.py -q",
        "exit_code": 1,
        "failure_count": 1,
        "failed_nodeids": ["tests/test_checkout.py::test_total"],
        "first_failure": {
            "nodeid": "tests/test_checkout.py::test_total",
            "file_path": "tests/test_checkout.py",
            "line": 42,
        },
        "reason": "pytest failed: tests/test_checkout.py::test_total",
        "suggested_next_action": (
            "Rerun pytest tests/test_checkout.py::test_total -q and inspect "
            "tests/test_checkout.py:42"
        ),
    }
    assert "SECRET_TOKEN" not in failure_event.model_dump_json()

    output_event = events[1]
    assert output_event.source is EventSource.TASK
    assert output_event.type == "test_output"
    assert output_event.sensitivity is EventSensitivity.SENSITIVE
    assert output_event.data_class == "metadata"
    assert output_event.payload["recipe"] == "pytest_failure"
    assert "SECRET_TOKEN=abc123" in str(output_event.payload["output"])


def test_pytest_failure_recipe_without_raw_output_emits_one_failure_event() -> None:
    report = PytestFailureRecipeInput(
        command="pytest",
        exit_code=1,
        failures=[PytestFailure(nodeid="tests/test_state.py::test_state_updates")],
    )

    events = events_from_pytest_failure(report)

    assert len(events) == 1
    assert events[0].type == "test_failure"
    assert events[0].payload["reason"] == "pytest failed: tests/test_state.py::test_state_updates"


def test_research_session_recipe_validates_required_goal_and_sources() -> None:
    with pytest.raises(ValidationError):
        ResearchSessionRecipeInput(goal="", reviewed_sources=[])

    with pytest.raises(ValidationError):
        ResearchSource(title="", reference="doi:10.0000/example", source_type="paper")

    with pytest.raises(ValidationError):
        ResearchSource(
            title="Latency and answer quality",
            reference="doi:10.0000/example",
            source_type="",
        )

    report = ResearchSessionRecipeInput(
        goal="Assess whether retrieval latency changes answer quality",
        reviewed_sources=[
            ResearchSource(
                title="Latency and answer quality",
                reference="doi:10.0000/example",
                source_type="paper",
            )
        ],
    )

    assert report.goal == "Assess whether retrieval latency changes answer quality"
    assert report.reviewed_sources[0].source_type == "paper"


def test_research_session_recipe_emits_metadata_events_and_sensitive_full_content() -> None:
    report = ResearchSessionRecipeInput(
        goal="Assess whether retrieval latency changes answer quality",
        timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
        reviewed_sources=[
            ResearchSource(
                title="Latency and answer quality",
                url="https://example.invalid/paper",
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
            )
        ],
        suggested_next_step="Find a matched source-count comparison",
        transcript_text="PRIVATE_TRANSCRIPT_TEXT",
        full_content="PRIVATE_FULL_CONTENT",
    )

    events = events_from_research_session(report)

    assert [event.type for event in events[:6]] == [
        "research_goal",
        "source_review",
        "note_update",
        "hypothesis",
        "decision",
        "failed_attempt",
    ]
    assert events[0].source is EventSource.TASK
    assert events[0].payload == {
        "recipe": "research_session",
        "current_goal": "Assess whether retrieval latency changes answer quality",
    }
    source_event = events[1]
    assert source_event.source is EventSource.NOTES
    assert source_event.sensitivity is EventSensitivity.NORMAL
    assert source_event.payload["title"] == "Latency and answer quality"
    assert source_event.payload["url"] == "https://example.invalid/paper"
    assert source_event.payload["source_type"] == "paper"
    assert source_event.payload["kind"] == "source"
    assert "PRIVATE" not in source_event.model_dump_json()
    assert events[5].payload["suggested_next_action"] == "Find a matched source-count comparison"
    assert events[5].payload["why_attempt_failed"] == (
        "The comparison mixed latency with source-count effects."
    )

    sensitive_events = [
        event for event in events if event.sensitivity is EventSensitivity.SENSITIVE
    ]
    assert [event.type for event in sensitive_events] == [
        "source_full_text",
        "note_update",
        "transcript_update",
        "full_content",
    ]
    assert all(event.data_class == "metadata" for event in sensitive_events)
    assert "PRIVATE_ARTICLE_TEXT" in sensitive_events[0].payload["full_text"]
    assert "PRIVATE_NOTE_TEXT" in sensitive_events[1].payload["text"]
