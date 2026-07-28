import argparse
import json
from datetime import UTC, datetime
from typing import Any

from audit_core import AuditEventType
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact
from app.services.audit_service import log_audit_event


_SECTIONS_REQUIRING_EVIDENCE = [
    "key_process_observations",
    "data_sensitivity_observations",
    "risk_observations",
    "control_recommendations",
    "hitl_recommendations",
    "implementation_recommendations",
]


def main() -> None:
    args = _parse_args()
    client = TestClient(app)

    print(f"\n1. Evaluating evidence grounding for run: {args.run_id}")

    artifacts = _get_artifacts(client=client, run_id=args.run_id)
    llm_artifact = _find_latest_llm_artifact(artifacts=artifacts)

    if llm_artifact is None:
        raise AssertionError(
            f"No {ArtifactType.llm_workflow_analysis.value} artifact found "
            f"for run_id={args.run_id}."
        )

    analysis = llm_artifact["content"]
    llm_artifact_id = llm_artifact["artifact_id"]

    print(f"- llm_artifact_id: {llm_artifact_id}")

    evaluation = evaluate_evidence_grounding(
        run_id=args.run_id,
        workflow_id=args.workflow_id,
        llm_artifact_id=llm_artifact_id,
        analysis=analysis,
    )

    print("\nEvidence grounding results:")

    for check in evaluation["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(
            f"- {status}: {check['name']} "
            f"({check['earned_points']}/{check['max_points']})"
        )
        print(f"  {check['details']}")

    print(
        f"\nScore: {evaluation['score']}/{evaluation['max_score']} "
        f"(minimum={evaluation['minimum_score']})"
    )
    print(f"Passed: {evaluation['passed']}")

    if not args.skip_persist:
        print("\nPersisting evidence grounding evaluation artifact...")

        log_audit_event(
            run_id=args.run_id,
            event_type=AuditEventType.agent_started,
            actor="evidence_grounding_evaluator",
            details={
                "workflow_id": args.workflow_id,
                "llm_artifact_id": llm_artifact_id,
            },
        )

        artifact = create_artifact(
            run_id=args.run_id,
            artifact_type=ArtifactType.evidence_grounding_evaluation,
            content=evaluation,
        )

        log_audit_event(
            run_id=args.run_id,
            event_type=AuditEventType.agent_completed,
            actor="evidence_grounding_evaluator",
            details={
                "workflow_id": args.workflow_id,
                "llm_artifact_id": llm_artifact_id,
                "evaluation_artifact_id": artifact.artifact_id,
                "score": evaluation["score"],
                "passed": evaluation["passed"],
            },
        )

        print(f"- evaluation_artifact_id: {artifact.artifact_id}")

    if args.print_json:
        print("\nFull evidence grounding evaluation artifact:")
        print(json.dumps(evaluation, indent=2))

    if not evaluation["passed"]:
        raise AssertionError(
            f"Evidence grounding score {evaluation['score']} "
            f"is below required threshold {evaluation['minimum_score']}."
        )

    print("\nPASS: Evidence grounding evaluation completed successfully.")


def evaluate_evidence_grounding(
    run_id: str,
    workflow_id: str,
    llm_artifact_id: str,
    analysis: dict[str, Any],
) -> dict[str, Any]:
    metadata = analysis.get("metadata", {})
    evidence_index = metadata.get("evidence_catalog_index", [])

    valid_evidence_ids = {
        str(item.get("evidence_id"))
        for item in evidence_index
        if item.get("evidence_id")
    }

    checks = [
        _check_evidence_index_present(evidence_index=evidence_index),
        _check_evidence_index_is_lightweight(evidence_index=evidence_index),
        _check_section_reference_coverage(analysis=analysis),
        _check_all_references_are_valid(
            analysis=analysis,
            valid_evidence_ids=valid_evidence_ids,
        ),
        _check_reference_diversity(
            analysis=analysis,
            evidence_index=evidence_index,
        ),
        _check_high_value_sections_are_grounded(analysis=analysis),
        _check_workflow_scope(
            workflow_id=workflow_id,
            evidence_index=evidence_index,
        ),
    ]

    score = sum(check["earned_points"] for check in checks)
    max_score = sum(check["max_points"] for check in checks)
    minimum_score = 85

    return {
        "evaluation_type": "evidence_grounding",
        "workflow_id": workflow_id,
        "run_id": run_id,
        "llm_artifact_id": llm_artifact_id,
        "analysis_mode": metadata.get("analysis_mode"),
        "evidence_item_count": len(evidence_index),
        "score": score,
        "max_score": max_score,
        "minimum_score": minimum_score,
        "passed": score >= minimum_score,
        "checks": checks,
        "created_at": datetime.now(UTC).isoformat(),
        "evaluation_note": (
            "This evaluation checks whether the LLM analysis includes valid evidence "
            "references tied to the MCP-retrieved evidence catalog. It complements "
            "the output-quality and MCP-operational evaluations."
        ),
    }


