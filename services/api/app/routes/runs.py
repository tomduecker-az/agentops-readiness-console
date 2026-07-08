from fastapi import APIRouter, HTTPException

from app.schemas.audit import AuditEvent
from app.schemas.runs import WorkflowRunRequest, WorkflowRunResponse
from app.services.audit_service import get_audit_events_for_run
from app.services.run_service import create_workflow_run
from app.services.workflow_registry import WorkflowNotFoundError, WorkflowPacketInvalidError

router = APIRouter()


@router.post("", response_model=WorkflowRunResponse)
async def create_run(request: WorkflowRunRequest) -> WorkflowRunResponse:
    try:
        return create_workflow_run(request)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkflowPacketInvalidError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{run_id}/audit", response_model=list[AuditEvent])
async def get_run_audit_events(run_id: str) -> list[AuditEvent]:
    return get_audit_events_for_run(run_id)