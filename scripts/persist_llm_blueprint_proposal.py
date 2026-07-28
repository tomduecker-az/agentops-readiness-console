from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_core.models import AuditEventType

from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact
from app.services.audit_service import log_audit_event
from scripts.check_llm_blueprint_proposal import _validate_proposal


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Persist a previously exported LLM Blueprint Advisor proposal without rerunning the model."
    )
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--path", required=True)

    args = parser.parse_args()

    path = Path(args.path)
    proposal = json.loads(path.read_text(encoding="utf-8"))

    issues = _validate_proposal(proposal)
    errors = [issue for issue in issues if issue["severity"] == "error"]

    print("1. Validating existing LLM Blueprint Advisor proposal...")
    print(f"- workflow_id: {args.workflow_id}")
    print(f"- run_id: {args.run_id}")
    print(f"- path: {path}")
    print(f"- issue_count: {len(issues)}")
    print(f"- error_count: {len(errors)}")

    if errors:
        for error in errors:
            print(
                f"- ERROR {error['code']} {error['location']}: {error['message']}"
            )
        raise AssertionError("Cannot persist proposal with validation errors.")

    proposal.setdefault("metadata", {})
    proposal["metadata"]["persisted_from_export"] = True
    proposal["metadata"]["source_export_path"] = str(path)
    proposal["metadata"]["proposal_validation"] = {
        "passed": True,
        "issue_count": len(issues),
        "issues": issues,
    }

    log_audit_event(
        run_id=args.run_id,
        event_type=AuditEventType.agent_started,
        actor="llm_blueprint_advisor",
        details={
            "workflow_id": args.workflow_id,
            "action": "persist_existing_llm_blueprint_proposal",
            "source_export_path": str(path),
        },
    )

    artifact = create_artifact(
        run_id=args.run_id,
        artifact_type=ArtifactType.llm_blueprint_proposal,
        content=proposal,
    )

    log_audit_event(
        run_id=args.run_id,
        event_type=AuditEventType.agent_completed,
        actor="llm_blueprint_advisor",
        details={
            "workflow_id": args.workflow_id,
            "action": "persist_existing_llm_blueprint_proposal",
            "artifact_id": artifact.artifact_id,
            "source_export_path": str(path),
            "validation_issue_count": len(issues),
            "autonomy_rows": len(proposal.get("step_level_autonomy_matrix", [])),
            "tool_capabilities": len(proposal.get("tooling_blueprint", [])),
            "approval_gates": len(proposal.get("human_approval_gates", [])),
        },
    )

    print("\n2. LLM Blueprint Advisor proposal persisted")
    print(f"- artifact_id: {artifact.artifact_id}")
    print(f"- recommendation: {proposal['executive_summary']['recommendation']}")
    print(f"- autonomy_rows: {len(proposal['step_level_autonomy_matrix'])}")
    print(f"- tool_capabilities: {len(proposal['tooling_blueprint'])}")
    print(f"- approval_gates: {len(proposal['human_approval_gates'])}")


if __name__ == "__main__":
    main()