from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)

    print("\n1. Creating governed workflow run...")

    run_response = client.post(
        "/runs",
        json={"workflow_id": "payment_reconciliation"},
    )

    assert run_response.status_code == 200, run_response.text

    run_data = run_response.json()
    run_id = run_data["run_id"]

    print(f"- run_id: {run_id}")
    print(f"- message: {run_data['message']}")

    print("\n2. Fetching generated artifacts...")

    artifacts_response = client.get(f"/runs/{run_id}/artifacts")
    assert artifacts_response.status_code == 200, artifacts_response.text

    artifacts = artifacts_response.json()
    artifact_types = [artifact["artifact_type"] for artifact in artifacts]

    print(f"- artifact_count: {len(artifacts)}")
    print(f"- artifact_types: {artifact_types}")

    expected_artifacts = {
        "workflow_map",
        "data_sensitivity_report",
        "risk_control_matrix",
        "hitl_design",
        "implementation_backlog",
    }

    missing_artifacts = expected_artifacts.difference(artifact_types)
    assert not missing_artifacts, f"Missing artifacts: {missing_artifacts}"

    implementation_backlog = next(
        artifact
        for artifact in artifacts
        if artifact["artifact_type"] == "implementation_backlog"
    )

    backlog_items = implementation_backlog["content"]["backlog_items"]
    assert backlog_items, "Expected implementation backlog to contain items."

    backlog_id = backlog_items[0]["backlog_id"]

    print(f"- selected_backlog_id: {backlog_id}")

    print("\n3. Approving backlog item in dry-run mode...")

    approval_response = client.post(
        f"/runs/{run_id}/backlog/{backlog_id}/approve",
        json={
            "approved_by": "smoke_test_reviewer",
            "approval_reference": "approval_smoke_test_001",
            "dry_run": True,
            "labels": ["agentops", "smoke-test"],
        },
    )

    assert approval_response.status_code == 200, approval_response.text

    approval_data = approval_response.json()

    print(f"- approval_status: {approval_data['status']}")
    print(f"- approval_reference: {approval_data['approval_reference']}")
    print(f"- issue_status: {approval_data['issue_creation_result']['status']}")
    print(f"- dry_run: {approval_data['issue_creation_result']['dry_run']}")

    assert approval_data["status"] == "approved"
    assert approval_data["issue_creation_result"]["status"] == "dry_run"
    assert approval_data["issue_creation_result"]["dry_run"] is True

    print("\n4. Verifying audit trail...")

    audit_response = client.get(f"/runs/{run_id}/audit")
    assert audit_response.status_code == 200, audit_response.text

    audit_events = audit_response.json()
    event_types = [event["event_type"] for event in audit_events]

    required_audit_events = {
        "run_started",
        "agent_started",
        "policy_checked",
        "tool_called",
        "approval_granted",
        "write_action_executed",
        "agent_completed",
        "run_completed",
    }

    missing_events = required_audit_events.difference(event_types)
    assert not missing_events, f"Missing audit events: {missing_events}"

    print(f"- audit_event_count: {len(audit_events)}")
    print("- required audit events found")

    print("\nPASS: Full governed workflow flow completed successfully.")


if __name__ == "__main__":
    main()