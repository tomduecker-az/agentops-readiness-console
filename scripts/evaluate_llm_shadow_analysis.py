import argparse
import json
from datetime import UTC, datetime
from typing import Any
from audit_core import AuditEventType
from fastapi.testclient import TestClient
from app.llm.shadow_analysis import run_llm_shadow_analysis
from app.main import app
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact
from app.services.audit_service import log_audit_event
from pathlib import Path
from scripts.local_artifacts import load_local_artifacts, write_local_artifact


EVALUATION_PROFILES = {
    "access_request_review": {
        "minimum_score": 80,
        "required_sections": {
            "workflow_summary",
            "key_process_observations",
            "data_sensitivity_observations",
            "risk_observations",
            "control_recommendations",
            "hitl_recommendations",
            "implementation_recommendations",
            "missing_information",
            "grounding_notes",
            "hallucination_risk_notes",
            "confidence_by_section",
            "metadata",
        },
        "workflow_specificity_groups": [
            ["access request", "system access", "requested system", "identity"],
            ["employee", "manager", "hr source", "employment status"],
            ["application owner", "security reviewer", "security review"],
            ["provisioning", "identity provider", "target systems"],
            ["approval evidence", "audit evidence", "reviewer information"],
            ["sla", "deadline", "escalation", "weekly access review"],
        ],
        "risk_theme_groups": [
            ["unauthorized access", "provisioning", "write action", "approval"],
            ["routing", "classification", "privileged", "sensitive", "custom"],
            ["identity", "employee", "manager", "hr verification"],
            ["audit", "evidence", "reviewer", "integrity"],
            ["data protection", "sensitive employee", "security details", "model inputs"],
            ["sla", "deadline", "escalation"],
        ],
        "missing_information_groups": [
            ["routing matrix", "approval and routing matrix", "review sequence"],
            ["evidence format", "evidence formats", "retention", "storage location"],
            ["sla duration", "approaching the deadline", "pause conditions"],
            ["ai data use", "prompt", "output retention", "model"],
            ["hr source", "freshness", "authorization model"],
            ["sample records", "completed provisioning", "rejection", "audit evidence"],
        ],
        "governance_control_groups": [
            ["human approval", "human reviewer", "human-approved"],
            ["write", "provisioning", "record update", "ticket status"],
            ["read-only", "advisory", "recommendation"],
            ["data minimization", "access restriction", "retention", "redaction"],
            ["audit", "evidence", "reviewer information"],
        ],
        "prohibited_terms": {
            "payment reconciliation",
            "approval-threshold exception",
            "threshold exception",
            "customer onboarding",
            "high-risk onboarding",
            "onboarding plan",
            "financial handling",
            "payment exception",
        },
    }
}


