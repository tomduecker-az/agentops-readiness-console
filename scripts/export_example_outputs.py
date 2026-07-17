import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from audit_core import clear_audit_events
from app.main import app
from app.services.artifact_service import clear_artifacts


def main() -> None:
    args = _parse_args()

    workflow_id = args.workflow_id
    output_dir = Path(args.output_dir or f"examples/{workflow_id}_outputs")
    approval_reference = args.approval_reference or f"approval_example_export_{workflow_id}_001"

    output_dir.mkdir(parents=True, exist_ok=True)

    clear_artifacts()
    clear_audit_events()

    client = TestClient(app)

    print(f"Creating workflow run for: {workflow_id}")

    run_response = client.post(
        "/runs",
        json={"workflow_id": workflow_id},
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

    if not backlog_items:
        raise ValueError("No backlog items were generated.")

    selected_backlog_id = args.backlog_id or backlog_items[0]["backlog_id"]

    print(f"Approving backlog item in dry-run mode: {selected_backlog_id}")

    approval_response = client.post(
        f"/runs/{run_id}/backlog/{selected_backlog_id}/approve",
        json={
            "approved_by": "example_export_reviewer",
            "approval_reference": approval_reference,
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

    _write_json(output_dir, "run_response.json", run_data)
    _write_json(output_dir, "approval_response.json", approval_data)
    _write_json(output_dir, "artifacts.json", updated_artifacts)
    _write_json(output_dir, "audit_events.json", audit_events)
    _write_json(output_dir, "audit_summary.json", _build_audit_summary(audit_events))

    for artifact in updated_artifacts:
        artifact_type = artifact["artifact_type"]
        _write_json(output_dir, f"{artifact_type}.json", artifact)

    _write_readme(
        output_dir=output_dir,
        workflow_id=workflow_id,
        run_id=run_id,
        artifact_types=[artifact["artifact_type"] for artifact in updated_artifacts],
        selected_backlog_id=selected_backlog_id,
        audit_event_count=len(audit_events),
    )

    print(f"Example outputs written to: {output_dir}")
    print("Done.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export example governed workflow outputs.",
    )

    parser.add_argument(
        "--workflow-id",
        default="payment_reconciliation",
        help="Workflow ID to run and export.",
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where example outputs should be written.",
    )

    parser.add_argument(
        "--backlog-id",
        default=None,
        help="Specific backlog item to approve. Defaults to the first generated backlog item.",
    )

    parser.add_argument(
        "--approval-reference",
        default=None,
        help="Approval reference to include in the dry-run approval.",
    )

    return parser.parse_args()


def _find_artifact(
    artifacts: list[dict[str, Any]],
    artifact_type: str,
) -> dict[str, Any]:
    for artifact in artifacts:
        if artifact["artifact_type"] == artifact_type:
            return artifact

    raise ValueError(f"Artifact not found: {artifact_type}")


def _write_json(output_dir: Path, filename: str, data: Any) -> None:
    path = output_dir / filename

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
    output_dir: Path,
    workflow_id: str,
    run_id: str,
    artifact_types: list[str],
    selected_backlog_id: str,
    audit_event_count: int,
) -> None:
    artifact_lines = "\n".join(f"- `{artifact_type}`" for artifact_type in artifact_types)

    content = "\n".join(
        [
            f"# {workflow_id} Example Outputs",
            "",
            "This folder contains example output from the AgentOps Readiness Console.",
            "",
            "## Workflow",
            "",
            "```text",
            workflow_id,
            "```",
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

    (output_dir / "README.md").write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()