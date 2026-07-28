from __future__ import annotations

import copy
from datetime import UTC, datetime
from typing import Any

from readiness_core.models import (
    AgenticReadinessBlueprint,
    AutonomyPosture,
    OperationType,
    RiskLevel,
)


_RISK_RANK = {
    RiskLevel.low.value: 1,
    RiskLevel.medium.value: 2,
    RiskLevel.high.value: 3,
    RiskLevel.critical.value: 4,
}

_OPERATION_RANK = {
    OperationType.read.value: 1,
    OperationType.external_communication.value: 2,
    OperationType.write.value: 3,
    OperationType.mixed.value: 4,
}


def reconcile_blueprint_with_llm_proposal(
    *,
    baseline_blueprint: dict[str, Any],
    llm_proposal: dict[str, Any],
    comparison: dict[str, Any] | None = None,
) -> tuple[AgenticReadinessBlueprint, dict[str, Any]]:
    """Create a final blueprint from deterministic baseline and LLM proposal.

    The LLM proposal supplies richer semantic recommendations.
    The deterministic baseline supplies safety floors and complete product structure.
    """

    reconciled = copy.deepcopy(baseline_blueprint)

    reconciliation_report: dict[str, Any] = {
        "reconciliation_version": "0.1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "strategy": "llm_proposal_with_deterministic_safety_floor",
        "accepted_sections": [],
        "safety_overrides": [],
        "review_items": [],
    }

    _replace_executive_summary(
        reconciled=reconciled,
        proposal=llm_proposal,
        reconciliation_report=reconciliation_report,
    )

    reconciled["step_level_autonomy_matrix"] = _reconcile_steps(
        baseline_steps=baseline_blueprint.get("step_level_autonomy_matrix", []),
        proposal_steps=llm_proposal.get("step_level_autonomy_matrix", []),
        reconciliation_report=reconciliation_report,
    )

    reconciled["tooling_blueprint"] = _reconcile_tooling(
        baseline_tools=baseline_blueprint.get("tooling_blueprint", []),
        proposal_tools=llm_proposal.get("tooling_blueprint", []),
        reconciliation_report=reconciliation_report,
    )

    _replace_if_present(
        reconciled=reconciled,
        proposal=llm_proposal,
        section_name="human_approval_gates",
        reconciliation_report=reconciliation_report,
    )

    _replace_if_present(
        reconciled=reconciled,
        proposal=llm_proposal,
        section_name="risk_control_summary",
        reconciliation_report=reconciliation_report,
    )

    _replace_if_present(
        reconciled=reconciled,
        proposal=llm_proposal,
        section_name="implementation_roadmap",
        reconciliation_report=reconciliation_report,
    )

    _replace_if_present(
        reconciled=reconciled,
        proposal=llm_proposal,
        section_name="limitations_and_missing_information",
        reconciliation_report=reconciliation_report,
    )

    reconciled["created_at"] = datetime.now(UTC).isoformat()

    metadata = reconciled.setdefault("metadata", {})
    metadata["generation_mode"] = "llm_assisted_with_deterministic_validation"
    metadata["baseline_generation_mode"] = baseline_blueprint.get("metadata", {}).get(
        "generation_mode",
        "deterministic_from_validated_artifacts",
    )
    metadata["llm_proposal_generation_mode"] = llm_proposal.get("metadata", {}).get(
        "generation_mode",
        "llm_assisted_proposal_only",
    )
    metadata["reconciliation_report"] = reconciliation_report

    if comparison:
        metadata["blueprint_comparison_summary"] = comparison.get("summary", {})
        metadata["blueprint_comparison_review_items"] = comparison.get("review_items", [])

    blueprint = AgenticReadinessBlueprint.model_validate(reconciled)

    return blueprint, reconciliation_report


def _replace_executive_summary(
    *,
    reconciled: dict[str, Any],
    proposal: dict[str, Any],
    reconciliation_report: dict[str, Any],
) -> None:
    proposed_summary = proposal.get("executive_summary")

    if not proposed_summary:
        reconciliation_report["review_items"].append(
            _review_item(
                "warning",
                "missing_proposal_executive_summary",
                "executive_summary",
                "LLM proposal did not include executive summary; baseline retained.",
            )
        )
        return

    cleaned_summary = {
        key: value
        for key, value in proposed_summary.items()
        if key != "evidence_references"
    }

    reconciled["executive_summary"] = cleaned_summary
    reconciliation_report["accepted_sections"].append("executive_summary")


def _replace_if_present(
    *,
    reconciled: dict[str, Any],
    proposal: dict[str, Any],
    section_name: str,
    reconciliation_report: dict[str, Any],
) -> None:
    if proposal.get(section_name):
        reconciled[section_name] = proposal[section_name]
        reconciliation_report["accepted_sections"].append(section_name)
    else:
        reconciliation_report["review_items"].append(
            _review_item(
                "warning",
                f"missing_proposal_{section_name}",
                section_name,
                f"LLM proposal did not include {section_name}; baseline retained.",
            )
        )


