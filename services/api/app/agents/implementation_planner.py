from typing import Any

from audit_core import AuditEventType

from app.mcp_clients.policy_gateway import check_tool_permission
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact, get_artifacts_for_run
from app.services.audit_service import log_audit_event


_AGENT_NAME = "implementation_planner"


def generate_implementation_backlog(run_id: str, workflow_id: str) -> dict[str, Any]:
    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_started,
        actor=_AGENT_NAME,
        details={"workflow_id": workflow_id},
    )

    risk_control_matrix = _get_artifact_content(
        run_id=run_id,
        artifact_type=ArtifactType.risk_control_matrix,
    )

    hitl_design = _get_artifact_content(
        run_id=run_id,
        artifact_type=ArtifactType.hitl_design,
    )

    github_issue_permission = check_tool_permission(
        run_id=run_id,
        requesting_agent_name=_AGENT_NAME,
        target_tool_name="project_mgmt_server.create_issue",
        approval_granted=False,
    )

    backlog_items = _build_backlog_items(
        risk_control_matrix=risk_control_matrix,
        hitl_design=hitl_design,
        write_permission_decision=github_issue_permission.decision.value,
        requires_human_approval=github_issue_permission.requires_human_approval,
    )

    content = {
        "workflow_id": workflow_id,
        "title": "Implementation Backlog",
        "source_artifacts": {
            "risk_control_matrix": risk_control_matrix.get("title"),
            "hitl_design": hitl_design.get("title"),
        },
        "write_action_policy": {
            "target_tool_name": "project_mgmt_server.create_issue",
            "requesting_agent_name": _AGENT_NAME,
            "decision_without_approval": github_issue_permission.decision.value,
            "requires_human_approval": github_issue_permission.requires_human_approval,
            "rationale": github_issue_permission.rationale,
        },
        "backlog_items": backlog_items,
        "summary": _build_summary(backlog_items),
        "generation_mode": "deterministic_skeleton",
    }

    artifact = create_artifact(
        run_id=run_id,
        artifact_type=ArtifactType.implementation_backlog,
        content=content,
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_completed,
        actor=_AGENT_NAME,
        details={
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type.value,
            "backlog_item_count": len(backlog_items),
            "write_action_decision_without_approval": github_issue_permission.decision.value,
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


def _build_backlog_items(
    risk_control_matrix: dict[str, Any],
    hitl_design: dict[str, Any],
    write_permission_decision: str,
    requires_human_approval: bool,
) -> list[dict[str, Any]]:
    matrix_rows = risk_control_matrix.get("matrix_rows", [])
    approval_gates = hitl_design.get("approval_gates", [])
    review_queue_design = hitl_design.get("review_queue_design", [])
    escalation_rules = hitl_design.get("escalation_rules", [])

    items: list[dict[str, Any]] = []

    risk_ids = _collect_risk_ids(matrix_rows)
    control_ids = _collect_control_ids(matrix_rows)

    if "RISK-DATA-001" in risk_ids:
        items.append(
            _backlog_item(
                backlog_id="BACKLOG-DATA-001",
                title="Add sensitive-data redaction and model-context gate",
                description=(
                    "Prevent fields requiring redaction or blocked from model context "
                    "from being sent to the LLM without approved handling."
                ),
                priority="high",
                implementation_type="data_governance_control",
                recommended_owner="Data steward / AI platform owner",
                source_risk_ids=["RISK-DATA-001"],
                source_control_ids=_matching_controls(control_ids, ["CTRL-HITL-002", "CTRL-AUDIT-002"]),
                requires_human_approval=requires_human_approval,
                write_permission_decision=write_permission_decision,
            )
        )

    if "RISK-APPROVAL-001" in risk_ids:
        items.append(
            _backlog_item(
                backlog_id="BACKLOG-HITL-001",
                title="Add supervisor approval gate for threshold exceptions",
                description=(
                    "Require supervisor approval before exceptions above threshold "
                    "can be advanced, closed, or marked resolved."
                ),
                priority="high",
                implementation_type="workflow_approval_gate",
                recommended_owner="Operations / Process owner",
                source_risk_ids=["RISK-APPROVAL-001"],
                source_control_ids=_matching_controls(control_ids, ["CTRL-HITL-001", "CTRL-AUDIT-001"]),
                requires_human_approval=requires_human_approval,
                write_permission_decision=write_permission_decision,
            )
        )

    if "RISK-WRITE-001" in risk_ids:
        items.append(
            _backlog_item(
                backlog_id="BACKLOG-WRITE-001",
                title="Block write actions until approval is recorded",
                description=(
                    "Ensure financial or operational status updates remain draft-only "
                    "until an approved human decision is present."
                ),
                priority="high",
                implementation_type="write_action_guardrail",
                recommended_owner="Engineering / AI platform owner",
                source_risk_ids=["RISK-WRITE-001"],
                source_control_ids=_matching_controls(control_ids, ["CTRL-HITL-001", "CTRL-AUDIT-001"]),
                requires_human_approval=requires_human_approval,
                write_permission_decision=write_permission_decision,
            )
        )

    if "RISK-SOURCE-001" in risk_ids:
        items.append(
            _backlog_item(
                backlog_id="BACKLOG-SOURCE-001",
                title="Validate source-system identifiers before resolution",
                description=(
                    "Prevent auto-resolution or closure when source-system identifiers "
                    "are missing, ambiguous, or conflicting."
                ),
                priority="high",
                implementation_type="data_quality_validation",
                recommended_owner="Operations / Data owner",
                source_risk_ids=["RISK-SOURCE-001"],
                source_control_ids=_matching_controls(control_ids, ["CTRL-VALID-001"]),
                requires_human_approval=requires_human_approval,
                write_permission_decision=write_permission_decision,
            )
        )

    if review_queue_design:
        items.append(
            _backlog_item(
                backlog_id="BACKLOG-QUEUE-001",
                title="Create review queue for high-risk workflow steps",
                description=(
                    "Route high-risk exceptions to a review queue with required evidence, "
                    "recommended reviewer, and approval status."
                ),
                priority="medium",
                implementation_type="review_workflow",
                recommended_owner="Product / Operations",
                source_risk_ids=sorted(risk_ids),
                source_control_ids=sorted(control_ids),
                requires_human_approval=requires_human_approval,
                write_permission_decision=write_permission_decision,
                additional_context={
                    "review_queue_count": len(review_queue_design),
                },
            )
        )

    if escalation_rules:
        items.append(
            _backlog_item(
                backlog_id="BACKLOG-ESCALATION-001",
                title="Implement escalation rules for blocked or high-risk cases",
                description=(
                    "Escalate records that meet high-risk conditions such as missing "
                    "source identifiers or approval-threshold exceptions."
                ),
                priority="medium",
                implementation_type="escalation_rule",
                recommended_owner="Operations / Process owner",
                source_risk_ids=sorted(risk_ids),
                source_control_ids=sorted(control_ids),
                requires_human_approval=requires_human_approval,
                write_permission_decision=write_permission_decision,
                additional_context={
                    "escalation_rule_count": len(escalation_rules),
                },
            )
        )

    if approval_gates:
        items.append(
            _backlog_item(
                backlog_id="BACKLOG-AUDIT-001",
                title="Persist approval and write-action audit events",
                description=(
                    "Move audit records for approvals, policy checks, and write actions "
                    "from the MVP in-memory store to a durable append-only store."
                ),
                priority="medium",
                implementation_type="audit_persistence",
                recommended_owner="Engineering / Security",
                source_risk_ids=sorted(risk_ids),
                source_control_ids=sorted(control_ids),
                requires_human_approval=requires_human_approval,
                write_permission_decision=write_permission_decision,
            )
        )

    return items


def _backlog_item(
    backlog_id: str,
    title: str,
    description: str,
    priority: str,
    implementation_type: str,
    recommended_owner: str,
    source_risk_ids: list[str],
    source_control_ids: list[str],
    requires_human_approval: bool,
    write_permission_decision: str,
    additional_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "backlog_id": backlog_id,
        "title": title,
        "description": description,
        "priority": priority,
        "implementation_type": implementation_type,
        "recommended_owner": recommended_owner,
        "source_risk_ids": source_risk_ids,
        "source_control_ids": source_control_ids,
        "requires_human_approval_before_execution": requires_human_approval,
        "write_permission_decision_without_approval": write_permission_decision,
        "status": "proposed",
        "github_issue_created": False,
        "additional_context": additional_context or {},
    }


def _collect_risk_ids(matrix_rows: list[dict[str, Any]]) -> set[str]:
    risk_ids: set[str] = set()

    for row in matrix_rows:
        for risk in row.get("identified_risks", []):
            risk_id = risk.get("risk_id")

            if risk_id:
                risk_ids.add(risk_id)

    return risk_ids


def _collect_control_ids(matrix_rows: list[dict[str, Any]]) -> set[str]:
    control_ids: set[str] = set()

    for row in matrix_rows:
        for control_group in row.get("required_control_groups", []):
            for control in control_group.get("controls", []):
                control_id = control.get("control_id")

                if control_id:
                    control_ids.add(control_id)

    return control_ids


def _matching_controls(
    control_ids: set[str],
    desired_control_ids: list[str],
) -> list[str]:
    return [control_id for control_id in desired_control_ids if control_id in control_ids]


def _build_summary(backlog_items: list[dict[str, Any]]) -> dict[str, Any]:
    high_priority_count = sum(
        1 for item in backlog_items if item.get("priority") == "high"
    )

    approval_required_count = sum(
        1
        for item in backlog_items
        if item.get("requires_human_approval_before_execution")
    )

    return {
        "backlog_item_count": len(backlog_items),
        "high_priority_count": high_priority_count,
        "approval_required_count": approval_required_count,
        "github_issues_created": 0,
    }