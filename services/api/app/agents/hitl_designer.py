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
    gates_by_id: dict[str, dict[str, Any]] = {}

    for row in matrix_rows:
        risks = row.get("identified_risks", [])

        for risk in risks:
            risk_id = risk.get("risk_id")

            if risk_id == "RISK-APPROVAL-001":
                _upsert_gate(
                    gates_by_id=gates_by_id,
                    row=row,
                    risk=risk,
                    gate_template={
                        "gate_id": "HITL-GATE-APPROVAL-001",
                        "name": "Human approval before governed workflow advancement",
                        "trigger": (
                            "Workflow item requires supervisor, process-owner, "
                            "or policy-defined approval before advancing."
                        ),
                        "human_reviewer": _recommended_reviewer(row),
                        "agent_allowed_action": "Draft recommendation with rationale and required evidence",
                        "blocked_action_without_approval": (
                            "Advance the workflow item, finalize a decision, "
                            "or communicate a final outcome"
                        ),
                    },
                )

            if risk_id == "RISK-WRITE-001":
                _upsert_gate(
                    gates_by_id=gates_by_id,
                    row=row,
                    risk=risk,
                    gate_template={
                        "gate_id": "HITL-GATE-WRITE-001",
                        "name": "Human approval before operational write action",
                        "trigger": (
                            "Agent recommendation would update workflow state, "
                            "task assignments, customer-facing language, or system-of-record data."
                        ),
                        "human_reviewer": "Process owner or authorized operations reviewer",
                        "agent_allowed_action": "Prepare draft update with rationale",
                        "blocked_action_without_approval": "Execute write action or update system of record",
                    },
                )

            if risk_id == "RISK-DATA-001":
                _upsert_gate(
                    gates_by_id=gates_by_id,
                    row=row,
                    risk=risk,
                    gate_template={
                        "gate_id": "HITL-GATE-DATA-001",
                        "name": "Sensitive-data review before model context use",
                        "trigger": "Input includes fields blocked from model context or requiring redaction.",
                        "human_reviewer": "Data steward or process owner",
                        "agent_allowed_action": "Use approved redacted context or request data handling review",
                        "blocked_action_without_approval": (
                            "Send sensitive or unredacted data to model context"
                        ),
                    },
                )

    return list(gates_by_id.values())


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
                    "workflow item reference",
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
        risk_ids = {risk.get("risk_id") for risk in risks}
        description = str(row.get("description", "")).lower()

        if "RISK-WRITE-001" in risk_ids:
            autonomy_level = "approval_required"
            rationale = (
                "This step may update workflow status, assignments, external language, "
                "or system-of-record data; the agent should prepare a draft only until "
                "human approval is recorded."
            )
        elif _contains_any(
            description,
            [
                "sent externally",
                "shared with the customer",
                "customer-facing",
                "commitment",
                "finalized",
            ],
        ):
            autonomy_level = "approval_required"
            rationale = (
                "This step may affect external communication or commitments; the agent "
                "should not finalize the action without human review."
            )
        elif "RISK-APPROVAL-001" in risk_ids:
            autonomy_level = "recommend_only"
            rationale = (
                "This step requires a governed approval decision; the agent may provide "
                "recommendations but should not make or execute the decision."
            )
        elif "RISK-DATA-001" in risk_ids and _contains_any(
            description,
            ["draft", "plan", "task", "schedule", "assign"],
        ):
            autonomy_level = "draft_only_with_redacted_context"
            rationale = (
                "This step can benefit from drafting support, but sensitive fields must "
                "be redacted or approved before model use."
            )
        elif "RISK-DATA-001" in risk_ids:
            autonomy_level = "assistive_with_redacted_context"
            rationale = (
                "This step may include sensitive data; the agent may assist only with "
                "approved or redacted context."
            )
        elif row.get("decision_point"):
            autonomy_level = "draft_only"
            rationale = (
                "Decision point detected; the agent may prepare a draft but should not "
                "finalize the decision without review."
            )
        else:
            autonomy_level = "assistive"
            rationale = (
                "No high-severity write or approval risk detected; the agent may assist "
                "with summarization, preparation, or evidence gathering."
            )

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
    rules_by_id: dict[str, dict[str, Any]] = {}

    for row in matrix_rows:
        for risk in row.get("identified_risks", []):
            risk_id = risk.get("risk_id")

            if risk_id == "RISK-SOURCE-001":
                _upsert_escalation_rule(
                    rules_by_id=rules_by_id,
                    row=row,
                    rule_template={
                        "rule_id": "ESC-SOURCE-001",
                        "name": "Escalate missing or conflicting source records",
                        "condition": (
                            "Required source information is missing, ambiguous, "
                            "or conflicts with another system or workflow record."
                        ),
                        "escalation_target": "Operations supervisor or data owner",
                        "required_action": "Manual review before the workflow item can be finalized.",
                    },
                )

            if risk_id == "RISK-APPROVAL-001":
                _upsert_escalation_rule(
                    rules_by_id=rules_by_id,
                    row=row,
                    rule_template={
                        "rule_id": "ESC-APPROVAL-001",
                        "name": "Escalate items requiring governed approval",
                        "condition": (
                            "Workflow item meets a policy, supervisor-review, "
                            "sensitive-data, custom-scope, or elevated-risk condition."
                        ),
                        "escalation_target": "Supervisor or process owner",
                        "required_action": (
                            "Authorized reviewer must approve, reject, or request clarification "
                            "before the workflow item advances."
                        ),
                    },
                )

    return list(rules_by_id.values())


