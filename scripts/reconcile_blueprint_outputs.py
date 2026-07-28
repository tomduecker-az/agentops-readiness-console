from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact
from readiness_core import (
    reconcile_blueprint_with_llm_proposal,
    validate_blueprint_safety,
    validation_passed,
)
from audit_core.models import AuditEventType
from app.services.audit_service import log_audit_event


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconcile deterministic blueprint with LLM Blueprint Advisor proposal."
    )
    parser.add_argument("--baseline-path", required=True)
    parser.add_argument("--proposal-path", required=True)
    parser.add_argument("--comparison-path")
    parser.add_argument("--export-json", action="store_true")
    parser.add_argument("--persist", action="store_true")

    args = parser.parse_args()

    baseline_path = Path(args.baseline_path)
    proposal_path = Path(args.proposal_path)
    comparison_path = Path(args.comparison_path) if args.comparison_path else None

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    comparison = (
        json.loads(comparison_path.read_text(encoding="utf-8"))
        if comparison_path
        else None
    )

    blueprint, reconciliation_report = reconcile_blueprint_with_llm_proposal(
        baseline_blueprint=baseline,
        llm_proposal=proposal,
        comparison=comparison,
    )

    validation_issues = validate_blueprint_safety(blueprint)
    validation_payload = [asdict(issue) for issue in validation_issues]
    validation_succeeded = validation_passed(validation_issues)

    blueprint.metadata["blueprint_safety_validation"] = {
        "passed": validation_succeeded,
        "issue_count": len(validation_issues),
        "issues": validation_payload,
    }

    blueprint_content = blueprint.model_dump(mode="json")

    print("Reconciled Blueprint")
    print(f"- workflow_id: {blueprint.workflow_id}")
    print(f"- run_id: {blueprint.run_id}")
    print(f"- recommendation: {blueprint.executive_summary.recommendation.value}")
    print(f"- autonomy_rows: {len(blueprint.step_level_autonomy_matrix)}")
    print(f"- tool_capabilities: {len(blueprint.tooling_blueprint)}")
    print(f"- approval_gates: {len(blueprint.human_approval_gates)}")
    print(f"- safety_overrides: {len(reconciliation_report['safety_overrides'])}")
    print(f"- review_items: {len(reconciliation_report['review_items'])}")
    print(f"- validation_passed: {validation_succeeded}")
    print(f"- validation_issue_count: {len(validation_issues)}")

    log_audit_event(
        run_id=blueprint.run_id,
        event_type=AuditEventType.agent_completed,
        actor="blueprint_reconciler",
        details={
            "workflow_id": blueprint.workflow_id,
            "generation_mode": "llm_assisted_with_deterministic_validation",
            "validation_passed": validation_succeeded,
            "validation_issue_count": len(validation_issues),
            "safety_overrides": len(reconciliation_report["safety_overrides"]),
            "review_items": len(reconciliation_report["review_items"]),
            "persist_requested": args.persist,
        },
    )

    if validation_issues:
        print("\nValidation Issues")
        for issue in validation_issues:
            print(f"- {issue.severity} {issue.code} {issue.location}: {issue.message}")

    if not validation_succeeded:
        raise AssertionError("Reconciled blueprint failed safety validation.")

    if args.export_json:
        output_path = _write_export(blueprint_content)
        print(f"- json_export_path: {output_path}")

    artifact_id = None

    if args.persist:
        artifact = create_artifact(
            run_id=blueprint.run_id,
            artifact_type=ArtifactType.agentic_readiness_blueprint,
            content=blueprint_content,
        )
        log_audit_event(
            run_id=blueprint.run_id,
            event_type=AuditEventType.write_action_executed,
            actor="blueprint_reconciler",
            details={
                "workflow_id": blueprint.workflow_id,
                "artifact_id": artifact.artifact_id,
                "artifact_type": ArtifactType.agentic_readiness_blueprint.value,
                "generation_mode": "llm_assisted_with_deterministic_validation",
                "action": "persist_reconciled_blueprint",
            },
        )
        artifact_id = artifact.artifact_id
        print(f"- artifact_id: {artifact_id}")


def _write_export(blueprint_content: dict[str, Any]) -> Path:
    output_dir = Path("examples/reconciled_blueprints")
    output_dir.mkdir(parents=True, exist_ok=True)

    workflow_id = blueprint_content["workflow_id"]
    run_id = blueprint_content["run_id"]

    output_path = output_dir / f"{workflow_id}_{run_id}_reconciled_blueprint.json"
    output_path.write_text(
        json.dumps(blueprint_content, indent=2),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    main()