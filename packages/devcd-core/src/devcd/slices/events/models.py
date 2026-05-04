from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

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
    source: EventSource
    type: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
    sensitivity: EventSensitivity = EventSensitivity.NORMAL