def _reconcile_steps(
    *,
    baseline_steps: list[dict[str, Any]],
    proposal_steps: list[dict[str, Any]],
    reconciliation_report: dict[str, Any],
) -> list[dict[str, Any]]:
    baseline_by_id = {step.get("step_id"): step for step in baseline_steps}
    proposal_by_id = {step.get("step_id"): step for step in proposal_steps}

    step_ids = sorted(set(baseline_by_id) | set(proposal_by_id))

    reconciled_steps = []

    for step_id in step_ids:
        baseline = baseline_by_id.get(step_id)
        proposal = proposal_by_id.get(step_id)

        if baseline and not proposal:
            reconciled_steps.append(baseline)
            reconciliation_report["review_items"].append(
                _review_item(
                    "warning",
                    "missing_proposal_step",
                    f"step_level_autonomy_matrix.{step_id}",
                    "Step exists in baseline but not LLM proposal; baseline retained.",
                )
            )
            continue

        if proposal and not baseline:
            reconciled_steps.append(proposal)
            reconciliation_report["review_items"].append(
                _review_item(
                    "warning",
                    "proposal_added_step",
                    f"step_level_autonomy_matrix.{step_id}",
                    "Step exists in LLM proposal but not baseline; proposal retained for review.",
                )
            )
            continue

        assert baseline is not None
        assert proposal is not None

        reconciled = copy.deepcopy(proposal)

        _apply_step_safety_floor(
            step_id=step_id,
            baseline=baseline,
            reconciled=reconciled,
            reconciliation_report=reconciliation_report,
        )

        reconciled_steps.append(reconciled)

    reconciliation_report["accepted_sections"].append("step_level_autonomy_matrix")

    return reconciled_steps


def _apply_step_safety_floor(
    *,
    step_id: str,
    baseline: dict[str, Any],
    reconciled: dict[str, Any],
    reconciliation_report: dict[str, Any],
) -> None:
    baseline_posture = baseline.get("recommended_posture")
    proposal_posture = reconciled.get("recommended_posture")

    if baseline_posture == AutonomyPosture.approval_gated_action.value:
        if proposal_posture != AutonomyPosture.approval_gated_action.value:
            reconciled["recommended_posture"] = AutonomyPosture.approval_gated_action.value
            _record_override(
                reconciliation_report,
                location=f"step_level_autonomy_matrix.{step_id}.recommended_posture",
                baseline_value=baseline_posture,
                proposal_value=proposal_posture,
                final_value=reconciled["recommended_posture"],
                reason="Baseline identified approval-gated action; LLM proposal cannot downgrade governed action.",
            )

    if baseline.get("approval_required") is True and reconciled.get("approval_required") is not True:
        proposal_value = reconciled.get("approval_required")
        reconciled["approval_required"] = True
        _record_override(
            reconciliation_report,
            location=f"step_level_autonomy_matrix.{step_id}.approval_required",
            baseline_value=True,
            proposal_value=proposal_value,
            final_value=True,
            reason="LLM proposal cannot remove approval requirement established by baseline.",
        )

    if baseline.get("audit_required") is True and reconciled.get("audit_required") is not True:
        proposal_value = reconciled.get("audit_required")
        reconciled["audit_required"] = True
        _record_override(
            reconciliation_report,
            location=f"step_level_autonomy_matrix.{step_id}.audit_required",
            baseline_value=True,
            proposal_value=proposal_value,
            final_value=True,
            reason="LLM proposal cannot remove audit requirement established by baseline.",
        )

    baseline_risk = baseline.get("risk_level")
    proposal_risk = reconciled.get("risk_level")
    final_risk = _max_risk_level(baseline_risk, proposal_risk)

    if final_risk != proposal_risk:
        reconciled["risk_level"] = final_risk
        _record_override(
            reconciliation_report,
            location=f"step_level_autonomy_matrix.{step_id}.risk_level",
            baseline_value=baseline_risk,
            proposal_value=proposal_risk,
            final_value=final_risk,
            reason="Final risk level uses the more conservative baseline/proposal risk.",
        )

    if (
        reconciled.get("recommended_posture") == AutonomyPosture.approval_gated_action.value
        and not reconciled.get("required_human_reviewer")
    ):
        reconciled["required_human_reviewer"] = (
            baseline.get("required_human_reviewer") or "Authorized workflow reviewer"
        )
        _record_override(
            reconciliation_report,
            location=f"step_level_autonomy_matrix.{step_id}.required_human_reviewer",
            baseline_value=baseline.get("required_human_reviewer"),
            proposal_value=None,
            final_value=reconciled["required_human_reviewer"],
            reason="Approval-gated actions must identify a human reviewer.",
        )


