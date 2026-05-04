from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class FreshnessStatus(StrEnum):
    CURRENT = "current"
    AGING = "aging"
    STALE = "stale"
    EXPIRED = "expired"


class SurfaceKind(StrEnum):
    CODING_AGENT = "coding-agent"
    REVIEW_AGENT = "review-agent"
    DEBUGGING_AGENT = "debugging-agent"
    SUBAGENT = "subagent"
    PUBLIC_DEMO = "public-demo"
    HTTP = "http"
    CLI = "cli"
    ARTIFACT = "artifact"
    MCP = "mcp"
    VSCODE = "vscode"
    OTHER = "other"


class DetailLevel(StrEnum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    DIAGNOSTIC = "diagnostic"


class IntentStatus(StrEnum):
    ACTIVE = "active"
    CANDIDATE = "candidate"
    STALE = "stale"
    UNCERTAIN = "uncertain"


class OpenLoopKind(StrEnum):
    TASK = "task"
    FAILURE = "failure"
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    REVIEW = "review"
    UNKNOWN = "unknown"


class OpenLoopStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    STALE = "stale"
    DISMISSED = "dismissed"


class ProactiveSuggestionStatus(StrEnum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class FreshnessState(BaseModel):
    status: FreshnessStatus
    last_seen_at: datetime
    expires_at: datetime | None = None


class EvidenceItem(BaseModel):
    source: str
    event_type: str | None = None
    summary: str
    timestamp: datetime
    policy_reason: str


class PolicySummary(BaseModel):
    allowed: bool
    operation: str
    reason: str
    included_sources: list[str] = Field(default_factory=list)
    withheld_sources: list[str] = Field(default_factory=list)
    included_data_classes: list[str] = Field(default_factory=list)
    withheld_data_classes: list[str] = Field(default_factory=list)


class WithheldContext(BaseModel):
    kind: str
    reason: str
    category: str = ""
    policy_reason: str = ""
    safe_summary: str = ""


class GitContext(BaseModel):
    branch: str | None = None
    latest_commit: str | None = None
    latest_commit_summary: str | None = None
    repository: str | None = None


class AgentContextSurface(BaseModel):
    kind: SurfaceKind = SurfaceKind.HTTP
    name: str = "local-client"
    detail_level: DetailLevel = DetailLevel.STANDARD
    requested_sources: list[str] = Field(default_factory=list)
    requested_data_classes: list[str] = Field(default_factory=lambda: ["metadata"])
    allowed_state_areas: list[str] = Field(default_factory=list)
    allowed_memory_scopes: list[str] = Field(default_factory=list)
    withheld_fields: list[str] = Field(default_factory=list)


class IntentLine(BaseModel):
    summary: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    started_at: datetime | None = None
    updated_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    status: IntentStatus


class RelevantArtifact(BaseModel):
    kind: str
    identifier: str
    summary: str
    source: str
    relevance: float = Field(ge=0.0, le=1.0)
    last_seen_at: datetime
    policy_reason: str


class OpenLoop(BaseModel):
    id: str
    summary: str
    kind: OpenLoopKind
    evidence: list[EvidenceItem] = Field(default_factory=list)
    status: OpenLoopStatus
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime
    updated_at: datetime


class RecentAttempt(BaseModel):
    timestamp: datetime
    source: str
    type: str
    summary: str
    outcome: Literal["unknown", "success", "failure", "interrupted"] = "unknown"
    policy_reason: str


class BlockerSignal(BaseModel):
    summary: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    detected_at: datetime
    suppressed_until: datetime | None = None


class ProactiveSuggestion(BaseModel):
    id: str
    summary: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    status: ProactiveSuggestionStatus
    created_at: datetime
    suppressed_until: datetime | None = None


class ContextMemoryItem(BaseModel):
    id: str
    scope: Literal["working", "episodic", "semantic"]
    summary: str
    source: str | None = None
    freshness: FreshnessState
    confidence: float = Field(ge=0.0, le=1.0)
    policy_reason: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None


class MemoryCorrection(BaseModel):
    summary: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class WorkState(BaseModel):
    active_intent: IntentLine | None = None
    candidate_intents: list[IntentLine] = Field(default_factory=list)
    relevant_artifacts: list[RelevantArtifact] = Field(default_factory=list)
    open_loops: list[OpenLoop] = Field(default_factory=list)
    recent_attempts: list[RecentAttempt] = Field(default_factory=list)
    blockers: list[BlockerSignal] = Field(default_factory=list)
    suggestions: list[ProactiveSuggestion] = Field(default_factory=list, max_length=3)
    freshness: FreshnessState = Field(
        default_factory=lambda: FreshnessState(
            status=FreshnessStatus.CURRENT,
            last_seen_at=datetime.now(UTC),
        )
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    policy_summary: PolicySummary
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ContextBrief(BaseModel):
    surface: AgentContextSurface
    summary: str
    active_goal: str | None = None
    active_intent: IntentLine | None = None
    relevant_artifacts: list[RelevantArtifact] = Field(default_factory=list)
    git_context: GitContext = Field(default_factory=GitContext)
    open_loops: list[OpenLoop] = Field(default_factory=list)
    recent_attempts: list[RecentAttempt] = Field(default_factory=list)
    blockers: list[BlockerSignal] = Field(default_factory=list)
    suggested_next_steps: list[ProactiveSuggestion] = Field(default_factory=list, max_length=3)
    withheld_context: list[WithheldContext] = Field(default_factory=list)
    withheld: list[WithheldContext] = Field(default_factory=list)
    agent_limitations: list[str] = Field(default_factory=list)
    policy_decision: PolicySummary
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
