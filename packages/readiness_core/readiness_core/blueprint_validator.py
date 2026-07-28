from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from readiness_core.models import (
    AgenticReadinessBlueprint,
    AutonomyPosture,
    OperationType,
    RiskLevel,
)


@dataclass(frozen=True)
class BlueprintValidationIssue:
    severity: str
    code: str
    location: str
    message: str


def validate_blueprint_safety(
    blueprint: AgenticReadinessBlueprint,
) -> list[BlueprintValidationIssue]:
    """Validate hard safety constraints for an Agentic Readiness Blueprint.

    This intentionally does not semantically classify free text.
    It validates structured recommendations produced by deterministic or LLM-assisted builders.
    """

    issues: list[BlueprintValidationIssue] = []

    valid_evidence_ids = {
        item.evidence_id
        for item in blueprint.evidence_catalog
        if item.evidence_id
    }

    issues.extend(_validate_evidence_references(blueprint, valid_evidence_ids))
    issues.extend(_validate_autonomy_matrix(blueprint))
    issues.extend(_validate_tooling_blueprint(blueprint))
    issues.extend(_validate_approval_gates(blueprint))

    return issues


def validation_passed(
    issues: Iterable[BlueprintValidationIssue],
) -> bool:
    return not any(issue.severity == "error" for issue in issues)


def _validate_evidence_references(
    blueprint: AgenticReadinessBlueprint,
    valid_evidence_ids: set[str],
) -> list[BlueprintValidationIssue]:
    issues: list[BlueprintValidationIssue] = []

    if not valid_evidence_ids:
        issues.append(
            BlueprintValidationIssue(
                severity="error",
                code="missing_evidence_catalog",
                location="evidence_catalog",
                message="Blueprint must include an evidence catalog.",
            )
        )
        return issues

    for section_name, items in [
        ("readiness_scorecard", blueprint.readiness_scorecard),
        ("step_level_autonomy_matrix", blueprint.step_level_autonomy_matrix),
        ("tooling_blueprint", blueprint.tooling_blueprint),
        ("human_approval_gates", blueprint.human_approval_gates),
        ("risk_control_summary", blueprint.risk_control_summary),
        ("implementation_roadmap", blueprint.implementation_roadmap),
    ]:
        for index, item in enumerate(items):
            refs = getattr(item, "evidence_references", [])

            if not refs:
                issues.append(
                    BlueprintValidationIssue(
                        severity="warning",
                        code="missing_evidence_references",
                        location=f"{section_name}[{index}]",
                        message="Item has no evidence references.",
                    )
                )
                continue

            invalid_refs = sorted(ref for ref in refs if ref not in valid_evidence_ids)

            if invalid_refs:
                issues.append(
                    BlueprintValidationIssue(
                        severity="error",
                        code="invalid_evidence_reference",
                        location=f"{section_name}[{index}]",
                        message=f"Invalid evidence references: {invalid_refs}",
                    )
                )

    return issues


def _validate_autonomy_matrix(
    blueprint: AgenticReadinessBlueprint,
) -> list[BlueprintValidationIssue]:
    issues: list[BlueprintValidationIssue] = []

    for index, step in enumerate(blueprint.step_level_autonomy_matrix):
        location = f"step_level_autonomy_matrix[{index}]"

        if step.recommended_posture == AutonomyPosture.approval_gated_action:
            if not step.approval_required:
                issues.append(
                    BlueprintValidationIssue(
                        severity="error",
                        code="approval_gated_step_missing_approval",
                        location=location,
                        message="Approval-gated steps must require approval.",
                    )
                )

            if not step.audit_required:
                issues.append(
                    BlueprintValidationIssue(
                        severity="error",
                        code="approval_gated_step_missing_audit",
                        location=location,
                        message="Approval-gated steps must require audit logging.",
                    )
                )

            if not step.required_human_reviewer:
                issues.append(
                    BlueprintValidationIssue(
                        severity="error",
                        code="approval_gated_step_missing_reviewer",
                        location=location,
                        message="Approval-gated steps must identify a human reviewer.",
                    )
                )

        if step.risk_level in {RiskLevel.high, RiskLevel.critical} and not step.audit_required:
            issues.append(
                BlueprintValidationIssue(
                    severity="error",
                    code="high_risk_step_missing_audit",
                    location=location,
                    message="High-risk and critical steps must require audit logging.",
                )
            )

        if step.recommended_posture == AutonomyPosture.limited_automation_candidate:
            issues.append(
                BlueprintValidationIssue(
                    severity="warning",
                    code="limited_automation_requires_review",
                    location=location,
                    message="Limited automation candidates require additional production review before deployment.",
                )
            )

    return issues


def _validate_tooling_blueprint(
    blueprint: AgenticReadinessBlueprint,
) -> list[BlueprintValidationIssue]:
    issues: list[BlueprintValidationIssue] = []

    for index, tool in enumerate(blueprint.tooling_blueprint):
        location = f"tooling_blueprint[{index}]"

        if tool.operation_type in {
            OperationType.write,
            OperationType.mixed,
            OperationType.external_communication,
        }:
            if not tool.audit_required:
                issues.append(
                    BlueprintValidationIssue(
                        severity="error",
                        code="write_tool_missing_audit",
                        location=location,
                        message="Write, mixed, and external-communication tools must require audit logging.",
                    )
                )

            if not tool.approval_required and tool.capability_name != "audit_event_write":
                issues.append(
                    BlueprintValidationIssue(
                        severity="error",
                        code="write_tool_missing_approval",
                        location=location,
                        message="Write, mixed, and external-communication tools must require approval unless explicitly exempted.",
                    )
                )

        if (
            tool.operation_type in {OperationType.write, OperationType.mixed}
            and tool.recommended_access == AutonomyPosture.limited_automation_candidate
        ):
            issues.append(
                BlueprintValidationIssue(
                    severity="error",
                    code="write_tool_limited_automation_not_allowed",
                    location=location,
                    message="Write-capable tools cannot be recommended for limited automation without a separate production control review.",
                )
            )

    return issues


def _validate_approval_gates(
    blueprint: AgenticReadinessBlueprint,
) -> list[BlueprintValidationIssue]:
    issues: list[BlueprintValidationIssue] = []

    for index, gate in enumerate(blueprint.human_approval_gates):
        location = f"human_approval_gates[{index}]"

        if not gate.required_reviewer:
            issues.append(
                BlueprintValidationIssue(
                    severity="error",
                    code="approval_gate_missing_reviewer",
                    location=location,
                    message="Approval gates must identify the required reviewer.",
                )
            )

        if not gate.blocked_without_approval:
            issues.append(
                BlueprintValidationIssue(
                    severity="warning",
                    code="approval_gate_missing_blocked_actions",
                    location=location,
                    message="Approval gates should identify what is blocked without approval.",
                )
            )

        if not gate.required_evidence:
            issues.append(
                BlueprintValidationIssue(
                    severity="warning",
                    code="approval_gate_missing_required_evidence",
                    location=location,
                    message="Approval gates should identify required evidence.",
                )
            )

    return issues