from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class ScoutTaskKind(StrEnum):
    IDENTIFY_CURRENT_GOAL = "identify_current_goal"
    FIND_RELEVANT_ARTIFACTS = "find_relevant_artifacts"
    SUMMARIZE_BLOCKERS = "summarize_blockers"
    PROPOSE_NEXT_ACTION = "propose_next_action"


class ScoutRunStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    INVALID_REPORT = "invalid_report"
    OUTPUT_LIMIT_EXCEEDED = "output_limit_exceeded"


class RunnerCommandTemplate(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    command: str = Field(min_length=1, max_length=240)
    args: list[str] = Field(default_factory=list, max_length=40)
    enabled: bool = True
    description: str = Field(default="", max_length=240)

    @field_validator("command")
    @classmethod
    def command_must_be_plain_executable(cls, value: str) -> str:
        _reject_shell_control(value)
        if _command_basename(value) in _SHELL_EXECUTABLES:
            raise ValueError("runner command templates must not invoke shell interpreters")
        return value

    @field_validator("args")
    @classmethod
    def args_must_not_contain_shell_control(cls, value: list[str]) -> list[str]:
        for argument in value:
            _reject_shell_control(argument)
            if argument.lower() in _SHELL_EXECUTION_FLAGS:
                raise ValueError("runner command templates must not include shell execution flags")
        return value


class ScoutEvidence(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=500)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    policy_reason: str = Field(min_length=1, max_length=500)
    reference: str | None = Field(default=None, max_length=300)


class ScoutTask(BaseModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    kind: ScoutTaskKind
    prompt: str = Field(min_length=1, max_length=1200)
    surface: str = Field(min_length=1, max_length=80)
    context_pack: str = Field(min_length=1, max_length=80)
    expected_evidence: list[str] = Field(default_factory=list, max_length=12)
    policy_decision_id: str = Field(min_length=1, max_length=120)
    data_class: str = "metadata"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None

    @field_validator("data_class")
    @classmethod
    def data_class_must_be_metadata(cls, value: str) -> str:
        if value != "metadata":
            raise ValueError("scout tasks may request metadata context only")
        return value

    @model_validator(mode="after")
    def default_expiration(self) -> ScoutTask:
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(minutes=15)
        if self.expires_at <= self.created_at:
            raise ValueError("scout task expiration must be after creation")
        return self


class ScoutReport(BaseModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    task_id: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=1200)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[ScoutEvidence] = Field(min_length=1, max_length=20)
    next_action: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data_class: str = "metadata"

    @field_validator("data_class")
    @classmethod
    def report_data_class_must_be_metadata(cls, value: str) -> str:
        if value != "metadata":
            raise ValueError("scout reports may store metadata summaries only")
        return value


class ScoutRunResult(BaseModel):
    runner_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    status: ScoutRunStatus
    report: ScoutReport | None = None
    error_summary: str | None = Field(default=None, max_length=500)
    raw_output_stored: bool = False


class ActionPacket(BaseModel):
    schema_version: str = "1.0"
    current_goal: str | None = Field(default=None, max_length=1200)
    next_action: str | None = Field(default=None, max_length=500)
    recommended_agent_mode: str = Field(default="continuation", max_length=80)
    evidence: list[ScoutEvidence] = Field(default_factory=list, max_length=30)
    policy_summary: str | None = Field(default=None, max_length=1000)
    ready_for_agent: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def derive_ready_for_agent(self) -> ActionPacket:
        self.ready_for_agent = bool(self.current_goal and self.next_action)
        return self


def _reject_shell_control(value: str) -> None:
    shell_control_characters = set(";|&$`<>")
    if any(character in shell_control_characters for character in value):
        raise ValueError("runner command templates must not include shell control characters")


def _command_basename(value: str) -> str:
    return value.replace("\\", "/").rsplit("/", maxsplit=1)[-1].lower()


_SHELL_EXECUTABLES = {
    "bash",
    "bash.exe",
    "cmd",
    "cmd.exe",
    "dash",
    "dash.exe",
    "powershell",
    "powershell.exe",
    "pwsh",
    "pwsh.exe",
    "sh",
    "sh.exe",
}
_SHELL_EXECUTION_FLAGS = {"-c", "/c", "-command", "-encodedcommand"}