def _check_evidence_index_present(
    evidence_index: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_ids = [
        item.get("evidence_id")
        for item in evidence_index
        if item.get("evidence_id")
    ]

    passed = len(evidence_ids) >= 5

    return _result(
        name="Evidence catalog index is present",
        passed=passed,
        earned_points=15 if passed else 0,
        max_points=15,
        details=f"evidence_item_count={len(evidence_index)}, evidence_id_count={len(evidence_ids)}",
    )


def _check_evidence_index_is_lightweight(
    evidence_index: list[dict[str, Any]],
) -> dict[str, Any]:
    entries_with_full_content = [
        item.get("evidence_id")
        for item in evidence_index
        if "content" in item
    ]

    entries_missing_summary = [
        item.get("evidence_id")
        for item in evidence_index
        if not item.get("summary")
    ]

    passed = not entries_with_full_content and len(entries_missing_summary) <= 2

    return _result(
        name="Evidence index is lightweight and reviewable",
        passed=passed,
        earned_points=10 if passed else 5,
        max_points=10,
        details=(
            f"entries_with_full_content={entries_with_full_content}, "
            f"entries_missing_summary={entries_missing_summary}"
        ),
    )


def _check_section_reference_coverage(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    total_items = 0
    referenced_items = 0
    section_counts = {}

    for section in _SECTIONS_REQUIRING_EVIDENCE:
        items = analysis.get(section, [])

        section_total = 0
        section_referenced = 0

        for item in items:
            if not isinstance(item, dict):
                continue

            section_total += 1
            total_items += 1

            refs = _normalize_references(item.get("evidence_references", []))

            if refs:
                section_referenced += 1
                referenced_items += 1

        section_counts[section] = {
            "total": section_total,
            "referenced": section_referenced,
        }

    coverage = referenced_items / total_items if total_items else 0
    passed = coverage >= 0.85

    if coverage >= 0.95:
        earned = 20
    elif coverage >= 0.85:
        earned = 17
    elif coverage >= 0.70:
        earned = 12
    else:
        earned = 0

    return _result(
        name="Major analysis sections include evidence references",
        passed=passed,
        earned_points=earned,
        max_points=20,
        details=(
            f"referenced_items={referenced_items}, total_items={total_items}, "
            f"coverage={coverage:.2f}, section_counts={section_counts}"
        ),
    )


def _check_all_references_are_valid(
    analysis: dict[str, Any],
    valid_evidence_ids: set[str],
) -> dict[str, Any]:
    observed_refs = _all_observed_references(analysis)

    invalid_refs = sorted(
        ref
        for ref in observed_refs
        if ref not in valid_evidence_ids
    )

    passed = bool(observed_refs) and not invalid_refs

    return _result(
        name="All evidence references resolve to the evidence catalog",
        passed=passed,
        earned_points=20 if passed else 0,
        max_points=20,
        details=(
            f"observed_reference_count={len(observed_refs)}, "
            f"valid_evidence_id_count={len(valid_evidence_ids)}, "
            f"invalid_refs={invalid_refs}"
        ),
    )


def _check_reference_diversity(
    analysis: dict[str, Any],
    evidence_index: list[dict[str, Any]],
) -> dict[str, Any]:
    observed_refs = _all_observed_references(analysis)

    evidence_type_by_id = {
        item.get("evidence_id"): item.get("evidence_type")
        for item in evidence_index
    }

    observed_types = sorted(
        {
            evidence_type_by_id.get(ref)
            for ref in observed_refs
            if evidence_type_by_id.get(ref)
        }
    )

    has_document = "workflow_document" in observed_types
    has_search = "document_search_result" in observed_types
    has_policy = (
        "data_classification_batch" in observed_types
        or "required_controls_batch" in observed_types
    )

    earned = 0
    earned += 5 if has_document else 0
    earned += 5 if has_search else 0
    earned += 5 if has_policy else 0

    passed = earned >= 10

    return _result(
        name="Evidence references use multiple evidence types",
        passed=passed,
        earned_points=earned,
        max_points=15,
        details=f"observed_evidence_types={observed_types}",
    )


def _check_high_value_sections_are_grounded(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    section_thresholds = {
        "risk_observations": 0.90,
        "control_recommendations": 0.80,
        "hitl_recommendations": 0.80,
        "implementation_recommendations": 0.80,
    }

    section_results = {}
    earned = 0

    for section, threshold in section_thresholds.items():
        items = [
            item
            for item in analysis.get(section, [])
            if isinstance(item, dict)
        ]

        referenced = [
            item
            for item in items
            if _normalize_references(item.get("evidence_references", []))
        ]

        coverage = len(referenced) / len(items) if items else 0
        passed_section = coverage >= threshold

        section_results[section] = {
            "total": len(items),
            "referenced": len(referenced),
            "coverage": round(coverage, 2),
            "threshold": threshold,
            "passed": passed_section,
        }

        earned += 5 if passed_section else 0

    passed = earned >= 15

    return _result(
        name="High-value sections are evidence-grounded",
        passed=passed,
        earned_points=earned,
        max_points=20,
        details=f"section_results={section_results}",
    )


def _check_workflow_scope(
    workflow_id: str,
    evidence_index: list[dict[str, Any]],
) -> dict[str, Any]:
    mismatches = [
        {
            "evidence_id": item.get("evidence_id"),
            "workflow_id": item.get("workflow_id"),
        }
        for item in evidence_index
        if item.get("workflow_id") and item.get("workflow_id") != workflow_id
    ]

    passed = not mismatches

    return _result(
        name="Evidence catalog stays within workflow scope",
        passed=passed,
        earned_points=10 if passed else 0,
        max_points=10,
        details=f"workflow_id={workflow_id}, mismatches={mismatches}",
    )


def _all_observed_references(
    analysis: dict[str, Any],
) -> set[str]:
    refs = set()

    for section in _SECTIONS_REQUIRING_EVIDENCE:
        for item in analysis.get(section, []):
            if isinstance(item, dict):
                refs.update(_normalize_references(item.get("evidence_references", [])))

    return refs


def _normalize_references(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        candidates = value.replace(";", ",").split(",")
        return [
            candidate.strip()
            for candidate in candidates
            if candidate.strip()
        ]

    if isinstance(value, list):
        refs = []

        for item in value:
            if isinstance(item, str):
                refs.extend(_normalize_references(item))

        return refs

    return []


def _get_artifacts(
    client: TestClient,
    run_id: str,
) -> list[dict[str, Any]]:
    response = client.get(f"/runs/{run_id}/artifacts")
    assert response.status_code == 200, response.text
    return response.json()


def _find_latest_llm_artifact(
    artifacts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    matching_artifacts = [
        artifact
        for artifact in artifacts
        if artifact["artifact_type"] == ArtifactType.llm_workflow_analysis.value
    ]

    if not matching_artifacts:
        return None

    return matching_artifacts[-1]


def _result(
    name: str,
    passed: bool,
    earned_points: int,
    max_points: int,
    details: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "earned_points": earned_points,
        "max_points": max_points,
        "details": details,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate evidence grounding for an LLM shadow artifact."
    )

    parser.add_argument(
        "--workflow-id",
        default="access_request_review",
    )

    parser.add_argument(
        "--run-id",
        required=True,
    )

    parser.add_argument(
        "--skip-persist",
        action="store_true",
    )

    parser.add_argument(
        "--print-json",
        action="store_true",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()