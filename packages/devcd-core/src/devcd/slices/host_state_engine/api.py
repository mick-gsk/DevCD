from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from devcd.slices.events.models import DevEvent
from devcd.slices.host_state_engine.models import DevState
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.models import MemoryEntry, MemoryScope
from devcd.slices.policy_layer.models import PolicyDecision

router = APIRouter()


def _state_engine(request: Request) -> StateEngine:
    return cast(StateEngine, request.app.state.state_engine)


@router.get("/state", response_model=DevState)
def get_state(request: Request) -> DevState:
    return _state_engine(request).state


@router.post("/event", response_model=PolicyDecision)
def post_event(event: DevEvent, request: Request) -> PolicyDecision:
    return _state_engine(request).accept_event(event)


@router.get("/memory/{scope}", response_model=list[MemoryEntry])
def get_memory(scope: MemoryScope, request: Request) -> list[MemoryEntry]:
    state_engine = _state_engine(request)
    return state_engine.memory_store.list_by_scope(scope, state_engine.is_source_visible)
