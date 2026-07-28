from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare deterministic Agentic Readiness Blueprint with LLM Blueprint Advisor proposal."
    )
    parser.add_argument("--baseline-path", required=True)
    parser.add_argument("--proposal-path", required=True)
    parser.add_argument("--export-json", action="store_true")

    args = parser.parse_args()

    baseline_path = Path(args.baseline_path)
    proposal_path = Path(args.proposal_path)

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

    comparison = compare_blueprints(
        baseline=baseline,
        proposal=proposal,
        baseline_path=baseline_path,
        proposal_path=proposal_path,
    )

    print("Blueprint Comparison")
    print(f"- workflow_id: {comparison['workflow_id']}")
    print(f"- run_id: {comparison['run_id']}")
    print(f"- baseline_recommendation: {comparison['recommendation_comparison']['baseline']}")
    print(f"- proposal_recommendation: {comparison['recommendation_comparison']['proposal']}")
    print(f"- recommendation_match: {comparison['recommendation_comparison']['match']}")

    summary = comparison["summary"]
    print("\nSummary")
    print(f"- step_count_baseline: {summary['step_count_baseline']}")
    print(f"- step_count_proposal: {summary['step_count_proposal']}")
    print(f"- step_posture_matches: {summary['step_posture_matches']}")
    print(f"- step_posture_disagreements: {summary['step_posture_disagreements']}")
    print(f"- tooling_matches: {summary['tooling_matches']}")
    print(f"- tooling_disagreements: {summary['tooling_disagreements']}")
    print(f"- review_required_count: {summary['review_required_count']}")

    print("\nStep Comparison")
    for row in comparison["step_comparison"]:
        marker = "MATCH" if row["posture_match"] else "REVIEW"
        print(
            f"- {marker} {row['step_id']} "
            f"baseline={row['baseline_posture']} "
            f"proposal={row['proposal_posture']} "
            f"| {row['proposal_step_name'] or row['baseline_step_name']}"
        )

    print("\nTooling Comparison")
    for row in comparison["tooling_comparison"]:
        marker = "MATCH" if row["matches"] else "REVIEW"
        print(
            f"- {marker} {row['capability_name']} "
            f"baseline={row['baseline_operation_type']}/{row['baseline_risk_level']} "
            f"proposal={row['proposal_operation_type']}/{row['proposal_risk_level']}"
        )

    if comparison["review_items"]:
        print("\nReview Items")
        for item in comparison["review_items"]:
            print(f"- {item['severity']} {item['code']} {item['location']}: {item['message']}")

    if args.export_json:
        output_path = _write_export(comparison)
        print(f"\njson_export_path: {output_path}")


def compare_blueprints(
    *,
    baseline: dict[str, Any],
    proposal: dict[str, Any],
    baseline_path: Path,
    proposal_path: Path,
) -> dict[str, Any]:
    workflow_id = baseline.get("workflow_id") or proposal.get("metadata", {}).get("workflow_id")
    run_id = baseline.get("run_id") or proposal.get("metadata", {}).get("run_id")

    step_comparison = _compare_steps(
        baseline.get("step_level_autonomy_matrix", []),
        proposal.get("step_level_autonomy_matrix", []),
    )

    tooling_comparison = _compare_tooling(
        baseline.get("tooling_blueprint", []),
        proposal.get("tooling_blueprint", []),
    )

    approval_gate_comparison = _compare_approval_gates(
        baseline.get("human_approval_gates", []),
        proposal.get("human_approval_gates", []),
    )

    recommendation_comparison = {
        "baseline": baseline.get("executive_summary", {}).get("recommendation"),
        "proposal": proposal.get("executive_summary", {}).get("recommendation"),
    }
    recommendation_comparison["match"] = (
        recommendation_comparison["baseline"] == recommendation_comparison["proposal"]
    )

    review_items = []
    review_items.extend(_step_review_items(step_comparison))
    review_items.extend(_tooling_review_items(tooling_comparison))
    review_items.extend(_recommendation_review_items(recommendation_comparison))

    summary = {
        "step_count_baseline": len(baseline.get("step_level_autonomy_matrix", [])),
        "step_count_proposal": len(proposal.get("step_level_autonomy_matrix", [])),
        "step_posture_matches": sum(1 for row in step_comparison if row["posture_match"]),
        "step_posture_disagreements": sum(1 for row in step_comparison if not row["posture_match"]),
        "tooling_matches": sum(1 for row in tooling_comparison if row["matches"]),
        "tooling_disagreements": sum(1 for row in tooling_comparison if not row["matches"]),
        "approval_gate_count_baseline": len(baseline.get("human_approval_gates", [])),
        "approval_gate_count_proposal": len(proposal.get("human_approval_gates", [])),
        "review_required_count": len(review_items),
    }

    return {
        "comparison_version": "0.1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "workflow_id": workflow_id,
        "run_id": run_id,
        "baseline_path": str(baseline_path),
        "proposal_path": str(proposal_path),
        "recommendation_comparison": recommendation_comparison,
        "summary": summary,
        "step_comparison": step_comparison,
        "tooling_comparison": tooling_comparison,
        "approval_gate_comparison": approval_gate_comparison,
        "review_items": review_items,
        "reconciliation_note": (
            "This comparison does not choose the final blueprint. It identifies where the "
            "deterministic baseline and LLM advisor agree or disagree so the reconciliation "
            "layer can apply safety rules and human-review requirements."
        ),
    }


