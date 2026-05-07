from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from devcd.slices.workflow_layer.catalog import CatalogEntry, WorkflowCatalog
from devcd.slices.workflow_layer.models import WorkflowDefinition

router = APIRouter(prefix="/workflow", tags=["workflow-layer"])


class WorkflowCatalogEntryResponse(BaseModel):
    name: str
    source_tier: str
    install_allowed: bool


def workflow_catalog(request: Request) -> WorkflowCatalog:
    return cast(WorkflowCatalog, request.app.state.workflow_catalog)


@router.get("/catalog", response_model=list[WorkflowCatalogEntryResponse])
def list_workflow_catalog(request: Request) -> list[WorkflowCatalogEntryResponse]:
    entries: list[CatalogEntry] = workflow_catalog(request).list_available()
    return [
        WorkflowCatalogEntryResponse(
            name=entry.name,
            source_tier=entry.source_tier.value,
            install_allowed=entry.install_allowed,
        )
        for entry in entries
    ]


@router.get("/catalog/{name}", response_model=WorkflowDefinition)
def get_workflow_catalog_entry(name: str, request: Request) -> WorkflowDefinition:
    definition = workflow_catalog(request).resolve(name)
    if definition is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    return definition