def _recommended_reviewer(row: dict[str, Any]) -> str:
    actor = str(row.get("actor", "")).lower()
    description = str(row.get("description", "")).lower()

    if "data" in description or "sensitive" in description:
        return "Data steward or process owner"

    if "customer-facing" in description or "customer" in description and "commitment" in description:
        return "Customer success or process owner"

    if "supervisor" in actor or "supervisor" in description:
        return "Supervisor"

    if "approval" in description or "review" in description:
        return "Supervisor or process owner"

    if "integration" in description or "technical" in description:
        return "Implementation or technical owner"

    return "Process owner"


def _upsert_gate(
    gates_by_id: dict[str, dict[str, Any]],
    row: dict[str, Any],
    risk: dict[str, Any],
    gate_template: dict[str, Any],
) -> None:
    gate_id = gate_template["gate_id"]

    if gate_id not in gates_by_id:
        gates_by_id[gate_id] = {
            **gate_template,
            "source_risk_ids": [],
            "applies_to_steps": [],
        }

    gate = gates_by_id[gate_id]

    risk_id = risk.get("risk_id")
    if risk_id:
        _append_unique(gate["source_risk_ids"], risk_id)

    _add_unique_step_reference(gate["applies_to_steps"], row)

    affected_fields = risk.get("affected_fields")
    if affected_fields:
        gate["affected_fields"] = _merge_affected_fields(
            existing=gate.get("affected_fields", {}),
            incoming=affected_fields,
        )


def _upsert_escalation_rule(
    rules_by_id: dict[str, dict[str, Any]],
    row: dict[str, Any],
    rule_template: dict[str, Any],
) -> None:
    rule_id = rule_template["rule_id"]

    if rule_id not in rules_by_id:
        rules_by_id[rule_id] = {
            **rule_template,
            "applies_to_steps": [],
        }

    _add_unique_step_reference(rules_by_id[rule_id]["applies_to_steps"], row)


def _add_unique_step_reference(
    step_references: list[dict[str, Any]],
    row: dict[str, Any],
) -> None:
    step_id = row.get("step_id")

    if any(step.get("step_id") == step_id for step in step_references):
        return

    step_references.append(
        {
            "step_id": step_id,
            "workflow_step": row.get("description"),
        }
    )


def _merge_affected_fields(
    existing: dict[str, Any],
    incoming: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(existing)

    for key, values in incoming.items():
        if not isinstance(values, list):
            merged[key] = values
            continue

        existing_values = merged.get(key, [])
        if not isinstance(existing_values, list):
            existing_values = []

        for value in values:
            _append_unique(existing_values, value)

        merged[key] = existing_values

    return merged


def _append_unique(values: list[Any], value: Any) -> None:
    if value not in values:
        values.append(value)


def _contains_any(value: str, terms: list[str]) -> bool:
    return any(term in value for term in terms)