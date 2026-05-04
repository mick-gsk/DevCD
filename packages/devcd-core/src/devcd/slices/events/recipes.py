from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from devcd.slices.events.models import DevEvent, EventSensitivity, EventSource


class PytestFailure(BaseModel):
    nodeid: str = Field(min_length=1)
    file_path: str | None = None
    line: int | None = Field(default=None, ge=1)


class PytestFailureRecipeInput(BaseModel):
    command: str = Field(default="pytest", min_length=1)
    exit_code: int = 1
    failures: list[PytestFailure] = Field(default_factory=list)
    stdout: str | None = None
    stderr: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


def events_from_pytest_failure(report: PytestFailureRecipeInput) -> list[DevEvent]:
    first_failure = report.failures[0] if report.failures else None
    failed_nodeids = [failure.nodeid for failure in report.failures]
    reason = _failure_reason(first_failure, len(report.failures))
    payload: dict[str, object] = {
        "recipe": "pytest_failure",
        "command": report.command,
        "exit_code": report.exit_code,
        "failure_count": len(report.failures),
        "failed_nodeids": failed_nodeids,
        "first_failure": _failure_payload(first_failure),
        "reason": reason,
        "suggested_next_action": _suggested_next_action(report.command, first_failure),
    }
    events = [
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=report.timestamp,
            payload=payload,
        )
    ]
    raw_output = _raw_output(report)
    if raw_output is not None:
        events.append(
            DevEvent(
                source=EventSource.TASK,
                type="test_output",
                timestamp=report.timestamp,
                payload={"recipe": "pytest_failure", "output": raw_output},
                sensitivity=EventSensitivity.SENSITIVE,
            )
        )
    return events


def _failure_reason(first_failure: PytestFailure | None, failure_count: int) -> str:
    if first_failure is None:
        return "pytest failed"
    if failure_count == 1:
        return f"pytest failed: {first_failure.nodeid}"
    return f"pytest failed: {failure_count} tests, first failure: {first_failure.nodeid}"


def _failure_payload(first_failure: PytestFailure | None) -> dict[str, object]:
    if first_failure is None:
        return {}
    payload: dict[str, object] = {"nodeid": first_failure.nodeid}
    if first_failure.file_path is not None:
        payload["file_path"] = first_failure.file_path
    if first_failure.line is not None:
        payload["line"] = first_failure.line
    return payload


def _suggested_next_action(command: str, first_failure: PytestFailure | None) -> str:
    if first_failure is None:
        return f"Rerun {command} and inspect the first failing test"

    rerun = f"Rerun {_pytest_command_prefix(command)} {first_failure.nodeid}"
    if " -q" in f" {command} ":
        rerun = f"{rerun} -q"
    location = first_failure.nodeid
    if first_failure.file_path is not None and first_failure.line is not None:
        location = f"{first_failure.file_path}:{first_failure.line}"
    elif first_failure.file_path is not None:
        location = first_failure.file_path
    return f"{rerun} and inspect {location}"


def _pytest_command_prefix(command: str) -> str:
    parts = command.split()
    if len(parts) >= 3 and parts[0] == "python" and parts[1] == "-m" and parts[2] == "pytest":
        return "python -m pytest"
    return "pytest"


def _raw_output(report: PytestFailureRecipeInput) -> str | None:
    parts = [part.strip() for part in (report.stdout, report.stderr) if part and part.strip()]
    if not parts:
        return None
    return "\n".join(parts)
