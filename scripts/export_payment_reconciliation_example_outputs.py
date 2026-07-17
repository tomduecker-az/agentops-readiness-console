import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from audit_core import clear_audit_events
from app.main import app
from app.services.artifact_service import clear_artifacts


OUTPUT_DIR = Path("examples/payment_reconciliation_outputs")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    clear_artifacts()
    clear_audit_events()

    client = TestClient(app)

    print("Creating payment reconciliation workflow run...")

    run_response = client.post(
        "/runs",
        json={"workflow_id": "payment_reconciliation"},
    )
    run_response.raise_for_status()

    run_data = run_response.json()
    run_id = run_data["run_id"]

    print(f"- run_id: {run_id}")

    artifacts_response = client.get(f"/runs/{run_id}/artifacts")
    artifacts_response.raise_for_status()
    artifacts = artifacts_response.json()

    implementation_backlog = _find_artifact(
        artifacts=artifacts,
        artifact_type="implementation_backlog",
    )

    backlog_items = implementation_backlog["content"]["backlog_items"]
    selected_backlog_id = backlog_items[0]["backlog_id"]

    print(f"Approving backlog item in dry-run mode: {selected_backlog_id}")

    approval_response = client.post(
        f"/runs/{run_id}/backlog/{selected_backlog_id}/approve",
        json={
            "approved_by": "example_export_reviewer",
            "approval_reference": "approval_example_export_001",
            "dry_run": True,
            "labels": ["agentops", "example-output"],
        },
    )
    approval_response.raise_for_status()
    approval_data = approval_response.json()

    updated_artifacts_response = client.get(f"/runs/{run_id}/artifacts")
    updated_artifacts_response.raise_for_status()
    updated_artifacts = updated_artifacts_response.json()

    audit_response = client.get(f"/runs/{run_id}/audit")
    audit_response.raise_for_status()
    audit_events = audit_response.json()

    print("Writing example output files...")

    _write_json("run_response.json", run_data)
    _write_json("approval_response.json", approval_data)
    _write_json("artifacts.json", updated_artifacts)
    _write_json("audit_events.json", audit_events)
    _write_json("audit_summary.json", _build_audit_summary(audit_events))

    for artifact in updated_artifacts:
        artifact_type = artifact["artifact_type"]
        _write_json(f"{artifact_type}.json", artifact)

    _write_readme(
        run_id=run_id,
        artifact_types=[artifact["artifact_type"] for artifact in updated_artifacts],
        selected_backlog_id=selected_backlog_id,
        audit_event_count=len(audit_events),
    )

    print(f"Example outputs written to: {OUTPUT_DIR}")
    print("Done.")


def _find_artifact(
    artifacts: list[dict[str, Any]],
    artifact_type: str,
) -> dict[str, Any]:
    for artifact in artifacts:
        if artifact["artifact_type"] == artifact_type:
            return artifact

    raise ValueError(f"Artifact not found: {artifact_type}")


def _write_json(filename: str, data: Any) -> None:
    path = OUTPUT_DIR / filename

    path.write_text(
        json.dumps(data, indent=2, sort_keys=False),
        encoding="utf-8",
    )


def _build_audit_summary(
    audit_events: list[dict[str, Any]],
) -> dict[str, Any]:
    event_type_counts: dict[str, int] = {}
    actor_counts: dict[str, int] = {}

    for event in audit_events:
        event_type = event["event_type"]
        actor = event["actor"]

        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        actor_counts[actor] = actor_counts.get(actor, 0) + 1

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "audit_event_count": len(audit_events),
        "event_type_counts": event_type_counts,
        "actor_counts": actor_counts,
        "contains_approval_event": "approval_granted" in event_type_counts,
        "contains_write_action_event": "write_action_executed" in event_type_counts,
    }


def _write_readme(
    run_id: str,
    artifact_types: list[str],
    selected_backlog_id: str,
    audit_event_count: int,
) -> None:
    artifact_lines = "\n".join(f"- `{artifact_type}`" for artifact_type in artifact_types)

    content = "\n".join(
        [
            "# Payment Reconciliation Example Outputs",
            "",
            "This folder contains example output from the AgentOps Readiness Console using the demo workflow:",
            "",
            "```text",
            "payment_reconciliation",
            "```",
            "",
            "The example run generated the full governed analysis chain and approved one backlog item in dry-run mode.",
            "",
            "## Run",
            "",
            "```text",
            run_id,
            "```",
            "",
            "## Artifacts",
            "",
            "The run generated:",
            "",
            artifact_lines,
            "",
            "## Approval-Gated Write Action",
            "",
            "The example approved this backlog item:",
            "",
            "```text",
            selected_backlog_id,
            "```",
            "",
            "The approval was executed in dry-run mode, so no real GitHub issue was created by this export script.",
            "",
            "## Audit Trail",
            "",
            "The run produced:",
            "",
            "```text",
            f"{audit_event_count} audit events",
            "```",
            "",
            "See:",
            "",
            "```text",
            "audit_events.json",
            "audit_summary.json",
            "```",
            "",
            "## What This Demonstrates",
            "",
            "This example demonstrates the core governed flow:",
            "",
            "```text",
            "Workflow packet",
            "  → specialist analysis artifacts",
            "  → implementation backlog",
            "  → human approval",
            "  → policy-checked write action",
            "  → audit evidence",
            "```",
            "",
        ]
    )

    (OUTPUT_DIR / "README.md").write_text(content, encoding="utf-8")

if __name__ == "__main__":
    main()