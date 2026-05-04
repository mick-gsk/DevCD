from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryScope(StrEnum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    scope: MemoryScope
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content: dict[str, Any]
