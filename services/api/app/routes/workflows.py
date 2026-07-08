from fastapi import APIRouter, HTTPException

from app.schemas.workflows import WorkflowDefinition
from app.services.workflow_registry import (
    WorkflowNotFoundError,
    WorkflowPacketInvalidError,
    get_registered_workflow,
    list_registered_workflows,
)

router = APIRouter()


@router.get("", response_model=list[WorkflowDefinition])
async def list_workflows() -> list[WorkflowDefinition]:
    return list_registered_workflows()


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str) -> WorkflowDefinition:
    try:
        return get_registered_workflow(workflow_id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkflowPacketInvalidError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc