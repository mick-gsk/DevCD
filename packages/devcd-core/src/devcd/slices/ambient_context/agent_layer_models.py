from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class AgentTarget(StrEnum):
    COPILOT = "copilot"
    CLAUDE = "claude"
    CODEX = "codex"
    OPENCLAW = "openclaw"


class AgentDetectionStatus(StrEnum):
    DETECTED = "detected"
    AVAILABLE = "available"
    MISSING = "missing"


class AgentLayerArchetype(StrEnum):
    BUILDER = "builder"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    ORCHESTRATOR = "orchestrator"


class WorkspaceToolKind(StrEnum):
    LANGUAGE = "language"
    TEST = "test"
    BUILD = "build"
    LINT = "lint"
    MCP = "mcp"
    CI = "ci"
    DEVCD = "devcd"


class DetectedAgentTarget(BaseModel):
    target: AgentTarget
    display_name: str = Field(min_length=1, max_length=80)
    status: AgentDetectionStatus
    path: str = Field(min_length=1, max_length=260)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=240)


class DetectedWorkspaceTool(BaseModel):
    kind: WorkspaceToolKind
    name: str = Field(min_length=1, max_length=80)
    path: str = Field(min_length=1, max_length=260)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=240)


class WorkspaceDetectionResult(BaseModel):
    workspace_root: str = Field(min_length=1)
    agents: list[DetectedAgentTarget] = Field(default_factory=list)
    languages: list[DetectedWorkspaceTool] = Field(default_factory=list)
    test_tools: list[DetectedWorkspaceTool] = Field(default_factory=list)
    build_tools: list[DetectedWorkspaceTool] = Field(default_factory=list)
    lint_tools: list[DetectedWorkspaceTool] = Field(default_factory=list)
    mcp_hints: list[DetectedWorkspaceTool] = Field(default_factory=list)
    ci_hints: list[DetectedWorkspaceTool] = Field(default_factory=list)
    devcd_state: dict[str, bool | int | str | None] = Field(default_factory=dict)
    policy_receipts: list[str] = Field(default_factory=list)
    workspace_fingerprint: str = Field(default="unknown", min_length=1, max_length=500)


class AgentLayerArchetypeDefinition(BaseModel):
    id: AgentLayerArchetype
    display_name: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=240)
    primary_surface: str = Field(min_length=1, max_length=80)
    secondary_surfaces: list[str] = Field(default_factory=list, max_length=6)
    context_pack: str = Field(min_length=1, max_length=80)
    recommended_when: list[str] = Field(default_factory=list, max_length=8)
    default_agent_targets: list[AgentTarget] = Field(default_factory=list, max_length=4)

    @property
    def surface_plan(self) -> list[str]:
        return [self.primary_surface, *self.secondary_surfaces]


class AgentLayerWritePreview(BaseModel):
    path: str = Field(min_length=1, max_length=260)
    status: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=240)


class AgentLayerProposal(BaseModel):
    recommended_archetype: AgentLayerArchetype
    alternatives: list[AgentLayerArchetype] = Field(default_factory=list, max_length=3)
    agent_targets: list[AgentTarget] = Field(default_factory=list, max_length=4)
    context_pack: str = Field(min_length=1, max_length=80)
    surface_plan: list[str] = Field(min_length=1, max_length=6)
    writes: list[AgentLayerWritePreview] = Field(default_factory=list, max_length=8)
    next_commands: list[str] = Field(default_factory=list, max_length=8)
    trust_receipts: list[str] = Field(default_factory=list, max_length=12)
    confidence: float = Field(ge=0.0, le=1.0)
    detection_summary: list[str] = Field(default_factory=list, max_length=12)
    workspace_fingerprint: str = Field(default="unknown", min_length=1, max_length=500)


class AgentLayerProfile(BaseModel):
    schema_version: str = "1.0"
    profile_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=120)
    archetype: AgentLayerArchetype
    agent_targets: list[AgentTarget] = Field(min_length=1, max_length=4)
    context_pack: str = Field(min_length=1, max_length=80)
    surface_plan: list[str] = Field(min_length=1, max_length=6)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    workspace_fingerprint: str = Field(min_length=1, max_length=500)
    policy_reason: str = Field(min_length=1, max_length=500)
    detection_summary: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("detection_summary")
    @classmethod
    def detection_summary_must_be_metadata(cls, value: list[str]) -> list[str]:
        sensitive_markers = ("secret", "token=", "password", "raw log", "private key")
        for item in value:
            lowered = item.lower()
            if any(marker in lowered for marker in sensitive_markers):
                raise ValueError("agent layer profiles may store metadata summaries only")
        return value


class AgentLayerApplyResult(BaseModel):
    profile: AgentLayerProfile
    profile_path: str = Field(min_length=1, max_length=260)
    writes: list[AgentLayerWritePreview] = Field(default_factory=list, max_length=8)
    trust_receipts: list[str] = Field(default_factory=list, max_length=12)
    next_commands: list[str] = Field(default_factory=list, max_length=8)


class AgentLayerProfileLoadResult(BaseModel):
    status: str = Field(min_length=1, max_length=80)
    profile: AgentLayerProfile | None = None
    path: str = Field(min_length=1, max_length=260)
    next_step: str = Field(min_length=1, max_length=160)
