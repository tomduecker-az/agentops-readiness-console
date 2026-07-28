from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_core.models import AuditEventType

from app.llm.blueprint_advisor import generate_llm_blueprint_proposal
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact, get_artifacts_for_run
from app.services.audit_service import log_audit_event
from workflow_core import list_documents, read_document


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the LLM Blueprint Advisor proposal for a completed workflow analysis run."
    )
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--export-json", action="store_true")
    parser.add_argument("--persist-proposal", action="store_true")

    args = parser.parse_args()

    print("1. Running LLM Blueprint Advisor proposal...")
    print(f"- workflow_id: {args.workflow_id}")
    print(f"- run_id: {args.run_id}")
    print("- mode: llm_assisted_proposal_only")

    log_audit_event(
        run_id=args.run_id,
        event_type=AuditEventType.agent_started,
        actor="llm_blueprint_advisor",
        details={
            "workflow_id": args.workflow_id,
            "generation_mode": "llm_assisted_proposal_only",
        },
    )

    artifacts_by_type = _load_artifacts_by_type(run_id=args.run_id)
    workflow_documents = _load_workflow_documents(workflow_id=args.workflow_id)
    deterministic_blueprint = _latest_artifact_content(
        artifacts_by_type,
        ArtifactType.agentic_readiness_blueprint.value,
    )

    proposal = generate_llm_blueprint_proposal(
        workflow_id=args.workflow_id,
        run_id=args.run_id,
        artifacts_by_type=artifacts_by_type,
        workflow_documents=workflow_documents,
        deterministic_blueprint=deterministic_blueprint,
    )

    artifact_id = None

    if args.persist_proposal:
        artifact = create_artifact(
            run_id=args.run_id,
            artifact_type=ArtifactType.llm_blueprint_proposal,
            content=proposal,
        )
        artifact_id = artifact.artifact_id

    log_audit_event(
        run_id=args.run_id,
        event_type=AuditEventType.agent_completed,
        actor="llm_blueprint_advisor",
        details={
            "workflow_id": args.workflow_id,
            "artifact_id": artifact_id,
            "generation_mode": "llm_assisted_proposal_only",
            "persisted": args.persist_proposal,
            "autonomy_rows": len(proposal.get("step_level_autonomy_matrix", [])),
            "tool_capabilities": len(proposal.get("tooling_blueprint", [])),
            "approval_gates": len(proposal.get("human_approval_gates", [])),
        },
    )

    print("\n2. LLM Blueprint Advisor proposal generated")
    print(f"- artifact_id: {artifact_id}")
    print(f"- recommendation: {proposal['executive_summary']['recommendation']}")
    print(f"- autonomy_rows: {len(proposal['step_level_autonomy_matrix'])}")
    print(f"- tool_capabilities: {len(proposal['tooling_blueprint'])}")
    print(f"- approval_gates: {len(proposal['human_approval_gates'])}")
    print(f"- limitations: {len(proposal['limitations_and_missing_information'])}")

    if args.export_json:
        output_path = _write_json_export(
            workflow_id=args.workflow_id,
            run_id=args.run_id,
            proposal=proposal,
        )
        print(f"- json_export_path: {output_path}")

    if args.print_json:
        print("\nFull LLM Blueprint Advisor proposal:")
        print(json.dumps(proposal, indent=2))


def _load_artifacts_by_type(*, run_id: str) -> dict[str, list[dict[str, Any]]]:
    artifacts = get_artifacts_for_run(run_id)

    artifacts_by_type: dict[str, list[dict[str, Any]]] = {}

    for artifact in artifacts:
        artifact_type = artifact.artifact_type.value
        artifacts_by_type.setdefault(artifact_type, [])
        artifacts_by_type[artifact_type].append(artifact.content)

    return artifacts_by_type


def _load_workflow_documents(*, workflow_id: str) -> list[dict[str, Any]]:
    documents = list_documents(workflow_id)

    loaded_documents: list[dict[str, Any]] = []

    for document in documents:
        document_content = read_document(
            workflow_id=workflow_id,
            document_id=document.document_id,
        )

        loaded_documents.append(
            {
                "document_id": document_content.document_id,
                "title": document_content.title,
                "document_type": document_content.document_type,
                "content": document_content.content,
            }
        )

    return loaded_documents


def _latest_artifact_content(
    artifacts_by_type: dict[str, list[dict[str, Any]]],
    artifact_type: str,
) -> dict[str, Any] | None:
    artifacts = artifacts_by_type.get(artifact_type, [])

    if not artifacts:
        return None

    latest = artifacts[-1]

    if isinstance(latest, dict) and "content" in latest and isinstance(latest["content"], dict):
        return latest["content"]

    if isinstance(latest, dict):
        return latest

    return None


def _write_json_export(
    *,
    workflow_id: str,
    run_id: str,
    proposal: dict[str, Any],
) -> Path:
    output_dir = Path("examples/blueprint_proposals")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{workflow_id}_{run_id}_llm_blueprint_proposal.json"
    output_path.write_text(
        json.dumps(proposal, indent=2),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    main()