def main() -> None:
    args = _parse_args()
    if args.artifacts_dir and not args.run_id:
        raise ValueError("--run-id is required when --artifacts-dir is provided.")

    profile_id = args.evaluation_profile_id or args.workflow_id

    if profile_id not in EVALUATION_PROFILES:
        available_profiles = ", ".join(sorted(EVALUATION_PROFILES))
        raise ValueError(
            f"No LLM shadow evaluation profile configured for '{profile_id}'. "
            f"Use --evaluation-profile-id with one of: {available_profiles}"
        )

    profile = EVALUATION_PROFILES[profile_id]
    client = TestClient(app)

    if args.run_id:
        run_id = args.run_id
        print(f"\n1. Evaluating existing run: {run_id}")

        if args.artifacts_dir:
            artifacts = load_local_artifacts(Path(args.artifacts_dir))
        else:
            artifacts = _get_artifacts(client=client, run_id=run_id)
        llm_artifact = _find_artifact(
            artifacts=artifacts,
            artifact_type=ArtifactType.llm_workflow_analysis.value,
        )

        if llm_artifact is None:
            raise AssertionError(
                f"No {ArtifactType.llm_workflow_analysis.value} artifact found "
                f"for run_id={run_id}."
            )

        analysis = llm_artifact["content"]
        llm_artifact_id = llm_artifact["artifact_id"]

    else:
        print(f"\n1. Creating governed baseline run for workflow: {args.workflow_id}")

        run_response = client.post(
            "/runs",
            json={"workflow_id": args.workflow_id},
        )
        assert run_response.status_code == 200, run_response.text

        run_data = run_response.json()
        run_id = run_data["run_id"]

        print(f"- run_id: {run_id}")
        print("\n2. Running LLM shadow analysis...")

        shadow_result = run_llm_shadow_analysis(
            run_id=run_id,
            workflow_id=args.workflow_id,
        )

        analysis = shadow_result["analysis"]
        llm_artifact_id = shadow_result["artifact_id"]

    print(f"- llm_artifact_id: {llm_artifact_id}")

    evaluation = evaluate_llm_shadow_analysis(
        run_id=run_id,
        workflow_id=args.workflow_id,
        llm_artifact_id=llm_artifact_id,
        analysis=analysis,
        profile=profile,
    )

    print("\nEvaluation results:")

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

    print(f"Model: {evaluation['model']}")
    print(f"Passed: {evaluation['passed']}")

    if args.artifacts_dir:
        print("\nWriting LLM shadow evaluation local artifact...")

        output_path = write_local_artifact(
            artifacts_dir=Path(args.artifacts_dir),
            artifact_type=ArtifactType.llm_shadow_evaluation.value,
            content=evaluation,
        )

        print(f"- local_artifact_path: {output_path}")

    elif not args.skip_persist:
        print("\nPersisting evaluation artifact...")

        log_audit_event(
            run_id=run_id,
            event_type=AuditEventType.agent_started,
            actor="llm_shadow_evaluator",
            details={
                "workflow_id": args.workflow_id,
                "llm_artifact_id": llm_artifact_id,
            },
        )

        artifact = create_artifact(
            run_id=run_id,
            artifact_type=ArtifactType.llm_shadow_evaluation,
            content=evaluation,
        )

        log_audit_event(
            run_id=run_id,
            event_type=AuditEventType.agent_completed,
            actor="llm_shadow_evaluator",
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
        print("\nFull evaluation artifact:")
        print(json.dumps(evaluation, indent=2))

    if not evaluation["passed"]:
        raise AssertionError(
            f"LLM shadow evaluation score {evaluation['score']} "
            f"is below required threshold {evaluation['minimum_score']}."
        )

    print("\nPASS: LLM shadow analysis evaluation completed successfully.")


def evaluate_llm_shadow_analysis(
    run_id: str,
    workflow_id: str,
    llm_artifact_id: str,
    analysis: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        _check_required_sections(
            analysis=analysis,
            required_sections=profile["required_sections"],
        ),
        _check_workflow_specificity(
            analysis=analysis,
            term_groups=profile["workflow_specificity_groups"],
        ),
        _check_risk_observations(
            analysis=analysis,
            term_groups=profile["risk_theme_groups"],
        ),
        _check_missing_information(
            analysis=analysis,
            term_groups=profile["missing_information_groups"],
        ),
        _check_grounding_and_hallucination_notes(analysis=analysis),
        _check_implementation_recommendations(analysis=analysis),
        _check_governance_controls(
            analysis=analysis,
            term_groups=profile["governance_control_groups"],
        ),
        _check_domain_leakage(
            analysis=analysis,
            prohibited_terms=profile["prohibited_terms"],
        ),
    ]

    score = sum(check["earned_points"] for check in checks)
    max_score = sum(check["max_points"] for check in checks)
    minimum_score = profile["minimum_score"]

    return {
        "evaluation_type": "llm_shadow_analysis",
        "workflow_id": workflow_id,
        "run_id": run_id,
        "llm_artifact_id": llm_artifact_id,
        "model": analysis.get("metadata", {}).get("model", "unknown"),
        "score": score,
        "max_score": max_score,
        "minimum_score": minimum_score,
        "passed": score >= minimum_score,
        "checks": checks,
        "created_at": datetime.now(UTC).isoformat(),
        "evaluation_note": (
            "This evaluation checks the advisory LLM shadow artifact for structure, "
            "workflow specificity, risk quality, missing-information analysis, grounding, "
            "governance boundaries, and domain leakage. It does not replace human review."
        ),
    }


def _check_required_sections(
    analysis: dict[str, Any],
    required_sections: set[str],
) -> dict[str, Any]:
    missing = sorted(
        section
        for section in required_sections
        if section not in analysis or _is_empty(analysis.get(section))
    )

    earned = 10 if not missing else max(0, 10 - len(missing) * 2)

    return _result(
        name="Required LLM artifact sections present",
        passed=not missing,
        earned_points=earned,
        max_points=10,
        details=f"missing_sections={missing}",
    )


def _check_workflow_specificity(
    analysis: dict[str, Any],
    term_groups: list[list[str]],
) -> dict[str, Any]:
    text = _json_text(analysis)
    matched = _matched_groups(text=text, term_groups=term_groups)

    earned = min(10, round((len(matched) / len(term_groups)) * 10))
    passed = earned >= 8

    return _result(
        name="Output is specific to the access-request workflow",
        passed=passed,
        earned_points=earned,
        max_points=10,
        details=f"matched_groups={matched}",
    )


def _check_risk_observations(
    analysis: dict[str, Any],
    term_groups: list[list[str]],
) -> dict[str, Any]:
    risks = analysis.get("risk_observations", [])
    risk_text = _json_text(risks)
    matched = _matched_groups(text=risk_text, term_groups=term_groups)

    high_risk_count = sum(
        1
        for risk in risks
        if str(risk.get("severity", "")).lower() == "high"
    )

    count_points = 5 if len(risks) >= 7 else max(0, len(risks))
    severity_points = 4 if high_risk_count >= 3 else high_risk_count
    theme_points = min(6, len(matched))

    earned = count_points + severity_points + theme_points
    passed = earned >= 12

    return _result(
        name="Risk observations are specific and useful",
        passed=passed,
        earned_points=earned,
        max_points=15,
        details=(
            f"risk_count={len(risks)}, "
            f"high_risk_count={high_risk_count}, "
            f"matched_theme_groups={matched}"
        ),
    )


def _check_missing_information(
    analysis: dict[str, Any],
    term_groups: list[list[str]],
) -> dict[str, Any]:
    missing_information = analysis.get("missing_information", [])
    text = _json_text(missing_information)
    matched = _matched_groups(text=text, term_groups=term_groups)

    count_points = 5 if len(missing_information) >= 8 else max(0, len(missing_information))
    theme_points = min(10, round((len(matched) / len(term_groups)) * 10))

    earned = count_points + theme_points
    passed = earned >= 12

    return _result(
        name="Missing-information analysis is substantive",
        passed=passed,
        earned_points=earned,
        max_points=15,
        details=(
            f"missing_information_count={len(missing_information)}, "
            f"matched_theme_groups={matched}"
        ),
    )


def _check_grounding_and_hallucination_notes(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    grounding_notes = analysis.get("grounding_notes", [])
    hallucination_notes = analysis.get("hallucination_risk_notes", [])

    combined_text = _json_text(
        {
            "grounding_notes": grounding_notes,
            "hallucination_risk_notes": hallucination_notes,
        }
    )

    grounding_points = 5 if len(grounding_notes) >= 4 else len(grounding_notes)
    hallucination_points = 5 if len(hallucination_notes) >= 4 else len(hallucination_notes)

    caution_terms = [
        "does not",
        "not specified",
        "not infer",
        "not establish",
        "not authorize",
        "no ",
        "missing",
    ]

    caution_points = 5 if any(term in combined_text for term in caution_terms) else 0

    earned = grounding_points + hallucination_points + caution_points
    passed = earned >= 12

    return _result(
        name="Grounding and hallucination controls are present",
        passed=passed,
        earned_points=earned,
        max_points=15,
        details=(
            f"grounding_note_count={len(grounding_notes)}, "
            f"hallucination_risk_note_count={len(hallucination_notes)}, "
            f"caution_language_present={caution_points > 0}"
        ),
    )


def _check_implementation_recommendations(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    recommendations = analysis.get("implementation_recommendations", [])

    approval_required_count = sum(
        1
        for recommendation in recommendations
        if recommendation.get("approval_required") is True
    )

    high_priority_count = sum(
        1
        for recommendation in recommendations
        if str(recommendation.get("priority", "")).lower() == "high"
    )

    owner_count = sum(
        1
        for recommendation in recommendations
        if recommendation.get("suggested_owner")
    )

    count_points = 3 if len(recommendations) >= 5 else min(3, len(recommendations))
    approval_points = 3 if approval_required_count >= 4 else min(3, approval_required_count)
    priority_points = 2 if high_priority_count >= 2 else min(2, high_priority_count)
    owner_points = 2 if owner_count >= 5 else 0

    earned = count_points + approval_points + priority_points + owner_points
    passed = earned >= 8

    return _result(
        name="Implementation recommendations are actionable",
        passed=passed,
        earned_points=earned,
        max_points=10,
        details=(
            f"recommendation_count={len(recommendations)}, "
            f"approval_required_count={approval_required_count}, "
            f"high_priority_count={high_priority_count}, "
            f"owner_count={owner_count}"
        ),
    )


def _check_governance_controls(
    analysis: dict[str, Any],
    term_groups: list[list[str]],
) -> dict[str, Any]:
    text = _json_text(analysis)
    matched = _matched_groups(text=text, term_groups=term_groups)

    earned = min(15, len(matched) * 3)
    passed = earned >= 12

    return _result(
        name="Governance boundaries are clearly represented",
        passed=passed,
        earned_points=earned,
        max_points=15,
        details=f"matched_governance_groups={matched}",
    )


def _check_domain_leakage(
    analysis: dict[str, Any],
    prohibited_terms: set[str],
) -> dict[str, Any]:
    text = _json_text(analysis)
    found = sorted(
        term
        for term in prohibited_terms
        if term.lower() in text
    )

    return _result(
        name="No domain leakage from prior examples",
        passed=not found,
        earned_points=10 if not found else 0,
        max_points=10,
        details=f"found_prohibited_terms={found}",
    )


def _get_artifacts(
    client: TestClient,
    run_id: str,
) -> list[dict[str, Any]]:
    response = client.get(f"/runs/{run_id}/artifacts")
    assert response.status_code == 200, response.text
    return response.json()


def _find_artifact(
    artifacts: list[dict[str, Any]],
    artifact_type: str,
) -> dict[str, Any] | None:
    matching_artifacts = [
        artifact
        for artifact in artifacts
        if artifact["artifact_type"] == artifact_type
    ]

    if not matching_artifacts:
        return None

    return matching_artifacts[-1]


def _matched_groups(
    text: str,
    term_groups: list[list[str]],
) -> list[str]:
    matched = []

    for index, group in enumerate(term_groups, start=1):
        if any(term.lower() in text for term in group):
            matched.append(f"group_{index}")

    return matched


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True).lower()


def _is_empty(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    if isinstance(value, (list, dict, set, tuple)):
        return len(value) == 0

    return False


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
        description="Evaluate an LLM shadow-analysis artifact."
    )

    parser.add_argument(
        "--workflow-id",
        default="access_request_review",
        help="Workflow ID to evaluate.",
    )

    parser.add_argument(
        "--evaluation-profile-id",
        default=None,
        help=(
            "Evaluation profile to use. Defaults to --workflow-id. "
            "Use this when evaluating a generated workflow with a different workflow ID."
        ),
    )

    parser.add_argument(
        "--run-id",
        default=None,
        help=(
            "Existing run_id containing an llm_workflow_analysis artifact. "
            "When omitted, a new governed baseline run and LLM shadow analysis are created."
        ),
    )

    parser.add_argument(
        "--artifacts-dir",
        default=None,
        help="Load input artifacts from a local directory instead of /runs/{run_id}/artifacts.",
    )

    parser.add_argument(
        "--skip-persist",
        action="store_true",
        help="Print the evaluation without saving it as an artifact.",
    )

    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print the full evaluation artifact JSON.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()