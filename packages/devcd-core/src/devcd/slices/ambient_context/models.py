from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from devcd.slices.vision_layer.models import VisionBlock


class FreshnessStatus(StrEnum):
    CURRENT = "current"
    AGING = "aging"
    STALE = "stale"
    EXPIRED = "expired"


class SurfaceKind(StrEnum):
    CODING_AGENT = "coding-agent"
    REVIEW_AGENT = "review-agent"
    RESEARCH_AGENT = "research-agent"
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


class ContextFeedbackKind(StrEnum):
    MISSING = "missing"
    WRONG = "wrong"
    STALE = "stale"
    TOO_BROAD = "too_broad"
    TOO_SENSITIVE = "too_sensitive"


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


class ContextPackEventSupport(BaseModel):
    source: str = Field(min_length=1)
    event_types: list[str] = Field(default_factory=list)


class ContextPack(BaseModel):
    id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    supported_events: list[ContextPackEventSupport] = Field(default_factory=list)
    supported_surfaces: list[str] = Field(default_factory=list)
    default_sensitivity: str = Field(min_length=1)
    policy_notes: list[str] = Field(default_factory=list)
    remote_export_enabled_by_default: bool = False
    renderer_metadata: dict[str, Any] = Field(default_factory=dict)


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


class AgentResurrectionContext(BaseModel):
    current_goal: str | None = None
    last_attempt: RecentAttempt | None = None
    last_failure: str | None = None
    last_attempted_fix: str | None = None
    why_attempt_failed: str | None = None
    why_it_failed: str | None = None
    do_not_repeat: list[str] = Field(default_factory=list)
    suggested_next_action: str | None = None
    unknowns: list[str] = Field(default_factory=list)


class ContinuityIntent(BaseModel):
    summary: str = Field(min_length=1)
    status: IntentStatus = IntentStatus.ACTIVE
    evidence: list[EvidenceItem] = Field(default_factory=list)
    started_at: datetime | None = None
    updated_at: datetime
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ContinuityArtifact(BaseModel):
    kind: str = Field(min_length=1)
    identifier: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source: str = Field(min_length=1)
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    last_seen_at: datetime
    policy_reason: str = Field(min_length=1)


class ContinuityAttempt(BaseModel):
    timestamp: datetime
    source: str = Field(min_length=1)
    type: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    outcome: Literal["unknown", "success", "failure", "interrupted"] = "unknown"
    failure_reason: str | None = None
    policy_reason: str = Field(min_length=1)


class ContinuityBlocker(BaseModel):
    kind: str = Field(default="blocker", min_length=1)
    summary: str = Field(min_length=1)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    detected_at: datetime
    reason: str | None = None
    policy_reason: str = Field(default="visible blocker signal is allowed by policy", min_length=1)


class ContinuityDecision(BaseModel):
    kind: str = Field(default="decision", min_length=1)
    summary: str = Field(min_length=1)
    source: str = Field(min_length=1)
    decided_at: datetime
    policy_reason: str = Field(min_length=1)


class ContinuityPreference(BaseModel):
    summary: str = Field(min_length=1)
    source: str = Field(min_length=1)
    policy_reason: str = Field(min_length=1)


class ContextReference(BaseModel):
    kind: str = Field(min_length=1)
    identifier: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source: str = Field(min_length=1)
    load_hint: str = Field(min_length=1)
    include_reason: str = Field(min_length=1)
    freshness: FreshnessState
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    policy_reason: str = Field(min_length=1)
    discard_reason: str | None = None


class ContextBudget(BaseModel):
    estimated_tokens: int = Field(default=0, ge=0)
    reference_count: int = Field(default=0, ge=0)
    withheld_context_count: int = Field(default=0, ge=0)
    sync_warning_ab: float = Field(default=0.5, ge=0.0, le=1.0)
    switch_recommended_ab: float = Field(default=0.7, ge=0.0, le=1.0)
    included_sources: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)


class StateSnapshotModel(BaseModel):
    keys: list[str] = Field(default_factory=list)
    values: list[str | int | bool] = Field(default_factory=list)


class SessionContract(BaseModel):
    next_action: str = Field(min_length=1)
    definition_of_done: str = Field(min_length=1)
    verification_command: str = Field(min_length=1)
    clean_state_required: bool = True
    sync_warning_ab: float = Field(default=0.5, ge=0.0, le=1.0)
    switch_recommended_ab: float = Field(default=0.7, ge=0.0, le=1.0)