def _compare_steps(
    baseline_steps: list[dict[str, Any]],
    proposal_steps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline_by_id = {step.get("step_id"): step for step in baseline_steps}
    proposal_by_id = {step.get("step_id"): step for step in proposal_steps}

    step_ids = sorted(set(baseline_by_id) | set(proposal_by_id))

    rows = []

    for step_id in step_ids:
        baseline = baseline_by_id.get(step_id, {})
        proposal = proposal_by_id.get(step_id, {})

        baseline_posture = baseline.get("recommended_posture")
        proposal_posture = proposal.get("recommended_posture")

        rows.append(
            {
                "step_id": step_id,
                "baseline_step_name": baseline.get("step_name"),
                "proposal_step_name": proposal.get("step_name"),
                "baseline_posture": baseline_posture,
                "proposal_posture": proposal_posture,
                "posture_match": baseline_posture == proposal_posture,
                "baseline_risk_level": baseline.get("risk_level"),
                "proposal_risk_level": proposal.get("risk_level"),
                "risk_match": baseline.get("risk_level") == proposal.get("risk_level"),
                "baseline_approval_required": baseline.get("approval_required"),
                "proposal_approval_required": proposal.get("approval_required"),
                "approval_match": baseline.get("approval_required") == proposal.get("approval_required"),
                "baseline_audit_required": baseline.get("audit_required"),
                "proposal_audit_required": proposal.get("audit_required"),
                "audit_match": baseline.get("audit_required") == proposal.get("audit_required"),
            }
        )

    return rows


def _compare_tooling(
    baseline_tools: list[dict[str, Any]],
    proposal_tools: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline_by_name = {tool.get("capability_name"): tool for tool in baseline_tools}
    proposal_by_name = {tool.get("capability_name"): tool for tool in proposal_tools}

    capability_names = sorted(set(baseline_by_name) | set(proposal_by_name))

    rows = []

    for capability_name in capability_names:
        baseline = baseline_by_name.get(capability_name, {})
        proposal = proposal_by_name.get(capability_name, {})

        operation_match = baseline.get("operation_type") == proposal.get("operation_type")
        risk_match = baseline.get("risk_level") == proposal.get("risk_level")
        approval_match = baseline.get("approval_required") == proposal.get("approval_required")
        audit_match = baseline.get("audit_required") == proposal.get("audit_required")

        rows.append(
            {
                "capability_name": capability_name,
                "present_in_baseline": bool(baseline),
                "present_in_proposal": bool(proposal),
                "baseline_operation_type": baseline.get("operation_type"),
                "proposal_operation_type": proposal.get("operation_type"),
                "operation_match": operation_match,
                "baseline_risk_level": baseline.get("risk_level"),
                "proposal_risk_level": proposal.get("risk_level"),
                "risk_match": risk_match,
                "baseline_approval_required": baseline.get("approval_required"),
                "proposal_approval_required": proposal.get("approval_required"),
                "approval_match": approval_match,
                "baseline_audit_required": baseline.get("audit_required"),
                "proposal_audit_required": proposal.get("audit_required"),
                "audit_match": audit_match,
                "matches": (
                    bool(baseline)
                    and bool(proposal)
                    and operation_match
                    and risk_match
                    and approval_match
                    and audit_match
                ),
            }
        )

    return rows


def _compare_approval_gates(
    baseline_gates: list[dict[str, Any]],
    proposal_gates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "baseline_count": len(baseline_gates),
        "proposal_count": len(proposal_gates),
        "count_match": len(baseline_gates) == len(proposal_gates),
        "baseline_gate_names": [gate.get("gate_name") for gate in baseline_gates],
        "proposal_gate_names": [gate.get("gate_name") for gate in proposal_gates],
    }


def _step_review_items(step_comparison: list[dict[str, Any]]) -> list[dict[str, str]]:
    items = []

    for row in step_comparison:
        location = f"step_level_autonomy_matrix.{row['step_id']}"

        if not row["posture_match"]:
            items.append(
                _review_item(
                    severity="review",
                    code="step_posture_disagreement",
                    location=location,
                    message=(
                        f"Baseline posture is {row['baseline_posture']}; "
                        f"LLM proposal posture is {row['proposal_posture']}."
                    ),
                )
            )

        if not row["approval_match"]:
            items.append(
                _review_item(
                    severity="review",
                    code="step_approval_disagreement",
                    location=location,
                    message=(
                        f"Baseline approval_required is {row['baseline_approval_required']}; "
                        f"LLM proposal approval_required is {row['proposal_approval_required']}."
                    ),
                )
            )

        if row["baseline_audit_required"] is True and row["proposal_audit_required"] is not True:
            items.append(
                _review_item(
                    severity="error",
                    code="proposal_removed_required_audit",
                    location=location,
                    message="LLM proposal removed audit requirement that exists in baseline.",
                )
            )

    return items


def _tooling_review_items(tooling_comparison: list[dict[str, Any]]) -> list[dict[str, str]]:
    items = []

    for row in tooling_comparison:
        location = f"tooling_blueprint.{row['capability_name']}"

        if not row["present_in_baseline"] or not row["present_in_proposal"]:
            items.append(
                _review_item(
                    severity="review",
                    code="tool_capability_presence_disagreement",
                    location=location,
                    message="Tool capability is not present in both baseline and proposal.",
                )
            )
            continue

        if not row["matches"]:
            items.append(
                _review_item(
                    severity="review",
                    code="tool_capability_control_disagreement",
                    location=location,
                    message="Tool capability control settings differ between baseline and proposal.",
                )
            )

        if row["baseline_audit_required"] is True and row["proposal_audit_required"] is not True:
            items.append(
                _review_item(
                    severity="error",
                    code="proposal_removed_tool_audit_requirement",
                    location=location,
                    message="LLM proposal removed audit requirement that exists in baseline tooling.",
                )
            )

        if row["baseline_approval_required"] is True and row["proposal_approval_required"] is not True:
            items.append(
                _review_item(
                    severity="error",
                    code="proposal_removed_tool_approval_requirement",
                    location=location,
                    message="LLM proposal removed approval requirement that exists in baseline tooling.",
                )
            )

    return items


def _recommendation_review_items(
    recommendation_comparison: dict[str, Any],
) -> list[dict[str, str]]:
    if recommendation_comparison["match"]:
        return []

    return [
        _review_item(
            severity="review",
            code="readiness_recommendation_disagreement",
            location="executive_summary.recommendation",
            message=(
                f"Baseline recommendation is {recommendation_comparison['baseline']}; "
                f"LLM proposal recommendation is {recommendation_comparison['proposal']}."
            ),
        )
    ]


def _review_item(
    *,
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


def _write_export(comparison: dict[str, Any]) -> Path:
    output_dir = Path("examples/blueprint_comparisons")
    output_dir.mkdir(parents=True, exist_ok=True)

    workflow_id = comparison["workflow_id"]
    run_id = comparison["run_id"]

    output_path = output_dir / f"{workflow_id}_{run_id}_blueprint_comparison.json"
    output_path.write_text(
        json.dumps(comparison, indent=2),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    main()