import argparse
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


EVALUATION_PROFILES = {
    "access_request_review": {
        "minimum_score": 80,
        "expected_min_steps": 8,
        "required_artifacts": {
            "workflow_map",
            "data_sensitivity_report",
            "risk_control_matrix",
            "hitl_design",
            "implementation_backlog",
        },
        "required_risk_ids": {
            "RISK-APPROVAL-001",
            "RISK-SOURCE-001",
            "RISK-WRITE-001",
            "RISK-INTEGRATION-001",
            "RISK-HANDOFF-001",
            "RISK-TIMELINE-001",
            "RISK-DATA-001",
        },
        "prohibited_terms": {
            "payment reconciliation",
            "approval-threshold exception",
            "threshold exception",
            "onboarding plan",
            "high-risk onboarding",
            "customer onboarding",
        },
    }
}


def main() -> None:
    args = _parse_args()
    profile = EVALUATION_PROFILES[args.workflow_id]

    client = TestClient(app)

    print(f"\nEvaluating workflow analysis: {args.workflow_id}")

    run_response = client.post(
        "/runs",
        json={"workflow_id": args.workflow_id},
    )
    assert run_response.status_code == 200, run_response.text

    run_data = run_response.json()
    run_id = run_data["run_id"]

    print(f"- run_id: {run_id}")

    artifacts_response = client.get(f"/runs/{run_id}/artifacts")
    assert artifacts_response.status_code == 200, artifacts_response.text

    artifacts = artifacts_response.json()
    artifact_by_type = {
        artifact["artifact_type"]: artifact
        for artifact in artifacts
    }

    audit_response = client.get(f"/runs/{run_id}/audit")
    assert audit_response.status_code == 200, audit_response.text
    audit_events = audit_response.json()

    checks = []

    checks.append(
        _check_required_artifacts(
            artifact_by_type=artifact_by_type,
            required_artifacts=profile["required_artifacts"],
        )
    )

    checks.append(
        _check_workflow_steps(
            workflow_map=artifact_by_type["workflow_map"],
            expected_min_steps=profile["expected_min_steps"],
        )
    )

    checks.append(
        _check_required_risks(
            risk_control_matrix=artifact_by_type["risk_control_matrix"],
            required_risk_ids=profile["required_risk_ids"],
        )
    )

    checks.append(
        _check_data_sensitivity(
            data_sensitivity_report=artifact_by_type["data_sensitivity_report"],
        )
    )

    checks.append(
        _check_hitl_design(
            hitl_design=artifact_by_type["hitl_design"],
        )
    )

    checks.append(
        _check_backlog_coverage(
            implementation_backlog=artifact_by_type["implementation_backlog"],
            required_risk_ids=profile["required_risk_ids"],
        )
    )

    checks.append(
        _check_domain_leakage(
            artifacts=artifacts,
            prohibited_terms=profile["prohibited_terms"],
        )
    )

    checks.append(
        _check_audit_events(
            audit_events=audit_events,
        )
    )

    total_score = sum(check["earned_points"] for check in checks)
    max_score = sum(check["max_points"] for check in checks)

    print("\nEvaluation results:")

    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        print(
            f"- {status}: {check['name']} "
            f"({check['earned_points']}/{check['max_points']})"
        )
        print(f"  {check['details']}")

    print(f"\nScore: {total_score}/{max_score}")

    minimum_score = profile["minimum_score"]

    if total_score < minimum_score:
        raise AssertionError(
            f"Workflow analysis score {total_score} is below required threshold {minimum_score}."
        )

    print("\nPASS: Workflow analysis evaluation completed successfully.")


def _check_required_artifacts(
    artifact_by_type: dict[str, dict[str, Any]],
    required_artifacts: set[str],
) -> dict[str, Any]:
    found = set(artifact_by_type.keys())
    missing = required_artifacts - found
    passed = not missing

    return _result(
        name="Required artifacts generated",
        passed=passed,
        earned_points=10 if passed else 0,
        max_points=10,
        details=f"missing={sorted(missing)}",
    )


def _check_workflow_steps(
    workflow_map: dict[str, Any],
    expected_min_steps: int,
) -> dict[str, Any]:
    steps = workflow_map["content"].get("steps", [])
    passed = len(steps) >= expected_min_steps

    return _result(
        name="Workflow steps captured",
        passed=passed,
        earned_points=10 if passed else 0,
        max_points=10,
        details=f"step_count={len(steps)}, expected_min_steps={expected_min_steps}",
    )


