import json
from pathlib import Path
from typing import Any


REQUIRED_OUTPUT_FILES = [
    "README.md",
    "approval_response.json",
    "artifacts.json",
    "audit_events.json",
    "audit_summary.json",
    "data_sensitivity_report.json",
    "hitl_design.json",
    "implementation_backlog.json",
    "risk_control_matrix.json",
    "run_response.json",
    "workflow_map.json",
]


CUSTOMER_ONBOARDING_REQUIRED_RISKS = {
    "RISK-COMMITMENT-001",
    "RISK-SCOPE-001",
    "RISK-INTEGRATION-001",
    "RISK-HANDOFF-001",
}


CUSTOMER_ONBOARDING_PROHIBITED_PHRASES = [
    "exception advancement",
    "approval-threshold exceptions",
    "high-risk exceptions",
    "financial or operational status updates",
    "financial handling",
    "auto-closed",
    "mark exception",
]


def main() -> None:
    validate_output_folder(
        workflow_id="payment_reconciliation",
        output_dir=Path("examples/payment_reconciliation_outputs"),
    )

    validate_output_folder(
        workflow_id="customer_onboarding",
        output_dir=Path("examples/customer_onboarding_outputs"),
    )

    validate_customer_onboarding_specific_output(
        output_dir=Path("examples/customer_onboarding_outputs"),
    )

    print("PASS: Example outputs validated successfully.")


def validate_output_folder(workflow_id: str, output_dir: Path) -> None:
    if not output_dir.exists():
        raise AssertionError(f"Missing output directory: {output_dir}")

    for filename in REQUIRED_OUTPUT_FILES:
        path = output_dir / filename
        if not path.exists():
            raise AssertionError(f"Missing required output file: {path}")

    run_response = _read_json(output_dir / "run_response.json")
    if run_response["workflow_id"] != workflow_id:
        raise AssertionError(
            f"Expected workflow_id {workflow_id}, got {run_response['workflow_id']}"
        )

    audit_summary = _read_json(output_dir / "audit_summary.json")
    if not audit_summary.get("contains_approval_event"):
        raise AssertionError(f"Missing approval audit event for {workflow_id}")

    if not audit_summary.get("contains_write_action_event"):
        raise AssertionError(f"Missing write-action audit event for {workflow_id}")

    approval_response = _read_json(output_dir / "approval_response.json")
    issue_creation_result = approval_response.get("issue_creation_result", {})

    if approval_response.get("dry_run") is not True:
        raise AssertionError(f"Example export should use dry_run=true for {workflow_id}")

    if issue_creation_result.get("status") != "dry_run":
        raise AssertionError(
            f"Expected dry_run issue creation result for {workflow_id}, "
            f"got {issue_creation_result.get('status')}"
        )


def validate_customer_onboarding_specific_output(output_dir: Path) -> None:
    risk_control_matrix = _read_json(output_dir / "risk_control_matrix.json")
    risk_ids = _collect_risk_ids(risk_control_matrix)

    missing_risks = CUSTOMER_ONBOARDING_REQUIRED_RISKS - risk_ids
    if missing_risks:
        raise AssertionError(
            "Customer onboarding output is missing expected workflow-specific risks: "
            + ", ".join(sorted(missing_risks))
        )

    files_to_scan = [
        output_dir / "risk_control_matrix.json",
        output_dir / "hitl_design.json",
        output_dir / "implementation_backlog.json",
    ]

    for path in files_to_scan:
        text = path.read_text(encoding="utf-8").lower()

        for phrase in CUSTOMER_ONBOARDING_PROHIBITED_PHRASES:
            if phrase in text:
                raise AssertionError(
                    f"Prohibited phrase found in {path}: {phrase}"
                )

    hitl_design = _read_json(output_dir / "hitl_design.json")
    approval_gate_count = hitl_design["content"]["summary"]["approval_gate_count"]

    if approval_gate_count > 6:
        raise AssertionError(
            "Customer onboarding HITL design appears too repetitive. "
            f"approval_gate_count={approval_gate_count}"
        )

    implementation_backlog = _read_json(output_dir / "implementation_backlog.json")
    backlog_titles = [
        item["title"]
        for item in implementation_backlog["content"]["backlog_items"]
    ]

    expected_title_fragment = "onboarding"
    if not any(expected_title_fragment in title.lower() for title in backlog_titles):
        raise AssertionError(
            "Customer onboarding backlog does not appear workflow-specific."
        )


def _collect_risk_ids(risk_control_matrix: dict[str, Any]) -> set[str]:
    risk_ids: set[str] = set()

    for row in risk_control_matrix["content"]["matrix_rows"]:
        for risk in row.get("identified_risks", []):
            risk_ids.add(risk["risk_id"])

    return risk_ids


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()