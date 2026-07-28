from __future__ import annotations

from typing import Iterable

from readiness_core.models import (
    AutonomyPosture,
    ImplementationPhase,
    OperationType,
    RiskLevel,
    StepAutonomyRecommendation,
    ToolCapabilityRecommendation,
)


def infer_tool_capabilities(
    autonomy_matrix: Iterable[StepAutonomyRecommendation],
    default_evidence_references: list[str],
) -> list[ToolCapabilityRecommendation]:
    """Infer enterprise tool capabilities needed to support the recommended AI posture.

    This intentionally recommends generic capabilities, not vendor-specific tools.
    Vendor mapping should happen later through configuration, not model invention.
    """

    selected_capabilities: dict[str, ToolCapabilityRecommendation] = {}

    def add_capability(capability: ToolCapabilityRecommendation) -> None:
        selected_capabilities[capability.capability_name] = capability

    add_capability(
        ToolCapabilityRecommendation(
            capability_name="workflow_document_search",
            capability_description="Search approved workflow, policy, and procedure documents.",
            operation_type=OperationType.read,
            recommended_access=AutonomyPosture.ai_assist,
            risk_level=RiskLevel.low,
            approval_required=False,
            audit_required=True,
            mcp_server_candidate="document_server",
            implementation_phase=ImplementationPhase.phase_1_read_only_analysis,
            evidence_references=default_evidence_references,
        )
    )

    add_capability(
        ToolCapabilityRecommendation(
            capability_name="policy_lookup",
            capability_description="Retrieve applicable policy, control, and approval requirements.",
            operation_type=OperationType.read,
            recommended_access=AutonomyPosture.ai_assist,
            risk_level=RiskLevel.low,
            approval_required=False,
            audit_required=True,
            mcp_server_candidate="policy_server",
            implementation_phase=ImplementationPhase.phase_1_read_only_analysis,
            evidence_references=default_evidence_references,
        )
    )

    add_capability(
        ToolCapabilityRecommendation(
            capability_name="data_classification",
            capability_description="Classify workflow fields by sensitivity and required handling controls.",
            operation_type=OperationType.read,
            recommended_access=AutonomyPosture.ai_assist,
            risk_level=RiskLevel.medium,
            approval_required=False,
            audit_required=True,
            mcp_server_candidate="policy_server",
            implementation_phase=ImplementationPhase.phase_1_read_only_analysis,
            evidence_references=default_evidence_references,
        )
    )

    for step in autonomy_matrix:
        text = " ".join(
            [
                step.step_name,
                step.current_step_summary,
                " ".join(step.allowed_ai_actions),
                " ".join(step.blocked_ai_actions),
            ]
        ).lower()

        evidence_refs = step.evidence_references or default_evidence_references

        if any(keyword in text for keyword in ["missing", "unclear", "conflicting", "incomplete", "intake"]):
            add_capability(
                ToolCapabilityRecommendation(
                    capability_name="intake_validation",
                    capability_description="Check whether workflow intake contains required fields and flag incomplete or conflicting information.",
                    operation_type=OperationType.read,
                    recommended_access=AutonomyPosture.ai_assist,
                    risk_level=RiskLevel.medium,
                    approval_required=False,
                    audit_required=True,
                    mcp_server_candidate="document_server",
                    implementation_phase=ImplementationPhase.phase_1_read_only_analysis,
                    evidence_references=evidence_refs,
                )
            )

        if any(keyword in text for keyword in ["approve", "approval", "reject", "reviewer", "human reviewer"]):
            add_capability(
                ToolCapabilityRecommendation(
                    capability_name="approval_request",
                    capability_description="Prepare approval packages and route decisions to the required human reviewer.",
                    operation_type=OperationType.write,
                    recommended_access=AutonomyPosture.ai_recommend_human_approve,
                    risk_level=RiskLevel.high,
                    approval_required=True,
                    audit_required=True,
                    mcp_server_candidate="approval_server",
                    implementation_phase=ImplementationPhase.phase_2_human_reviewed_recommendations,
                    evidence_references=evidence_refs,
                )
            )

        if any(keyword in text for keyword in ["ticket", "status", "tracking", "record", "evidence"]):
            add_capability(
                ToolCapabilityRecommendation(
                    capability_name="workflow_record_update",
                    capability_description="Update workflow records, ticket status, and evidence fields after required approvals are confirmed.",
                    operation_type=OperationType.write,
                    recommended_access=AutonomyPosture.approval_gated_action,
                    risk_level=RiskLevel.high,
                    approval_required=True,
                    audit_required=True,
                    mcp_server_candidate="project_mgmt_server",
                    implementation_phase=ImplementationPhase.phase_3_approval_gated_actions,
                    evidence_references=evidence_refs,
                )
            )

        if any(keyword in text for keyword in ["provision", "access", "permission", "entitlement"]):
            add_capability(
                ToolCapabilityRecommendation(
                    capability_name="system_access_provisioning",
                    capability_description="Prepare or execute access provisioning actions only after policy, approval, and audit requirements are satisfied.",
                    operation_type=OperationType.write,
                    recommended_access=AutonomyPosture.approval_gated_action,
                    risk_level=RiskLevel.critical,
                    approval_required=True,
                    audit_required=True,
                    mcp_server_candidate="provisioning_server",
                    implementation_phase=ImplementationPhase.phase_3_approval_gated_actions,
                    evidence_references=evidence_refs,
                )
            )

        if any(keyword in text for keyword in ["notify", "email", "message", "communication", "route back"]):
            add_capability(
                ToolCapabilityRecommendation(
                    capability_name="controlled_notification",
                    capability_description="Prepare or send workflow communications with appropriate review, logging, and recipient controls.",
                    operation_type=OperationType.external_communication,
                    recommended_access=AutonomyPosture.ai_recommend_human_approve,
                    risk_level=RiskLevel.medium,
                    approval_required=True,
                    audit_required=True,
                    mcp_server_candidate="notification_server",
                    implementation_phase=ImplementationPhase.phase_2_human_reviewed_recommendations,
                    evidence_references=evidence_refs,
                )
            )

        if any(keyword in text for keyword in ["report", "weekly", "metric", "dashboard"]):
            add_capability(
                ToolCapabilityRecommendation(
                    capability_name="report_generation",
                    capability_description="Generate workflow status, exception, and audit-readiness reports from approved records.",
                    operation_type=OperationType.read,
                    recommended_access=AutonomyPosture.ai_assist,
                    risk_level=RiskLevel.medium,
                    approval_required=False,
                    audit_required=True,
                    mcp_server_candidate="reporting_server",
                    implementation_phase=ImplementationPhase.phase_2_human_reviewed_recommendations,
                    evidence_references=evidence_refs,
                )
            )

    add_capability(
        ToolCapabilityRecommendation(
            capability_name="audit_event_write",
            capability_description="Record model actions, tool calls, approvals, write attempts, and generated artifacts.",
            operation_type=OperationType.write,
            recommended_access=AutonomyPosture.approval_gated_action,
            risk_level=RiskLevel.high,
            approval_required=False,
            audit_required=True,
            mcp_server_candidate="audit_server",
            implementation_phase=ImplementationPhase.phase_1_read_only_analysis,
            evidence_references=default_evidence_references,
        )
    )

    return list(selected_capabilities.values())