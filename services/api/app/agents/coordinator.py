from audit_core import AuditEventType

from app.agents.data_sensitivity import generate_data_sensitivity_report
from app.agents.workflow_mapper import generate_workflow_map
from app.services.audit_service import log_audit_event


_COORDINATOR_NAME = "coordinator"


def run_initial_analysis(run_id: str, workflow_id: str) -> list[dict]:
    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_started,
        actor=_COORDINATOR_NAME,
        details={
            "workflow_id": workflow_id,
            "phase": "initial_analysis",
        },
    )

    workflow_map_artifact = generate_workflow_map(
        run_id=run_id,
        workflow_id=workflow_id,
    )

    data_sensitivity_artifact = generate_data_sensitivity_report(
        run_id=run_id,
        workflow_id=workflow_id,
    )

    artifacts = [
        workflow_map_artifact,
        data_sensitivity_artifact,
    ]

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_completed,
        actor=_COORDINATOR_NAME,
        details={
            "workflow_id": workflow_id,
            "phase": "initial_analysis",
            "artifacts_created": [
                artifact["artifact_id"] for artifact in artifacts
            ],
        },
    )

    return artifacts