from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_core.models import AuditEventType

from app.llm.opportunity_diagnostic_advisor import generate_workflow_ai_opportunity_diagnostic
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact, get_artifacts_for_run
from app.services.audit_service import log_audit_event
from workflow_core import list_documents, read_document
from dataclasses import asdict
from readiness_core import evaluate_diagnostic_quality, quality_passed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Workflow AI Opportunity Diagnostic from a reconciled readiness blueprint."
    )
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--reconciled-blueprint-path", required=True)
    parser.add_argument("--export-json", action="store_true")
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument(
        "--export-quality-json",
        action="store_true",
        help="Export a diagnostic quality evaluation JSON file.",
    )
    parser.add_argument(
        "--require-quality-pass",
        action="store_true",
        help="Fail the command if the diagnostic quality gate has errors.",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Treat diagnostic quality warnings as command failures.",
    )

    args = parser.parse_args()

    print("1. Generating Workflow AI Opportunity Diagnostic...")
    print(f"- workflow_id: {args.workflow_id}")
    print(f"- run_id: {args.run_id}")
    print(f"- reconciled_blueprint_path: {args.reconciled_blueprint_path}")
    print("- mode: llm_generated_opportunity_diagnostic")

    reconciled_blueprint_path = Path(args.reconciled_blueprint_path)
    reconciled_blueprint = json.loads(
        reconciled_blueprint_path.read_text(encoding="utf-8")
    )

    artifacts_by_type = _load_artifacts_by_type(run_id=args.run_id)
    workflow_documents = _load_workflow_documents(workflow_id=args.workflow_id)

    log_audit_event(
        run_id=args.run_id,
        event_type=AuditEventType.agent_started,
        actor="opportunity_diagnostic_advisor",
        details={
            "workflow_id": args.workflow_id,
            "generation_mode": "llm_generated_opportunity_diagnostic",
            "reconciled_blueprint_path": str(reconciled_blueprint_path),
        },
    )

    diagnostic = generate_workflow_ai_opportunity_diagnostic(
        workflow_id=args.workflow_id,
        run_id=args.run_id,
        workflow_documents=workflow_documents,
        artifacts_by_type=artifacts_by_type,
        reconciled_blueprint=reconciled_blueprint,
    )

    diagnostic_content = diagnostic.model_dump(mode="json")

    quality_issues = evaluate_diagnostic_quality(diagnostic_content)
    quality_errors = [issue for issue in quality_issues if issue.severity == "error"]
    quality_warnings = [issue for issue in quality_issues if issue.severity == "warning"]

    quality_evaluation = {
        "workflow_id": args.workflow_id,
        "run_id": args.run_id,
        "diagnostic_version": diagnostic_content.get("diagnostic_version"),
        "quality_passed": quality_passed(quality_issues),
        "error_count": len(quality_errors),
        "warning_count": len(quality_warnings),
        "issues": [asdict(issue) for issue in quality_issues],
    }

    diagnostic_content.setdefault("metadata", {})
    diagnostic_content["metadata"]["diagnostic_quality_evaluation"] = quality_evaluation

    artifact_id = None

    if args.persist and not quality_passed(quality_issues):
        raise SystemExit(
            "Diagnostic quality gate failed. Refusing to persist workflow_ai_opportunity_diagnostic."
        )

    if args.persist:
        artifact = create_artifact(
            run_id=args.run_id,
            artifact_type=ArtifactType.workflow_ai_opportunity_diagnostic,
            content=diagnostic_content,
        )
        artifact_id = artifact.artifact_id

    if args.require_quality_pass and not quality_passed(quality_issues):
        raise SystemExit("Diagnostic quality gate failed.")

    if args.warnings_as_errors and quality_warnings:
        raise SystemExit("Diagnostic quality gate produced warnings.")

    log_audit_event(
        run_id=args.run_id,
        event_type=AuditEventType.agent_completed,
        actor="opportunity_diagnostic_advisor",
        details={
            "workflow_id": args.workflow_id,
            "artifact_id": artifact_id,
            "generation_mode": "llm_generated_opportunity_diagnostic",
            "persisted": args.persist,
            "automation_ceiling": diagnostic.automation_ceiling.current_ceiling.value,
            "blocker_count": len(diagnostic.top_readiness_blockers),
            "avoid_count": len(diagnostic.use_cases_to_avoid),
            "redesign_requirement_count": len(diagnostic.process_redesign_requirements),
            "value_hypothesis_count": len(diagnostic.value_hypotheses),
        },
    )

    print("\n2. Workflow AI Opportunity Diagnostic generated")
    print(f"- artifact_id: {artifact_id}")
    print(f"- automation_ceiling: {diagnostic.automation_ceiling.current_ceiling.value}")
    print(f"- recommended_first_use_case: {diagnostic.recommended_first_use_case.title}")
    print(f"- blockers: {len(diagnostic.top_readiness_blockers)}")
    print(f"- use_cases_to_avoid: {len(diagnostic.use_cases_to_avoid)}")
    print(f"- process_redesign_requirements: {len(diagnostic.process_redesign_requirements)}")
    print(f"- control_gaps: {len(diagnostic.control_gap_remediation_plan)}")
    print(f"- value_hypotheses: {len(diagnostic.value_hypotheses)}")
    print(f"- measurement_plan_items: {len(diagnostic.measurement_plan)}")
    print(f"- sample_record_findings: {len(diagnostic.sample_record_opportunity_analysis)}")
    print(f"- workflow_owner_questions: {len(diagnostic.questions_for_workflow_owner)}")
    print(f"- quality_passed: {quality_evaluation['quality_passed']}")
    print(f"- quality_errors: {quality_evaluation['error_count']}")
    print(f"- quality_warnings: {quality_evaluation['warning_count']}")

    if quality_issues:
        print("\nQuality issues:")
        for issue in quality_issues:
            print(
                f"- {issue.severity.upper()} | {issue.code} | "
                f"{issue.location} | {issue.message}"
            )

    if args.export_json:
        output_path = _write_json_export(
            workflow_id=args.workflow_id,
            run_id=args.run_id,
            diagnostic=diagnostic_content,
        )
        print(f"- json_export_path: {output_path}")

    if args.export_quality_json:
        quality_output_path = _write_quality_json_export(
            workflow_id=args.workflow_id,
            run_id=args.run_id,
            quality_evaluation=quality_evaluation,
        )
        print(f"- quality_json_export_path: {quality_output_path}")

    if args.print_json:
        print("\nFull diagnostic:")
        print(json.dumps(diagnostic_content, indent=2))


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

def _write_quality_json_export(
    *,
    workflow_id: str,
    run_id: str,
    quality_evaluation: dict[str, Any],
) -> Path:
    output_dir = Path("examples/opportunity_diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{workflow_id}_{run_id}_opportunity_diagnostic_quality.json"
    output_path.write_text(
        json.dumps(quality_evaluation, indent=2),
        encoding="utf-8",
    )

    return output_path


def _write_json_export(
    *,
    workflow_id: str,
    run_id: str,
    diagnostic: dict[str, Any],
) -> Path:
    output_dir = Path("examples/opportunity_diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{workflow_id}_{run_id}_opportunity_diagnostic.json"
    output_path.write_text(
        json.dumps(diagnostic, indent=2),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    main()