from __future__ import annotations

import json
import os
from contextlib import contextmanager
from io import TextIOWrapper
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from devcd.slices.events.models import DevEvent, SubtaskCompletionEvent
from devcd.slices.policy_layer.models import PolicyDecision

if os.name == "nt":
    import msvcrt
else:
    import fcntl


class EventLedger:
    def __init__(self, path: Path | None) -> None:
        self._path = path

    @classmethod
    def local_default(cls) -> EventLedger:
        return cls(Path(".devcd/events.jsonl"))

    @classmethod
    def disabled(cls) -> EventLedger:
        return cls(None)

    def append(self, event: DevEvent | SubtaskCompletionEvent, decision: PolicyDecision) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        validated_event = _validate_ledger_event(event)
        validated_decision = PolicyDecision.model_validate(decision.model_dump(mode="json"))
        record = {
            "event": validated_event.model_dump(mode="json"),
            "policy_decision": validated_decision.model_dump(mode="json"),
        }
        with _locked_append_handle(self._path) as handle:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")

    def read_records(self) -> list[tuple[DevEvent, PolicyDecision]]:
        if self._path is None or not self._path.exists():
            return []

        records: list[tuple[DevEvent, PolicyDecision]] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw_record = _parse_record(line)
            if raw_record is None:
                continue
            raw_event = raw_record.get("event")
            raw_policy = raw_record.get("policy_decision")
            if not isinstance(raw_event, dict) or not isinstance(raw_policy, dict):
                continue
            raw_policy_decision = dict(raw_policy)
            raw_policy_decision.setdefault("operation", "store")
            try:
                event = DevEvent.model_validate(raw_event, strict=False)
                decision = PolicyDecision.model_validate(raw_policy_decision, strict=False)
            except ValidationError:
                continue
            records.append((event, decision))
        return records

    def read_subtask_completion_events(self) -> list[SubtaskCompletionEvent]:
        if self._path is None or not self._path.exists():
            return []

        events: list[SubtaskCompletionEvent] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw_record = _parse_record(line)
            if raw_record is None:
                continue
            raw_event = raw_record.get("event")
            if not isinstance(raw_event, dict):
                continue
            if raw_event.get("event_type") != "subtask_completion":
                continue
            try:
                event = SubtaskCompletionEvent.model_validate(raw_event, strict=False)
            except ValidationError:
                continue
            events.append(event)
        return events


def _validate_ledger_event(
    event: DevEvent | SubtaskCompletionEvent,
) -> DevEvent | SubtaskCompletionEvent:
    if isinstance(event, SubtaskCompletionEvent):
        return SubtaskCompletionEvent.model_validate(event.model_dump(mode="json"), strict=False)
    return DevEvent.model_validate(event.model_dump(mode="json"), strict=False)


def _parse_record(line: str) -> dict[str, Any] | None:
    try:
        raw_record = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(raw_record, dict):
        return None
    return raw_record


@contextmanager
def _locked_append_handle(path: Path) -> Any:
    with path.open("a", encoding="utf-8") as handle:
        _acquire_file_lock(handle)
        try:
            yield handle
        finally:
            _release_file_lock(handle)


def _acquire_file_lock(handle: TextIOWrapper) -> None:
    if os.name == "nt":
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        return
    flock = getattr(fcntl, "flock", None)
    lock_ex = getattr(fcntl, "LOCK_EX", None)
    if callable(flock) and lock_ex is not None:
        flock(handle.fileno(), lock_ex)


def _release_file_lock(handle: TextIOWrapper) -> None:
    if os.name == "nt":
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    flock = getattr(fcntl, "flock", None)
    lock_un = getattr(fcntl, "LOCK_UN", None)
    if callable(flock) and lock_un is not None:
        flock(handle.fileno(), lock_un)
