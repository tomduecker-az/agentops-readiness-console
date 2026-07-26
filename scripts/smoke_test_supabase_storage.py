from fastapi.testclient import TestClient

from app.main import app
from app.storage.supabase_store import get_workflow_run_record


def main() -> None:
    client = TestClient(app)

    print("\n1. Creating workflow run backed by Supabase...")
    run_response = client.post(
        "/runs",
        json={"workflow_id": "payment_reconciliation"},
    )
    assert run_response.status_code == 200, run_response.text

    run_data = run_response.json()
    run_id = run_data["run_id"]

    print(f"- run_id: {run_id}")

    print("\n2. Confirming persisted workflow run record...")
    run_record = get_workflow_run_record(run_id)
    assert run_record is not None, "Expected workflow run record in Supabase."
    assert run_record["run_id"] == run_id
    assert run_record["status"] == "completed"

    print(f"- workflow_id: {run_record['workflow_id']}")
    print(f"- run_status: {run_record['status']}")

    print("\n3. Confirming persisted artifacts through API...")
    artifacts_response = client.get(f"/runs/{run_id}/artifacts")
    assert artifacts_response.status_code == 200, artifacts_response.text

    artifacts = artifacts_response.json()
    artifact_types = {artifact["artifact_type"] for artifact in artifacts}

    expected_artifacts = {
        "workflow_map",
        "data_sensitivity_report",
        "risk_control_matrix",
        "hitl_design",
        "implementation_backlog",
    }

    missing_artifacts = expected_artifacts.difference(artifact_types)
    assert not missing_artifacts, f"Missing artifacts: {missing_artifacts}"

    print(f"- artifact_count: {len(artifacts)}")

    print("\n4. Confirming persisted audit events through API...")
    audit_response = client.get(f"/runs/{run_id}/audit")
    assert audit_response.status_code == 200, audit_response.text

    audit_events = audit_response.json()
    event_types = {event["event_type"] for event in audit_events}

    required_events = {
        "run_started",
        "agent_started",
        "policy_checked",
        "tool_called",
        "agent_completed",
        "run_completed",
    }

    missing_events = required_events.difference(event_types)
    assert not missing_events, f"Missing audit events: {missing_events}"

    print(f"- audit_event_count: {len(audit_events)}")

    print("\nPASS: Supabase persistent storage verified.")


if __name__ == "__main__":
    main()