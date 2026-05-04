from __future__ import annotations

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class PolicyDecisionKind(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    kind: PolicyDecisionKind
    reason: str
    operation: str
    source: str | None = None
    data_class: str | None = None

    @property
    def allowed(self) -> bool:
        return self.kind is PolicyDecisionKind.ALLOW


class PolicyDecisionExplanation(BaseModel):
    decision_id: str
    allowed: bool
    kind: PolicyDecisionKind
    operation: str
    reason: str
    category: str
    source: str | None = None
    data_class: str | None = None
    safe_summary: str = ""


class PolicySimulationReport(BaseModel):
    surface: str
    mutates_state: bool = False
    decisions: list[PolicyDecisionExplanation] = Field(default_factory=list)
    withheld: list[PolicyDecisionExplanation] = Field(default_factory=list)
