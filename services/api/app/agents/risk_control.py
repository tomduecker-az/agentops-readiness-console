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
            _risk(
                risk_id="RISK-DECISION-001",
                risk_name="Workflow decision may be applied inconsistently",
                risk_description="Decision points require clear criteria, traceability, and review expectations.",
                severity="medium",
                control_lookup_key="governed_workflow_decision",
                description=description,
            )
        )

    if _matches(description, _APPROVAL_TERMS):
        risks.append(
            _risk(
                risk_id="RISK-APPROVAL-001",
                risk_name="Required approval may be bypassed",
                risk_description=(
                    "Workflow items that meet approval, review, or authorization conditions "
                    "must not advance without a recorded human decision."
                ),
                severity="high",
                control_lookup_key="governed_workflow_decision",
                description=description,
            )
        )

    if _matches(description, _SOURCE_OR_INTAKE_QUALITY_TERMS):
        risks.append(
            _risk(
                risk_id="RISK-SOURCE-001",
                risk_name="Required source or intake information may be missing",
                risk_description=(
                    "Workflow items should not be finalized when required source, intake, "
                    "handoff, or reference information is missing, unclear, ambiguous, or conflicting."
                ),
                severity="high",
                control_lookup_key="source_record_validation",
                description=description,
            )
        )

    if _matches(description, _WRITE_ACTION_TERMS):
        risks.append(
            _risk(
                risk_id="RISK-WRITE-001",
                risk_name="Operational write action may occur without control",
                risk_description=(
                    "Workflow state changes, assignments, external language, or system-of-record "
                    "updates require approval and auditability."
                ),
                severity="high",
                control_lookup_key="operational_write_action",
                description=description,
            )
        )

    if _matches(description, _EXTERNAL_COMMITMENT_TERMS):
        risks.append(
            _risk(
                risk_id="RISK-COMMITMENT-001",
                risk_name="External commitment or communication may be released without review",
                risk_description=(
                    "External communications, timelines, scope statements, or commitments "
                    "should not be finalized from agent output without authorized review."
                ),
                severity="high",
                control_lookup_key="external_commitment_review",
                description=description,
            )
        )

    if _matches(description, _SCOPE_CHANGE_TERMS):
        risks.append(
            _risk(
                risk_id="RISK-SCOPE-001",
                risk_name="Scope, requirement, or commitment boundary may change without approval",
                risk_description=(
                    "Scope, requirements, terms, or implementation expectations must be reviewed "
                    "before the workflow item is finalized or communicated externally."
                ),
                severity="high",
                control_lookup_key="scope_change_review",
                description=description,
            )
        )

    if _matches(description, _TECHNICAL_INTEGRATION_TERMS):
        risks.append(
            _risk(
                risk_id="RISK-INTEGRATION-001",
                risk_name="Technical, integration, or security requirement may be mishandled",
                risk_description=(
                    "Technical integrations, security-related requirements, credentials, APIs, "
                    "or system-access dependencies require appropriate technical or security review."
                ),
                severity="high",
                control_lookup_key="sensitive_integration_review",
                description=description,
            )
        )

    if _matches(description, _HANDOFF_TERMS):
        risks.append(
            _risk(
                risk_id="RISK-HANDOFF-001",
                risk_name="Incomplete handoff may lead to incorrect workflow execution",
                risk_description=(
                    "Missing, unclear, or incomplete handoff information can cause incorrect actions, "
                    "missed dependencies, or premature communication."
                ),
                severity="medium",
                control_lookup_key="intake_handoff_quality",
                description=description,
            )
        )

    if _matches(description, _TIMELINE_TERMS):
        risks.append(
            _risk(
                risk_id="RISK-TIMELINE-001",
                risk_name="Compressed timeline or SLA pressure may create execution risk",
                risk_description=(
                    "Accelerated timelines, deadlines, SLAs, or launch commitments require review "
                    "before capacity, dates, or delivery commitments are finalized."
                ),
                severity="medium",
                control_lookup_key="timeline_or_sla_review",
                description=description,
            )
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


_APPROVAL_TERMS = [
    "approval",
    "approve",
    "approved",
    "approves",
    "authorized",
    "authorization",
    "signoff",
    "sign-off",
    "review",
    "reviewed",
    "supervisor",
    "reject",
    "rejects",
    "rejected",
    "clarification",
]

_SOURCE_OR_INTAKE_QUALITY_TERMS = [
    "source system",
    "source-system",
    "source record",
    "record reference",
    "missing",
    "unclear",
    "ambiguous",
    "conflicting",
    "required field",
    "required fields",
    "intake",
    "handoff",
]

_WRITE_ACTION_TERMS = [
    "status",
    "resolution",
    "update",
    "updates",
    "assign",
    "assigns",
    "assigned",
    "schedule",
    "schedules",
    "scheduled",
    "send",
    "sent",
    "shared",
    "close",
    "closed",
    "advance",
    "advanced",
    "finalize",
    "finalized",
    "external",
    "system of record",
    "system-of-record",
]

_EXTERNAL_COMMITMENT_TERMS = [
    "customer-facing",
    "client-facing",
    "vendor-facing",
    "external",
    "sent externally",
    "shared with",
    "commitment",
    "commitments",
    "offer",
    "contract language",
    "timeline",
    "sla",
    "service level",
]

_SCOPE_CHANGE_TERMS = [
    "scope",
    "implementation scope",
    "custom",
    "custom integration",
    "custom integrations",
    "requirement",
    "requirements",
    "terms",
    "contract terms",
    "change request",
    "plan is finalized",
    "finalized",
]

_TECHNICAL_INTEGRATION_TERMS = [
    "integration",
    "integrations",
    "technical requirement",
    "technical requirements",
    "api",
    "sso",
    "secure file transfer",
    "data warehouse",
    "credential",
    "credentials",
    "security",
    "system access",
]

_HANDOFF_TERMS = [
    "handoff",
    "intake",
    "missing",
    "unclear",
    "routed back",
    "clarification",
    "required intake",
    "incomplete",
]

_TIMELINE_TERMS = [
    "accelerated",
    "compressed",
    "timeline",
    "timelines",
    "deadline",
    "due date",
    "launch",
    "launch date",
    "sla",
    "service level",
    "expedite",
    "expedited",
]


def _risk(
    risk_id: str,
    risk_name: str,
    risk_description: str,
    severity: str,
    control_lookup_key: str,
    description: str,
) -> dict[str, Any]:
    return {
        "risk_id": risk_id,
        "risk_name": risk_name,
        "risk_description": risk_description,
        "severity": severity,
        "control_lookup_key": control_lookup_key,
        "matched_terms": _matched_terms(description),
    }


def _matched_terms(description: str) -> list[str]:
    all_terms = (
        _APPROVAL_TERMS
        + _SOURCE_OR_INTAKE_QUALITY_TERMS
        + _WRITE_ACTION_TERMS
        + _EXTERNAL_COMMITMENT_TERMS
        + _SCOPE_CHANGE_TERMS
        + _TECHNICAL_INTEGRATION_TERMS
        + _HANDOFF_TERMS
        + _TIMELINE_TERMS
    )

    return sorted({term for term in all_terms if term in description})


def _matches(description: str, terms: list[str]) -> bool:
    return any(term in description for term in terms)


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