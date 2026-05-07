from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class EventSource(StrEnum):
    IDE = "ide"
    GIT = "git"
    TASK = "task"
    NOTES = "notes"
    BROWSER = "browser"
    SYSTEM = "system"


class EventSensitivity(StrEnum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"


class DevEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    source: EventSource
    type: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
    event_class: str | None = None
    sensitivity: EventSensitivity = EventSensitivity.NORMAL
    data_class: str = Field(default="metadata", min_length=1)

    @model_validator(mode="after")
    def validate_event_class_payload(self) -> DevEvent:
        if self.event_class == "dead_end":
            for field_name in ("approach_summary", "reason", "related_goal"):
                value = self.payload.get(field_name)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"event_class 'dead_end' requires payload field '{field_name}'"
                    )
        if self.event_class == "goal.done_when":
            value = self.payload.get("done_when")
            if not isinstance(value, str) or not value.strip():
                raise ValueError("event_class 'goal.done_when' requires payload field 'done_when'")
        return self


class SubtaskCompletionEvent(BaseModel):
    event_type: Literal["subtask_completion"]
    subtask_id: str
    status: Literal["complete", "incomplete", "reverted"]
    completion_marker: str
    timestamp: datetime
