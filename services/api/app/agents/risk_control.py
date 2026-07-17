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
        workflow_context = _infer_workflow_context(workflow_steps)

        identified_risks = _identify_step_risks(
            step=step,
            sensitivity_summary=sensitivity_summary,
            workflow_context=workflow_context,
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
    workflow_context: str,
) -> list[dict[str, Any]]:
    description = str(step.get("description", "")).lower()
    risks: list[dict[str, Any]] = []

    if step.get("decision_point"):
        risks.append(
            {
                "risk_id": "RISK-DECISION-001",
                "risk_name": "Workflow decision may be applied inconsistently",
                "risk_description": "Decision points require clear criteria, traceability, and review expectations.",
                "severity": "medium",
                "control_lookup_key": _decision_control_key(workflow_context),
            }
        )

    if _requires_governed_approval(description):
        risks.append(
            {
                "risk_id": "RISK-APPROVAL-001",
                "risk_name": "Governed approval requirement may be bypassed",
                "risk_description": _approval_risk_description(workflow_context),
                "severity": "high",
                "control_lookup_key": _decision_control_key(workflow_context),
            }
        )

    if _has_source_or_intake_quality_risk(description):
        risks.append(
            {
                "risk_id": "RISK-SOURCE-001",
                "risk_name": _source_risk_name(workflow_context),
                "risk_description": _source_risk_description(workflow_context),
                "severity": "high",
                "control_lookup_key": _source_control_key(workflow_context),
            }
        )

    if _has_write_action_risk(description):
        risks.append(
            {
                "risk_id": "RISK-WRITE-001",
                "risk_name": "Operational write action may occur without control",
                "risk_description": (
                    "Workflow state changes, assignments, external language, or system-of-record "
                    "updates require approval and auditability."
                ),
                "severity": "high",
                "control_lookup_key": "operational_write_action",
            }
        )

    if workflow_context == "customer_onboarding":
        risks.extend(_identify_customer_onboarding_risks(description))

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


def _infer_workflow_context(workflow_steps: list[dict[str, Any]]) -> str:
    combined_text = " ".join(
        str(step.get("description", "")) for step in workflow_steps
    ).lower()

    if _contains_any(
        combined_text,
        [
            "customer onboarding",
            "onboarding",
            "customer-facing",
            "kickoff",
            "implementation plan",
            "implementation specialist",
            "requested integrations",
            "account executive",
            "customer success",
        ],
    ):
        return "customer_onboarding"

    if _contains_any(
        combined_text,
        [
            "payment",
            "reconciliation",
            "exception",
            "source system",
            "source-system",
            "supervisor approval",
            "resolution",
        ],
    ):
        return "financial_operations"

    return "general_operations"


