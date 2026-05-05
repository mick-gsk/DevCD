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


class ResearchSource(BaseModel):
    title: str = Field(min_length=1)
    url: str | None = None
    reference: str | None = None
    source_type: str = Field(min_length=1)
    summary: str | None = None
    full_text: str | None = None


class ResearchNoteMetadata(BaseModel):
    title: str = Field(min_length=1)
    summary: str | None = None
    reference: str | None = None
    raw_text: str | None = None


class ResearchFailedAttempt(BaseModel):
    summary: str = Field(min_length=1)
    why_failed: str = Field(min_length=1)
    do_not_repeat: str | list[str] | None = None
    suggested_next_step: str | None = None


class ResearchSessionRecipeInput(BaseModel):
    goal: str = Field(min_length=1)
    reviewed_sources: list[ResearchSource] = Field(default_factory=list)
    notes: list[ResearchNoteMetadata] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    failed_attempts: list[ResearchFailedAttempt] = Field(default_factory=list)
    suggested_next_step: str | None = None
    raw_note_text: str | None = None
    article_text: str | None = None
    transcript_text: str | None = None
    full_content: str | None = None
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


def events_from_research_session(report: ResearchSessionRecipeInput) -> list[DevEvent]:
    events: list[DevEvent] = [
        DevEvent(
            source=EventSource.TASK,
            type="research_goal",
            timestamp=report.timestamp,
            payload={"recipe": "research_session", "current_goal": report.goal},
        )
    ]
    sensitive_events: list[DevEvent] = []
    for source in report.reviewed_sources:
        source_id = source.reference or source.url or source.title
        payload: dict[str, object] = {
            "recipe": "research_session",
            "source_id": source_id,
            "title": source.title,
            "source_type": source.source_type,
            "kind": "source",
        }
        if source.url is not None:
            payload["url"] = source.url
        if source.reference is not None:
            payload["reference"] = source.reference
        if source.summary is not None:
            payload["summary"] = source.summary
        events.append(
            DevEvent(
                source=EventSource.NOTES,
                type="source_review",
                timestamp=report.timestamp,
                payload=payload,
            )
        )
        if source.full_text is not None:
            sensitive_events.append(
                _sensitive_research_event(
                    event_type="source_full_text",
                    timestamp=report.timestamp,
                    payload={
                        "recipe": "research_session",
                        "source_id": source_id,
                        "title": source.title,
                        "full_text": source.full_text,
                    },
                )
            )

    for note in report.notes:
        payload = {
            "recipe": "research_session",
            "title": note.title,
            "kind": "note",
        }
        if note.summary is not None:
            payload["summary"] = note.summary
        if note.reference is not None:
            payload["reference"] = note.reference
        events.append(
            DevEvent(
                source=EventSource.NOTES,
                type="note_update",
                timestamp=report.timestamp,
                payload=payload,
            )
        )
        if note.raw_text is not None:
            sensitive_events.append(
                _sensitive_research_event(
                    event_type="note_update",
                    timestamp=report.timestamp,
                    payload={
                        "recipe": "research_session",
                        "title": note.title,
                        "text": note.raw_text,
                    },
                )
            )

    for hypothesis in report.hypotheses:
        if hypothesis.strip():
            events.append(
                DevEvent(
                    source=EventSource.NOTES,
                    type="hypothesis",
                    timestamp=report.timestamp,
                    payload={"recipe": "research_session", "summary": hypothesis},
                )
            )
    for decision in report.decisions:
        if decision.strip():
            events.append(
                DevEvent(
                    source=EventSource.NOTES,
                    type="decision",
                    timestamp=report.timestamp,
                    payload={"recipe": "research_session", "summary": decision},
                )
            )
    for attempt in report.failed_attempts:
        payload = {
            "recipe": "research_session",
            "summary": attempt.summary,
            "why_attempt_failed": attempt.why_failed,
            "suggested_next_action": attempt.suggested_next_step or report.suggested_next_step,
        }
        if attempt.do_not_repeat is not None:
            payload["do_not_repeat"] = attempt.do_not_repeat
        events.append(
            DevEvent(
                source=EventSource.NOTES,
                type="failed_attempt",
                timestamp=report.timestamp,
                payload={key: value for key, value in payload.items() if value is not None},
            )
        )

    for event_type, payload in _root_sensitive_payloads(report):
        sensitive_events.append(
            _sensitive_research_event(
                event_type=event_type,
                timestamp=report.timestamp,
                payload=payload,
            )
        )
    events.extend(sensitive_events)
    return events


def _sensitive_research_event(
    *,
    event_type: str,
    timestamp: datetime,
    payload: dict[str, object],
) -> DevEvent:
    return DevEvent(
        source=EventSource.NOTES,
        type=event_type,
        timestamp=timestamp,
        payload=payload,
        sensitivity=EventSensitivity.SENSITIVE,
    )


def _root_sensitive_payloads(
    report: ResearchSessionRecipeInput,
) -> list[tuple[str, dict[str, object]]]:
    payloads: list[tuple[str, dict[str, object]]] = []
    if report.raw_note_text is not None:
        payloads.append(
            (
                "note_update",
                {"recipe": "research_session", "text": report.raw_note_text},
            )
        )
    if report.article_text is not None:
        payloads.append(
            (
                "source_full_text",
                {"recipe": "research_session", "full_text": report.article_text},
            )
        )
    if report.transcript_text is not None:
        payloads.append(
            (
                "transcript_update",
                {"recipe": "research_session", "text": report.transcript_text},
            )
        )
    if report.full_content is not None:
        payloads.append(
            (
                "full_content",
                {"recipe": "research_session", "content": report.full_content},
            )
        )
    return payloads


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
