from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from devcd.slices.agentic_context.models import ActionPacket, ScoutReport, ScoutTask
from devcd.slices.agentic_context.service import AgenticContextService
from devcd.slices.policy_layer.models import PolicyDecision

router = APIRouter(prefix="/agentic-context", tags=["agentic-context"])


class AgenticRunRequest(BaseModel):
    runner_id: str = Field(min_length=1)
    task_kind: str = Field(min_length=1)


def agentic_context_service(request: Request) -> AgenticContextService:
    return cast(AgenticContextService, request.app.state.agentic_context_service)


@router.get("/tasks", response_model=list[ScoutTask])
def list_scout_tasks(
    request: Request,
    surface: str = "coding-agent",
    pack: str = "developer",
) -> list[ScoutTask]:
    try:
        return agentic_context_service(request).create_scout_tasks(
            surface=surface,
            context_pack=pack,
        )
    except ValueError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.get("/action-packet", response_model=ActionPacket)
def get_action_packet(
    request: Request,
    surface: str = "coding-agent",
    pack: str = "developer",
) -> ActionPacket:
    return agentic_context_service(request).create_action_packet(
        surface=surface,
        context_pack=pack,
    )


@router.post("/reports", response_model=ScoutReport)
def accept_scout_report(report: ScoutReport, request: Request) -> ScoutReport:
    try:
        return agentic_context_service(request).accept_scout_report(report)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/runs", response_model=PolicyDecision)
def start_scout_run(run: AgenticRunRequest, request: Request, response: Response) -> PolicyDecision:
    service = agentic_context_service(request)
    decision = service.policy_engine.decide_agentic_runner_start(run.runner_id, run.task_kind)
    if not decision.allowed:
        response.status_code = 403
    return decision