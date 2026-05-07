from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    step_index: int
    step_type: str
    status: StepStatus
    output: str = ""
    error: str = ""
    started_at: datetime | None = None
    ended_at: datetime | None = None


class CommandStep(BaseModel):
    type: Literal["command"] = "command"
    name: str
    args: list[str] = Field(default_factory=list)
    description: str = ""
    timeout_seconds: int = 60


class ShellStep(BaseModel):
    type: Literal["shell"] = "shell"
    run: str
    description: str = ""
    timeout_seconds: int = 60
    working_dir: str | None = None


class GateStep(BaseModel):
    type: Literal["gate"] = "gate"
    message: str
    description: str = ""


StepDefinition = Annotated[
    CommandStep | ShellStep | GateStep,
    Field(discriminator="type"),
]


class WorkflowDefinition(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0"
    steps: list[StepDefinition] = Field(default_factory=list)


class RunState(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_name: str
    status: RunStatus = RunStatus.RUNNING
    current_step_index: int = 0
    step_results: list[StepResult] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def is_terminal(self) -> bool:
        return self.status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.ABORTED}