def _reconcile_tooling(
    *,
    baseline_tools: list[dict[str, Any]],
    proposal_tools: list[dict[str, Any]],
    reconciliation_report: dict[str, Any],
) -> list[dict[str, Any]]:
    baseline_by_name = {tool.get("capability_name"): tool for tool in baseline_tools}
    proposal_by_name = {tool.get("capability_name"): tool for tool in proposal_tools}

    capability_names = sorted(set(baseline_by_name) | set(proposal_by_name))

    reconciled_tools = []

    for capability_name in capability_names:
        baseline = baseline_by_name.get(capability_name)
        proposal = proposal_by_name.get(capability_name)

        if baseline and not proposal:
            reconciled_tools.append(baseline)
            reconciliation_report["review_items"].append(
                _review_item(
                    "warning",
                    "missing_proposal_tool_capability",
                    f"tooling_blueprint.{capability_name}",
                    "Tool capability exists in baseline but not LLM proposal; baseline retained.",
                )
            )
            continue

        if proposal and not baseline:
            reconciled_tools.append(proposal)
            reconciliation_report["review_items"].append(
                _review_item(
                    "warning",
                    "proposal_added_tool_capability",
                    f"tooling_blueprint.{capability_name}",
                    "Tool capability exists in LLM proposal but not baseline; proposal retained for review.",
                )
            )
            continue

        assert baseline is not None
        assert proposal is not None

        reconciled = copy.deepcopy(proposal)

        _apply_tool_safety_floor(
            capability_name=capability_name,
            baseline=baseline,
            reconciled=reconciled,
            reconciliation_report=reconciliation_report,
        )

        reconciled_tools.append(reconciled)

    reconciliation_report["accepted_sections"].append("tooling_blueprint")

    return reconciled_tools


def _apply_tool_safety_floor(
    *,
    capability_name: str,
    baseline: dict[str, Any],
    reconciled: dict[str, Any],
    reconciliation_report: dict[str, Any],
) -> None:
    baseline_operation = baseline.get("operation_type")
    proposal_operation = reconciled.get("operation_type")
    final_operation = _max_operation_type(baseline_operation, proposal_operation)

    if final_operation != proposal_operation:
        reconciled["operation_type"] = final_operation
        _record_override(
            reconciliation_report,
            location=f"tooling_blueprint.{capability_name}.operation_type",
            baseline_value=baseline_operation,
            proposal_value=proposal_operation,
            final_value=final_operation,
            reason="Final operation type uses the more governed baseline/proposal operation.",
        )

    if baseline.get("approval_required") is True and reconciled.get("approval_required") is not True:
        proposal_value = reconciled.get("approval_required")
        reconciled["approval_required"] = True
        _record_override(
            reconciliation_report,
            location=f"tooling_blueprint.{capability_name}.approval_required",
            baseline_value=True,
            proposal_value=proposal_value,
            final_value=True,
            reason="LLM proposal cannot remove tool approval requirement established by baseline.",
        )

    if baseline.get("audit_required") is True and reconciled.get("audit_required") is not True:
        proposal_value = reconciled.get("audit_required")
        reconciled["audit_required"] = True
        _record_override(
            reconciliation_report,
            location=f"tooling_blueprint.{capability_name}.audit_required",
            baseline_value=True,
            proposal_value=proposal_value,
            final_value=True,
            reason="LLM proposal cannot remove tool audit requirement established by baseline.",
        )

    baseline_risk = baseline.get("risk_level")
    proposal_risk = reconciled.get("risk_level")
    final_risk = _max_risk_level(baseline_risk, proposal_risk)

    if final_risk != proposal_risk:
        reconciled["risk_level"] = final_risk
        _record_override(
            reconciliation_report,
            location=f"tooling_blueprint.{capability_name}.risk_level",
            baseline_value=baseline_risk,
            proposal_value=proposal_risk,
            final_value=final_risk,
            reason="Final risk level uses the more conservative baseline/proposal risk.",
        )


def _max_risk_level(left: str | None, right: str | None) -> str | None:
    if left is None:
        return right

    if right is None:
        return left

    return left if _RISK_RANK.get(left, 0) >= _RISK_RANK.get(right, 0) else right


def _max_operation_type(left: str | None, right: str | None) -> str | None:
    if left is None:
        return right

    if right is None:
        return left

    return left if _OPERATION_RANK.get(left, 0) >= _OPERATION_RANK.get(right, 0) else right


def _record_override(
    reconciliation_report: dict[str, Any],
    *,
    location: str,
    baseline_value: Any,
    proposal_value: Any,
    final_value: Any,
    reason: str,
) -> None:
    reconciliation_report["safety_overrides"].append(
        {
            "location": location,
            "baseline_value": baseline_value,
            "proposal_value": proposal_value,
            "final_value": final_value,
            "reason": reason,
        }
    )


def _review_item(
    severity: str,
    code: str,
    location: str,
    message: str,
) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "location": location,
        "message": message,
    }