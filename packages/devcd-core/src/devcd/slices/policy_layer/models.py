from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class PolicyDecisionKind(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyDecision(BaseModel):
    kind: PolicyDecisionKind
    reason: str
    operation: str
    source: str | None = None
    data_class: str | None = None

    @property
    def allowed(self) -> bool:
        return self.kind is PolicyDecisionKind.ALLOW
