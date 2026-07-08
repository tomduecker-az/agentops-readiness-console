from uuid import uuid4

from app.schemas.audit import AuditEventType
from app.schemas.runs import WorkflowRunRequest, WorkflowRunResponse
from app.services.audit_service import log_audit_event
from app.services.workflow_registry import get_registered_workflow


def create_workflow_run(request: WorkflowRunRequest) -> WorkflowRunResponse:
    workflow = get_registered_workflow(request.workflow_id)

    run_id = f"run_{uuid4().hex}"

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.run_started,
        actor="system",
        details={
            "workflow_id": workflow.workflow_id,
            "workflow_display_name": workflow.display_name,
            "packet_path": workflow.packet_path,
        },
    )

    return WorkflowRunResponse(
        run_id=run_id,
        workflow_id=workflow.workflow_id,
        status="created",
        message="Workflow run created.",
    )