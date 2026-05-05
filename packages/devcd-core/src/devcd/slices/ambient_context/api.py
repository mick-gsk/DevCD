from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException, Request, Response

from devcd.slices.ambient_context.models import (
    AgentContextSurface,
    ContextBrief,
    ContextControlReport,
    ContextMemoryItem,
    DetailLevel,
    MemoryCorrection,
    ProactiveSuggestion,
    SurfaceKind,
    WorkState,
)
from devcd.slices.ambient_context.service import AmbientContextService
from devcd.slices.memory_layer.models import MemoryScope

router = APIRouter(prefix="/context", tags=["ambient-context"])


def ambient_context_service(request: Request) -> AmbientContextService:
    return cast(AmbientContextService, request.app.state.ambient_context_service)


@router.get("/work-state", response_model=WorkState)
def get_work_state(request: Request) -> WorkState:
    return ambient_context_service(request).get_work_state()


@router.post("/brief", response_model=ContextBrief)
def create_context_brief(
    request: Request,
    surface: AgentContextSurface | None = None,
) -> ContextBrief:
    return ambient_context_service(request).create_context_brief(surface)


@router.get("/control-plane", response_model=ContextControlReport)
def get_context_control_plane(
    request: Request,
    surface: SurfaceKind = SurfaceKind.CODING_AGENT,
    pack: str = "developer",
    detail: DetailLevel = DetailLevel.STANDARD,
) -> ContextControlReport:
    try:
        return ambient_context_service(request).create_context_control_report(
            AgentContextSurface(kind=surface, name="devcd-api-control", detail_level=detail),
            context_pack=pack,
        )
    except KeyError as error:
        raise HTTPException(status_code=422, detail=f"invalid context pack: {pack}") from error


@router.post("/suggestions/{suggestion_id}/dismiss", response_model=ProactiveSuggestion)
def dismiss_suggestion(suggestion_id: str, request: Request) -> ProactiveSuggestion:
    try:
        return ambient_context_service(request).dismiss_suggestion(suggestion_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="suggestion not found") from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.get("/memory", response_model=list[ContextMemoryItem])
def list_context_memory(
    request: Request,
    scope: MemoryScope | None = None,
) -> list[ContextMemoryItem]:
    return ambient_context_service(request).list_context_memory(scope)


@router.patch("/memory/{item_id}", response_model=ContextMemoryItem)
def correct_context_memory_item(
    item_id: str,
    correction: MemoryCorrection,
    request: Request,
) -> ContextMemoryItem:
    try:
        return ambient_context_service(request).correct_context_memory_item(item_id, correction)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="context memory item not found") from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.delete("/memory/{item_id}", status_code=204)
def delete_context_memory_item(item_id: str, request: Request) -> Response:
    try:
        ambient_context_service(request).delete_context_memory_item(item_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="context memory item not found") from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return Response(status_code=204)
