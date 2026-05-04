from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RecentAction(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str
    type: str
    summary: str
    policy_reason: str


class DevState(BaseModel):
    current_goal: str | None = None
    subtask: str | None = None
    recent_actions: list[RecentAction] = Field(default_factory=list, max_length=20)
    interruptibility: Literal["low", "medium", "high"] = "high"
    attention_score: dict[str, float] = Field(default_factory=dict)
    blocked_by: str | None = None
    confidence: dict[str, float] = Field(default_factory=dict)
    next_best_actions: list[str] = Field(default_factory=list)
    source_active_map: dict[str, bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
