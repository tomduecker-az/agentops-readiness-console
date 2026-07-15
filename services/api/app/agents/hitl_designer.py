from typing import Any

from audit_core import AuditEventType

from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact, get_artifacts_for_run
from app.services.audit_service import log_audit_event


_AGENT_NAME = "hitl_designer"


def generate_hitl_design(run_id: str, workflow_id: str) -> dict[str, Any]:
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

    matrix_rows = risk_control_matrix.get("matrix_rows", [])

    approval_gates = _build_approval_gates(matrix_rows)
    review_queue_design = _build_review_queue_design(matrix_rows)
    autonomy_recommendations = _build_autonomy_recommendations(matrix_rows)
    escalation_rules = _build_escalation_rules(matrix_rows)

    content = {
        "workflow_id": workflow_id,
        "title": "Human-in-the-Loop Design",
        "source_artifacts": {
            "risk_control_matrix": risk_control_matrix.get("title"),
        },
        "approval_gates": approval_gates,
        "review_queue_design": review_queue_design,
        "autonomy_recommendations": autonomy_recommendations,
        "escalation_rules": escalation_rules,
        "summary": {
            "approval_gate_count": len(approval_gates),
            "review_queue_count": len(review_queue_design),
            "autonomy_recommendation_count": len(autonomy_recommendations),
            "escalation_rule_count": len(escalation_rules),
        },
        "generation_mode": "deterministic_skeleton",
    }

    artifact = create_artifact(
        run_id=run_id,
        artifact_type=ArtifactType.hitl_design,
        content=content,
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_completed,
        actor=_AGENT_NAME,
        details={
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type.value,
            "approval_gate_count": len(approval_gates),
            "escalation_rule_count": len(escalation_rules),
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


def _build_approval_gates(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []

    for row in matrix_rows:
        risks = row.get("identified_risks", [])

        for risk in risks:
            risk_id = risk.get("risk_id")

            if risk_id == "RISK-APPROVAL-001":
                gates.append(
                    {
                        "gate_id": "HITL-GATE-APPROVAL-001",
                        "name": "Supervisor approval before exception advancement",
                        "trigger": "Workflow item is above approval threshold or requires supervisor review.",
                        "human_reviewer": "Supervisor",
                        "agent_allowed_action": "Draft recommendation only",
                        "blocked_action_without_approval": "Advance, close, or mark exception as resolved",
                        "source_step_id": row.get("step_id"),
                        "source_risk_id": risk_id,
                    }
                )

            if risk_id == "RISK-WRITE-001":
                gates.append(
                    {
                        "gate_id": "HITL-GATE-WRITE-001",
                        "name": "Human approval before financial or operational status update",
                        "trigger": "Agent recommendation would change workflow status, notes, resolution, or financial handling.",
                        "human_reviewer": "Process owner or authorized operations reviewer",
                        "agent_allowed_action": "Prepare draft update with rationale",
                        "blocked_action_without_approval": "Execute write action",
                        "source_step_id": row.get("step_id"),
                        "source_risk_id": risk_id,
                    }
                )

            if risk_id == "RISK-DATA-001":
                gates.append(
                    {
                        "gate_id": "HITL-GATE-DATA-001",
                        "name": "Sensitive-data review before model context use",
                        "trigger": "Input includes fields blocked from model context or requiring redaction.",
                        "human_reviewer": "Data steward or process owner",
                        "agent_allowed_action": "Request redacted context or classify fields",
                        "blocked_action_without_approval": "Send sensitive or unredacted data to model context",
                        "source_step_id": row.get("step_id"),
                        "source_risk_id": risk_id,
                        "affected_fields": risk.get("affected_fields", {}),
                    }
                )

    return _deduplicate_by_gate_and_step(gates)


def _build_review_queue_design(
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    queue_items: list[dict[str, Any]] = []

    for row in matrix_rows:
        high_risks = [
            risk
            for risk in row.get("identified_risks", [])
            if risk.get("severity") == "high"
        ]

        if not high_risks:
            continue

        queue_items.append(
            {
                "queue_id": f"REVIEW-{row.get('step_id')}",
                "workflow_step": row.get("description"),
                "routing_reason": "One or more high-severity risks were identified for this step.",
                "recommended_reviewer": _recommended_reviewer(row),
                "risk_ids": [risk.get("risk_id") for risk in high_risks],
                "minimum_required_evidence": [
                    "source record reference",
                    "agent recommendation",
                    "policy/control rationale",
                    "human approval decision",
                ],
            }
        )

    return queue_items


def _build_autonomy_recommendations(
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []

    for row in matrix_rows:
        risks = row.get("identified_risks", [])
        high_risk_count = sum(1 for risk in risks if risk.get("severity") == "high")

        if high_risk_count > 0:
            autonomy_level = "recommend_only"
            rationale = "High-severity risks are present; the agent should draft recommendations but not execute actions."
        elif row.get("decision_point"):
            autonomy_level = "draft_action"
            rationale = "Decision point detected; agent may prepare a draft but should not finalize without review."
        else:
            autonomy_level = "assistive"
            rationale = "No high-severity risk detected; agent may assist with summarization or preparation."

        recommendations.append(
            {
                "step_id": row.get("step_id"),
                "workflow_step": row.get("description"),
                "recommended_autonomy_level": autonomy_level,
                "rationale": rationale,
            }
        )

    return recommendations


def _build_escalation_rules(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []

    for row in matrix_rows:
        for risk in row.get("identified_risks", []):
            risk_id = risk.get("risk_id")

            if risk_id == "RISK-SOURCE-001":
                rules.append(
                    {
                        "rule_id": "ESC-SOURCE-001",
                        "name": "Escalate records missing source-system identifiers",
                        "condition": "Source-system identifier is missing, ambiguous, or conflicting.",
                        "escalation_target": "Operations supervisor",
                        "required_action": "Manual review before closure or resolution.",
                        "source_step_id": row.get("step_id"),
                    }
                )

            if risk_id == "RISK-APPROVAL-001":
                rules.append(
                    {
                        "rule_id": "ESC-APPROVAL-001",
                        "name": "Escalate approval-threshold exceptions",
                        "condition": "Exception exceeds threshold or requires supervisor approval.",
                        "escalation_target": "Supervisor",
                        "required_action": "Supervisor must approve or reject recommended resolution.",
                        "source_step_id": row.get("step_id"),
                    }
                )

    return _deduplicate_by_rule_and_step(rules)


def _recommended_reviewer(row: dict[str, Any]) -> str:
    actor = str(row.get("actor", "")).lower()
    description = str(row.get("description", "")).lower()

    if "supervisor" in actor or "supervisor" in description:
        return "Supervisor"

    if "approval" in description:
        return "Supervisor"

    return "Process owner"


def _deduplicate_by_gate_and_step(
    gates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str | None]] = set()
    unique: list[dict[str, Any]] = []

    for gate in gates:
        key = (gate["gate_id"], gate.get("source_step_id"))

        if key in seen:
            continue

        seen.add(key)
        unique.append(gate)

    return unique


def _deduplicate_by_rule_and_step(
    rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str | None]] = set()
    unique: list[dict[str, Any]] = []

    for rule in rules:
        key = (rule["rule_id"], rule.get("source_step_id"))

        if key in seen:
            continue

        seen.add(key)
        unique.append(rule)

    return unique