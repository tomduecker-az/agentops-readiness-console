from __future__ import annotations
from dataclasses import asdict
from typing import Any
from audit_core.models import AuditEventType
from readiness_core import (
    build_agentic_readiness_blueprint,
    validate_blueprint_safety,
    validation_passed,
)
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact, get_artifacts_for_run
from app.services.audit_service import log_audit_event
from workflow_core import list_documents, read_document



class BlueprintGenerationError(RuntimeError):
    pass


def generate_agentic_readiness_blueprint(
    *,
    run_id: str,
    workflow_id: str,
    persist: bool = True,
    audit_enabled: bool = True,
    artifacts_by_type: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Generate the primary Agentic Readiness Blueprint for a completed run.

    This function does not call an LLM. It builds a deterministic product artifact
    from previously generated and evaluated analysis artifacts.
    """

    if audit_enabled:
        log_audit_event(
            run_id=run_id,
            event_type=AuditEventType.agent_started,
            actor="blueprint_service",
            details={
                "workflow_id": workflow_id,
                "agent": "agentic_readiness_blueprint_builder",
                "generation_mode": "deterministic_from_validated_artifacts",
            },
        )

    if artifacts_by_type is None:
        artifacts_by_type = _load_artifacts_by_type(run_id=run_id)

    _validate_required_artifacts(artifacts_by_type)

    workflow_documents = _load_workflow_documents(workflow_id=workflow_id)

    blueprint = build_agentic_readiness_blueprint(
        workflow_id=workflow_id,
        run_id=run_id,
        artifacts_by_type=artifacts_by_type,
        workflow_documents=workflow_documents,
    )

    validation_issues = validate_blueprint_safety(blueprint)
    validation_issue_payload = [asdict(issue) for issue in validation_issues]
    validation_succeeded = validation_passed(validation_issues)

    blueprint.metadata["blueprint_safety_validation"] = {
        "passed": validation_succeeded,
        "issue_count": len(validation_issues),
        "issues": validation_issue_payload,
    }

    blueprint_content = blueprint.model_dump(mode="json")

    if not validation_succeeded:
        if audit_enabled:
            log_audit_event(
                run_id=run_id,
                event_type=AuditEventType.policy_violation,
                actor="blueprint_service",
                details={
                    "workflow_id": workflow_id,
                    "agent": "agentic_readiness_blueprint_builder",
                    "reason": "blueprint_safety_validation_failed",
                    "issues": validation_issue_payload,
                    "blueprint_safety_validation_passed": validation_succeeded,
                    "blueprint_safety_validation_issue_count": len(validation_issues),
                },
            )

        if persist:
            raise BlueprintGenerationError(
                "Cannot persist Agentic Readiness Blueprint because safety validation failed."
            )

    artifact_id = None

    if persist:
        artifact = create_artifact(
            run_id=run_id,
            artifact_type=ArtifactType.agentic_readiness_blueprint,
            content=blueprint_content,
        )
        artifact_id = artifact.artifact_id

    if audit_enabled:
        log_audit_event(
            run_id=run_id,
            event_type=AuditEventType.agent_completed,
            actor="blueprint_service",
            details={
                "workflow_id": workflow_id,
                "agent": "agentic_readiness_blueprint_builder",
                "artifact_id": artifact_id,
                "recommendation": blueprint.executive_summary.recommendation.value,
                "overall_score": _get_overall_score(blueprint_content),
                "autonomy_rows": len(blueprint.step_level_autonomy_matrix),
                "tool_capabilities": len(blueprint.tooling_blueprint),
                "approval_gates": len(blueprint.human_approval_gates),
                "persisted": persist,
            },
        )

    return {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "artifact_id": artifact_id,
        "blueprint": blueprint_content,
    }


def _load_artifacts_by_type(*, run_id: str) -> dict[str, list[dict[str, Any]]]:
    artifacts = get_artifacts_for_run(run_id)

    artifacts_by_type: dict[str, list[dict[str, Any]]] = {}

    for artifact in artifacts:
        artifact_type = artifact.artifact_type.value
        artifacts_by_type.setdefault(artifact_type, [])
        artifacts_by_type[artifact_type].append(artifact.content)

    return artifacts_by_type


def _validate_required_artifacts(artifacts_by_type: dict[str, Any]) -> None:
    required_artifacts = [
        ArtifactType.llm_workflow_analysis.value,
        ArtifactType.llm_shadow_evaluation.value,
        ArtifactType.mcp_operational_evaluation.value,
        ArtifactType.evidence_grounding_evaluation.value,
    ]

    missing = [
        artifact_type
        for artifact_type in required_artifacts
        if artifact_type not in artifacts_by_type
    ]

    if missing:
        raise BlueprintGenerationError(
            "Cannot generate Agentic Readiness Blueprint. "
            f"Missing required artifacts: {', '.join(missing)}"
        )


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


def _get_overall_score(blueprint_content: dict[str, Any]) -> int | None:
    for score in blueprint_content.get("readiness_scorecard", []):
        if score.get("dimension") == "overall_readiness":
            return score.get("score")

    return None