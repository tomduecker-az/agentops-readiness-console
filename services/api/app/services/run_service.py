from uuid import uuid4

from audit_core import AuditEventType

from app.agents.coordinator import run_initial_analysis
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

    artifacts = run_initial_analysis(
        run_id=run_id,
        workflow_id=workflow.workflow_id,
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.run_completed,
        actor="system",
        details={
            "workflow_id": workflow.workflow_id,
            "artifact_count": len(artifacts),
        },
    )

    return WorkflowRunResponse(
        run_id=run_id,
        workflow_id=workflow.workflow_id,
        status="created",
        message="Workflow run created and governed workflow design artifacts generated.",
    )