def _check_required_risks(
    risk_control_matrix: dict[str, Any],
    required_risk_ids: set[str],
) -> dict[str, Any]:
    found_risk_ids = _collect_risk_ids(risk_control_matrix)
    missing = required_risk_ids - found_risk_ids

    earned = 20 - min(20, len(missing) * 3)
    passed = earned >= 14

    return _result(
        name="Required risk patterns identified",
        passed=passed,
        earned_points=earned,
        max_points=20,
        details=(
            f"found={sorted(found_risk_ids)}, "
            f"missing={sorted(missing)}"
        ),
    )


def _check_data_sensitivity(
    data_sensitivity_report: dict[str, Any],
) -> dict[str, Any]:
    summary = data_sensitivity_report["content"]["summary"]
    blocked = summary.get("blocked_from_model_context", [])
    redaction = summary.get("requires_redaction", [])

    passed = len(blocked) >= 2 and len(redaction) >= 2

    return _result(
        name="Sensitive data handling identified",
        passed=passed,
        earned_points=15 if passed else 5,
        max_points=15,
        details=(
            f"blocked_from_model_context={blocked}, "
            f"requires_redaction={redaction}"
        ),
    )


def _check_hitl_design(
    hitl_design: dict[str, Any],
) -> dict[str, Any]:
    summary = hitl_design["content"]["summary"]

    approval_gate_count = summary.get("approval_gate_count", 0)
    review_queue_count = summary.get("review_queue_count", 0)
    escalation_rule_count = summary.get("escalation_rule_count", 0)

    passed = (
        approval_gate_count >= 1
        and review_queue_count >= 1
        and escalation_rule_count >= 1
    )

    return _result(
        name="HITL design is actionable",
        passed=passed,
        earned_points=15 if passed else 5,
        max_points=15,
        details=(
            f"approval_gate_count={approval_gate_count}, "
            f"review_queue_count={review_queue_count}, "
            f"escalation_rule_count={escalation_rule_count}"
        ),
    )


def _check_backlog_coverage(
    implementation_backlog: dict[str, Any],
    required_risk_ids: set[str],
) -> dict[str, Any]:
    backlog_risk_ids = set()

    for item in implementation_backlog["content"]["backlog_items"]:
        backlog_risk_ids.update(item.get("source_risk_ids", []))

    missing = required_risk_ids - backlog_risk_ids

    earned = 15 - min(15, len(missing) * 2)
    passed = earned >= 11

    return _result(
        name="Backlog covers identified risk patterns",
        passed=passed,
        earned_points=earned,
        max_points=15,
        details=(
            f"backlog_risk_ids={sorted(backlog_risk_ids)}, "
            f"missing={sorted(missing)}"
        ),
    )


def _check_domain_leakage(
    artifacts: list[dict[str, Any]],
    prohibited_terms: set[str],
) -> dict[str, Any]:
    combined_text = str(artifacts).lower()
    found_terms = sorted(
        term
        for term in prohibited_terms
        if term.lower() in combined_text
    )

    passed = not found_terms

    return _result(
        name="No domain leakage from prior examples",
        passed=passed,
        earned_points=10 if passed else 0,
        max_points=10,
        details=f"found_prohibited_terms={found_terms}",
    )


def _check_audit_events(
    audit_events: list[dict[str, Any]],
) -> dict[str, Any]:
    event_types = {event["event_type"] for event in audit_events}

    required_events = {
        "run_started",
        "agent_started",
        "policy_checked",
        "tool_called",
        "agent_completed",
        "run_completed",
    }

    missing = required_events - event_types
    passed = not missing

    return _result(
        name="Audit trail generated",
        passed=passed,
        earned_points=5 if passed else 0,
        max_points=5,
        details=f"missing={sorted(missing)}, audit_event_count={len(audit_events)}",
    )


def _collect_risk_ids(risk_control_matrix: dict[str, Any]) -> set[str]:
    risk_ids = set()

    for row in risk_control_matrix["content"]["matrix_rows"]:
        for risk in row.get("identified_risks", []):
            risk_ids.add(risk["risk_id"])

    return risk_ids


def _result(
    name: str,
    passed: bool,
    earned_points: int,
    max_points: int,
    details: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "earned_points": earned_points,
        "max_points": max_points,
        "details": details,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate workflow analysis output against a rubric."
    )
    parser.add_argument(
        "--workflow-id",
        default="access_request_review",
        choices=sorted(EVALUATION_PROFILES.keys()),
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()