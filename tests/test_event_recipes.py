from __future__ import annotations

from datetime import UTC, datetime

from devcd.slices.events.models import EventSensitivity, EventSource
from devcd.slices.events.recipes import (
    PytestFailure,
    PytestFailureRecipeInput,
    events_from_pytest_failure,
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