class ContinuityPacket(BaseModel):
    schema_version: str = "1"
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    context_pack: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    intent: ContinuityIntent | None = None
    artifacts: list[ContinuityArtifact] = Field(default_factory=list)
    decisions: list[ContinuityDecision] = Field(default_factory=list)
    attempts: list[ContinuityAttempt] = Field(default_factory=list)
    blockers: list[ContinuityBlocker] = Field(default_factory=list)
    preferences: list[ContinuityPreference] = Field(default_factory=list)
    do_not_repeat: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    context_quality_notes: list[str] = Field(default_factory=list)
    context_references: list[ContextReference] = Field(default_factory=list)
    context_budget: ContextBudget = Field(default_factory=ContextBudget)
    state_snapshot: StateSnapshotModel = Field(default_factory=StateSnapshotModel)
    narrative_context: str = ""
    decision_log: list[str] = Field(default_factory=list)
    priority_queue: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    session_contract: SessionContract | None = None
    withheld_context: list[WithheldContext] = Field(default_factory=list)
    policy_decision: PolicySummary
    vision: VisionBlock | None = Field(default=None)
    provenance: list[str] = Field(default_factory=list)
    pack_metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("narrative_context")
    @classmethod
    def narrative_context_max_length(cls, value: str) -> str:
        if len(value) > 500:
            raise ValueError("narrative_context must be 500 characters or fewer")
        return value


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


class ContextFeedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    brief_id: str = Field(min_length=1)
    kind: ContextFeedbackKind
    note: str | None = None
    note_withheld: bool = False
    withheld_context: list[WithheldContext] = Field(default_factory=list)
    policy_reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ContextQualityReport(BaseModel):
    feedback: list[ContextFeedback] = Field(default_factory=list)
    phase: Literal["deterministic_feedback_loop"] = "deterministic_feedback_loop"
    ranking_or_scoring: Literal["deterministic_local_score"] = "deterministic_local_score"
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    category_counts: dict[str, int] = Field(default_factory=dict)
    summary_notes: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    suggested_next_actions: list[str] = Field(default_factory=list)
    withheld_feedback_count: int = Field(default=0, ge=0)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ContextBudgetReport(BaseModel):
    schema_version: str = "1"
    surface: str = Field(min_length=1)
    context_pack: str = Field(min_length=1)
    estimated_tokens: int = Field(default=0, ge=0)
    reference_count: int = Field(default=0, ge=0)
    withheld_context_count: int = Field(default=0, ge=0)
    included_sources: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    context_references: list[ContextReference] = Field(default_factory=list)
    session_contract: SessionContract | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ContextControlContinuityPreview(BaseModel):
    context_pack: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    active_goal: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    artifact_count: int = Field(default=0, ge=0)
    attempt_count: int = Field(default=0, ge=0)
    blocker_count: int = Field(default=0, ge=0)
    withheld_context_count: int = Field(default=0, ge=0)
    suggested_next_steps: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class ContextControlQualitySummary(BaseModel):
    feedback_count: int = Field(default=0, ge=0)
    phase: str = "deterministic_feedback_loop"
    ranking_or_scoring: str = "deterministic_local_score"
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    category_counts: dict[str, int] = Field(default_factory=dict)
    latest_notes: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    suggested_next_actions: list[str] = Field(default_factory=list)


class ContextControlReport(BaseModel):
    schema_version: str = "1"
    active_goal: str | None = None
    selected_pack: str | None = None
    selected_surface: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    visible_sources: list[str] = Field(default_factory=list)
    withheld_sources: list[WithheldContext] = Field(default_factory=list)
    included_data_classes: list[str] = Field(default_factory=list)
    withheld_data_classes: list[str] = Field(default_factory=list)
    memory_counts_by_scope: dict[str, int] = Field(default_factory=dict)
    recent_timeline_summary: list[RecentAttempt] = Field(default_factory=list)
    latest_policy_reasons: list[str] = Field(default_factory=list)
    continuity_packet_preview: ContextControlContinuityPreview
    context_quality_summary: ContextControlQualitySummary | None = None
    next_commands: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


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
    schema_version: str = "1"
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    surface: AgentContextSurface
    summary: str
    active_goal: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    active_intent: IntentLine | None = None
    relevant_artifacts: list[RelevantArtifact] = Field(default_factory=list)
    git_context: GitContext = Field(default_factory=GitContext)
    open_loops: list[OpenLoop] = Field(default_factory=list)
    recent_attempts: list[RecentAttempt] = Field(default_factory=list)
    blockers: list[BlockerSignal] = Field(default_factory=list)
    suggested_next_steps: list[ProactiveSuggestion] = Field(default_factory=list, max_length=3)
    resurrection: AgentResurrectionContext = Field(default_factory=AgentResurrectionContext)
    withheld_context: list[WithheldContext] = Field(default_factory=list)
    withheld: list[WithheldContext] = Field(default_factory=list)
    agent_limitations: list[str] = Field(default_factory=list)
    context_quality_notes: list[str] = Field(default_factory=list)
    policy_decision: PolicySummary
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
