from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


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
    sensitivity: EventSensitivity = EventSensitivity.NORMAL
    data_class: str = Field(default="metadata", min_length=1)
