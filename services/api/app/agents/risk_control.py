from typing import Any

from audit_core import AuditEventType

from app.mcp_clients.policy_gateway import get_required_controls
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact, get_artifacts_for_run
from app.services.audit_service import log_audit_event


_AGENT_NAME = "risk_control_designer"


def generate_risk_control_matrix(run_id: str, workflow_id: str) -> dict[str, Any]:
    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_started,
        actor=_AGENT_NAME,
        details={"workflow_id": workflow_id},
    )

    workflow_map = _get_artifact_content(
        run_id=run_id,
        artifact_type=ArtifactType.workflow_map,
    )

    data_sensitivity_report = _get_artifact_content(
        run_id=run_id,
        artifact_type=ArtifactType.data_sensitivity_report,
    )

    workflow_steps = workflow_map.get("steps", [])
    sensitivity_summary = data_sensitivity_report.get("summary", {})

    matrix_rows = []

    for step in workflow_steps:
        identified_risks = _identify_step_risks(
            step=step,
            sensitivity_summary=sensitivity_summary,
        )

        control_groups = []

        for risk in identified_risks:
            controls_result = get_required_controls(
                run_id=run_id,
                agent_name=_AGENT_NAME,
                workflow_step=risk["control_lookup_key"],
            )

            control_groups.append(
                {
                    "risk_id": risk["risk_id"],
                    "control_lookup_key": risk["control_lookup_key"],
                    "controls": [
                        control.model_dump(mode="json")
                        for control in controls_result.controls
                    ],
                }
            )

        matrix_rows.append(
            {
                "step_id": step.get("step_id"),
                "sequence": step.get("sequence"),
                "description": step.get("description"),
                "actor": step.get("actor"),
                "decision_point": step.get("decision_point", False),
                "identified_risks": identified_risks,
                "required_control_groups": control_groups,
            }
        )

    content = {
        "workflow_id": workflow_id,
        "title": "Risk / Control Matrix",
        "source_artifacts": {
            "workflow_map": workflow_map.get("title"),
            "data_sensitivity_report": data_sensitivity_report.get("title"),
        },
        "matrix_rows": matrix_rows,
        "summary": _build_summary(matrix_rows),
        "generation_mode": "deterministic_skeleton",
    }

    artifact = create_artifact(
        run_id=run_id,
        artifact_type=ArtifactType.risk_control_matrix,
        content=content,
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_completed,
        actor=_AGENT_NAME,
        details={
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type.value,
            "row_count": len(matrix_rows),
            "risk_count": content["summary"]["risk_count"],
        },
    )

    return artifact.model_dump(mode="json")


def _get_artifact_content(
    run_id: str,
    artifact_type: ArtifactType,
) -> dict[str, Any]:
    artifacts = get_artifacts_for_run(run_id)

    for artifact in artifacts:
        if artifact.artifact_type == artifact_type:
            return artifact.content

    raise ValueError(
        f"Required artifact '{artifact_type.value}' was not found for run '{run_id}'."
    )


def _identify_step_risks(
    step: dict[str, Any],
    sensitivity_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    description = str(step.get("description", "")).lower()
    risks: list[dict[str, Any]] = []

    if step.get("decision_point"):
        risks.append(
            {
                "risk_id": "RISK-DECISION-001",
                "risk_name": "Decision logic may be applied inconsistently",
                "risk_description": "Decision points require clear criteria, traceability, and review expectations.",
                "severity": "medium",
                "control_lookup_key": "financial_status_adjustment",
            }
        )

    if "approval" in description or "supervisor" in description:
        risks.append(
            {
                "risk_id": "RISK-APPROVAL-001",
                "risk_name": "Approval requirement may be bypassed",
                "risk_description": "Items requiring approval must not be auto-closed or advanced without supervisor review.",
                "severity": "high",
                "control_lookup_key": "financial_status_adjustment",
            }
        )

    if "source system" in description or "source-system" in description:
        risks.append(
            {
                "risk_id": "RISK-SOURCE-001",
                "risk_name": "Missing source-system identifier",
                "risk_description": "Records missing source-system identifiers cannot be safely auto-resolved.",
                "severity": "high",
                "control_lookup_key": "missing_source_identifier",
            }
        )

    if "status" in description or "resolution" in description or "update" in description:
        risks.append(
            {
                "risk_id": "RISK-WRITE-001",
                "risk_name": "Financial or operational status may be changed without control",
                "risk_description": "Status-changing actions require audit logging and appropriate human approval.",
                "severity": "high",
                "control_lookup_key": "financial_status_adjustment",
            }
        )

    blocked_fields = sensitivity_summary.get("blocked_from_model_context", [])
    redaction_fields = sensitivity_summary.get("requires_redaction", [])

    if blocked_fields or redaction_fields:
        risks.append(
            {
                "risk_id": "RISK-DATA-001",
                "risk_name": "Sensitive data may enter model context",
                "risk_description": "Fields requiring redaction or blocked from model context must be controlled before LLM use.",
                "severity": "high",
                "control_lookup_key": "implementation_backlog_write",
                "affected_fields": {
                    "blocked_from_model_context": blocked_fields,
                    "requires_redaction": redaction_fields,
                },
            }
        )

    return _deduplicate_risks(risks)


def _deduplicate_risks(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique_risks: list[dict[str, Any]] = []

    for risk in risks:
        risk_id = risk["risk_id"]

        if risk_id in seen:
            continue

        seen.add(risk_id)
        unique_risks.append(risk)

    return unique_risks


def _build_summary(matrix_rows: list[dict[str, Any]]) -> dict[str, Any]:
    risk_count = 0
    high_severity_count = 0
    control_count = 0

    for row in matrix_rows:
        risks = row.get("identified_risks", [])
        risk_count += len(risks)

        high_severity_count += sum(
            1 for risk in risks if risk.get("severity") == "high"
        )

        for control_group in row.get("required_control_groups", []):
            control_count += len(control_group.get("controls", []))

    return {
        "row_count": len(matrix_rows),
        "risk_count": risk_count,
        "high_severity_risk_count": high_severity_count,
        "control_count": control_count,
    }