def _identify_customer_onboarding_risks(description: str) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []

    if _contains_any(
        description,
        [
            "customer-facing",
            "shared with the customer",
            "sent externally",
            "commitment",
            "commitments",
        ],
    ):
        risks.append(
            {
                "risk_id": "RISK-COMMITMENT-001",
                "risk_name": "Customer-facing commitment may be made without review",
                "risk_description": (
                    "Customer-facing timelines, scope, or commitments should not be finalized "
                    "from agent output without authorized review."
                ),
                "severity": "high",
                "control_lookup_key": "customer_facing_commitment",
            }
        )

    if _contains_any(
        description,
        [
            "implementation scope",
            "custom integration",
            "custom integrations",
            "enterprise terms",
            "onboarding plan is finalized",
            "onboarding plan",
        ],
    ):
        risks.append(
            {
                "risk_id": "RISK-SCOPE-001",
                "risk_name": "Implementation scope may change without approval",
                "risk_description": (
                    "Scope, enterprise terms, or custom implementation requirements must be reviewed "
                    "before the onboarding plan is finalized."
                ),
                "severity": "high",
                "control_lookup_key": "implementation_scope_change",
            }
        )

    if _contains_any(
        description,
        [
            "sensitive data",
            "requested integrations",
            "technical requirements",
            "sso",
            "secure file transfer",
            "integration",
            "integrations",
        ],
    ):
        risks.append(
            {
                "risk_id": "RISK-INTEGRATION-001",
                "risk_name": "Sensitive integration or security requirement may be mishandled",
                "risk_description": (
                    "Sensitive data, custom integrations, SSO, or security-related requirements "
                    "need technical review before planning or execution."
                ),
                "severity": "high",
                "control_lookup_key": "sensitive_integration_review",
            }
        )

    if _contains_any(
        description,
        [
            "handoff",
            "intake",
            "missing",
            "unclear",
            "routed back",
            "required intake",
        ],
    ):
        risks.append(
            {
                "risk_id": "RISK-HANDOFF-001",
                "risk_name": "Incomplete intake or handoff may lead to incorrect planning",
                "risk_description": (
                    "Missing or unclear handoff information can cause incorrect plans, missed dependencies, "
                    "or premature customer communication."
                ),
                "severity": "medium",
                "control_lookup_key": "intake_handoff_quality",
            }
        )

    if _contains_any(
        description,
        [
            "accelerated",
            "compressed",
            "launch timeline",
            "launch timelines",
            "timeline",
        ],
    ):
        risks.append(
            {
                "risk_id": "RISK-TIMELINE-001",
                "risk_name": "Compressed timeline may create delivery or commitment risk",
                "risk_description": (
                    "Accelerated or compressed timelines require review before capacity, dates, "
                    "or delivery commitments are shared externally."
                ),
                "severity": "medium",
                "control_lookup_key": "accelerated_timeline_review",
            }
        )

    return risks


def _requires_governed_approval(description: str) -> bool:
    return _contains_any(
        description,
        [
            "approval",
            "approve",
            "approves",
            "supervisor",
            "review",
            "sensitive data",
            "custom integration",
            "enterprise terms",
            "customer-facing",
            "sent externally",
            "shared with the customer",
            "commitment",
            "finalized",
        ],
    )


def _has_source_or_intake_quality_risk(description: str) -> bool:
    return _contains_any(
        description,
        [
            "source system",
            "source-system",
            "source record",
            "missing",
            "unclear",
            "intake",
            "handoff",
            "required fields",
        ],
    )


def _has_write_action_risk(description: str) -> bool:
    return _contains_any(
        description,
        [
            "status",
            "resolution",
            "update",
            "assigns",
            "assigned",
            "schedule",
            "schedules",
            "sent externally",
            "shared with the customer",
            "customer-facing",
            "commitment",
            "commitments",
            "finalized",
        ],
    )


def _decision_control_key(workflow_context: str) -> str:
    if workflow_context == "financial_operations":
        return "financial_status_adjustment"

    return "governed_workflow_decision"


def _source_control_key(workflow_context: str) -> str:
    if workflow_context == "financial_operations":
        return "missing_source_identifier"

    return "source_record_validation"


def _approval_risk_description(workflow_context: str) -> str:
    if workflow_context == "customer_onboarding":
        return (
            "Onboarding plans involving sensitive data, custom integrations, enterprise terms, "
            "customer-facing commitments, or supervisor review must not advance without approval."
        )

    return (
        "Items requiring approval must not advance, finalize, or trigger external communication "
        "without authorized review."
    )


def _source_risk_name(workflow_context: str) -> str:
    if workflow_context == "customer_onboarding":
        return "Missing or unclear onboarding intake information"

    if workflow_context == "financial_operations":
        return "Missing source-system identifier"

    return "Missing or conflicting source information"


def _source_risk_description(workflow_context: str) -> str:
    if workflow_context == "customer_onboarding":
        return (
            "Onboarding plans should not be finalized when intake fields, contract context, "
            "integration details, or handoff information are missing or unclear."
        )

    if workflow_context == "financial_operations":
        return "Records missing source-system identifiers cannot be safely auto-resolved."

    return "Workflow items should not be finalized when required source information is missing or conflicting."


def _contains_any(value: str, terms: list[str]) -> bool:
    return any(term in value for term in terms)


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