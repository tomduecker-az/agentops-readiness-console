from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DiagnosticQualityIssue:
    severity: str
    code: str
    location: str
    message: str


_GENERIC_PHRASES = (
    "define controls",
    "define process",
    "clarify requirements",
    "document policies",
    "ensure compliance",
    "establish governance",
    "implement controls",
    "stakeholder alignment",
    "best practices",
    "leverage ai",
    "drive efficiency",
)


def evaluate_diagnostic_quality(
    diagnostic: dict[str, Any],
) -> list[DiagnosticQualityIssue]:
    issues: list[DiagnosticQualityIssue] = []

    _require_non_empty_list(
        diagnostic,
        "non_obvious_insights",
        min_count=3,
        issues=issues,
    )
    _require_non_empty_list(
        diagnostic,
        "automation_misconceptions",
        min_count=2,
        issues=issues,
    )
    _require_non_empty_list(
        diagnostic,
        "operational_pattern_analysis",
        min_count=1,
        issues=issues,
    )
    _require_non_empty_list(
        diagnostic,
        "pilot_learning_objectives",
        min_count=3,
        issues=issues,
    )
    _require_non_empty_list(
        diagnostic,
        "autonomy_unlock_path",
        min_count=1,
        issues=issues,
    )

    _evaluate_executive_summary(diagnostic, issues)
    _evaluate_first_use_case(diagnostic, issues)
    _evaluate_non_obvious_insights(diagnostic, issues)
    _evaluate_autonomy_unlock_path(diagnostic, issues)
    _evaluate_generic_language(diagnostic, issues)
    _evaluate_evidence_references(diagnostic, issues)

    return issues


def quality_passed(issues: list[DiagnosticQualityIssue]) -> bool:
    return not any(issue.severity == "error" for issue in issues)


def _require_non_empty_list(
    diagnostic: dict[str, Any],
    field_name: str,
    *,
    min_count: int,
    issues: list[DiagnosticQualityIssue],
) -> None:
    value = diagnostic.get(field_name)

    if not isinstance(value, list) or len(value) < min_count:
        issues.append(
            DiagnosticQualityIssue(
                severity="error",
                code="missing_required_insight_section",
                location=field_name,
                message=f"Expected at least {min_count} items in {field_name}.",
            )
        )


def _evaluate_executive_summary(
    diagnostic: dict[str, Any],
    issues: list[DiagnosticQualityIssue],
) -> None:
    executive_summary = diagnostic.get("executive_summary", {})

    if not isinstance(executive_summary, dict):
        issues.append(
            DiagnosticQualityIssue(
                severity="error",
                code="missing_executive_summary",
                location="executive_summary",
                message="Executive summary is missing or invalid.",
            )
        )
        return

    takeaway = str(executive_summary.get("executive_takeaway", "")).strip()

    if len(takeaway) < 120:
        issues.append(
            DiagnosticQualityIssue(
                severity="warning",
                code="weak_executive_takeaway",
                location="executive_summary.executive_takeaway",
                message="Executive takeaway may be too short to explain the core insight.",
            )
        )

    lower_takeaway = takeaway.lower()

    if "model capability" not in lower_takeaway and "not" not in lower_takeaway:
        issues.append(
            DiagnosticQualityIssue(
                severity="warning",
                code="missing_blocker_framing",
                location="executive_summary.executive_takeaway",
                message=(
                    "Executive takeaway should explain whether the blocker is model capability, "
                    "process design, data readiness, or controls."
                ),
            )
        )


def _evaluate_first_use_case(
    diagnostic: dict[str, Any],
    issues: list[DiagnosticQualityIssue],
) -> None:
    use_case = diagnostic.get("recommended_first_use_case", {})

    if not isinstance(use_case, dict):
        issues.append(
            DiagnosticQualityIssue(
                severity="error",
                code="missing_first_use_case",
                location="recommended_first_use_case",
                message="Recommended first use case is missing or invalid.",
            )
        )
        return

    why = use_case.get("why_this_is_recommended", [])
    measures = use_case.get("success_measures", [])
    blocked_actions = use_case.get("blocked_actions", [])

    if not isinstance(why, list) or len(why) < 3:
        issues.append(
            DiagnosticQualityIssue(
                severity="error",
                code="weak_first_use_case_rationale",
                location="recommended_first_use_case.why_this_is_recommended",
                message="Recommended first use case needs at least three specific reasons.",
            )
        )

    if not isinstance(measures, list) or len(measures) < 4:
        issues.append(
            DiagnosticQualityIssue(
                severity="error",
                code="weak_first_use_case_measurement",
                location="recommended_first_use_case.success_measures",
                message="Recommended first use case needs at least four success measures.",
            )
        )

    if not isinstance(blocked_actions, list) or not blocked_actions:
        issues.append(
            DiagnosticQualityIssue(
                severity="warning",
                code="missing_first_use_case_boundaries",
                location="recommended_first_use_case.blocked_actions",
                message="Recommended first use case should clearly state blocked actions.",
            )
        )


def _evaluate_non_obvious_insights(
    diagnostic: dict[str, Any],
    issues: list[DiagnosticQualityIssue],
) -> None:
    insights = diagnostic.get("non_obvious_insights", [])

    if not isinstance(insights, list):
        return

    for index, insight in enumerate(insights):
        if not isinstance(insight, dict):
            continue

        insight_text = " ".join(
            str(insight.get(key, ""))
            for key in (
                "insight",
                "why_it_is_not_obvious",
                "business_implication",
                "recommended_action",
            )
        )

        if len(insight_text) < 250:
            issues.append(
                DiagnosticQualityIssue(
                    severity="warning",
                    code="thin_non_obvious_insight",
                    location=f"non_obvious_insights[{index}]",
                    message="Non-obvious insight may be too thin to be useful.",
                )
            )

        if not insight.get("why_it_is_not_obvious"):
            issues.append(
                DiagnosticQualityIssue(
                    severity="error",
                    code="missing_why_not_obvious",
                    location=f"non_obvious_insights[{index}].why_it_is_not_obvious",
                    message="Each non-obvious insight must explain why it is not obvious.",
                )
            )


def _evaluate_autonomy_unlock_path(
    diagnostic: dict[str, Any],
    issues: list[DiagnosticQualityIssue],
) -> None:
    stages = diagnostic.get("autonomy_unlock_path", [])

    if not isinstance(stages, list):
        return

    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            continue

        required_changes = stage.get("required_changes", [])
        validation_required = stage.get("validation_required", [])

        if not isinstance(required_changes, list) or len(required_changes) < 2:
            issues.append(
                DiagnosticQualityIssue(
                    severity="warning",
                    code="thin_autonomy_unlock_changes",
                    location=f"autonomy_unlock_path[{index}].required_changes",
                    message="Autonomy unlock stage should include concrete required changes.",
                )
            )

        if not isinstance(validation_required, list) or len(validation_required) < 2:
            issues.append(
                DiagnosticQualityIssue(
                    severity="warning",
                    code="thin_autonomy_unlock_validation",
                    location=f"autonomy_unlock_path[{index}].validation_required",
                    message="Autonomy unlock stage should include validation required before expansion.",
                )
            )


def _evaluate_generic_language(
    diagnostic: dict[str, Any],
    issues: list[DiagnosticQualityIssue],
) -> None:
    text = str(diagnostic).lower()

    generic_hits = [phrase for phrase in _GENERIC_PHRASES if phrase in text]

    if len(generic_hits) >= 5:
        issues.append(
            DiagnosticQualityIssue(
                severity="warning",
                code="generic_language_detected",
                location="diagnostic",
                message=f"Diagnostic contains multiple generic phrases: {generic_hits[:8]}",
            )
        )


def _evaluate_evidence_references(
    diagnostic: dict[str, Any],
    issues: list[DiagnosticQualityIssue],
) -> None:
    evidence_catalog = diagnostic.get("evidence_catalog", [])

    evidence_ids = {
        item.get("evidence_id")
        for item in evidence_catalog
        if isinstance(item, dict) and item.get("evidence_id")
    }

    if not evidence_ids:
        issues.append(
            DiagnosticQualityIssue(
                severity="error",
                code="missing_evidence_catalog",
                location="evidence_catalog",
                message="Diagnostic is missing an evidence catalog.",
            )
        )
        return

    sections_to_check = (
        "non_obvious_insights",
        "automation_misconceptions",
        "top_readiness_blockers",
        "recommended_first_use_case",
        "use_cases_to_avoid",
        "process_redesign_requirements",
        "control_gap_remediation_plan",
        "value_hypotheses",
        "future_state_recommendations",
    )

    for section_name in sections_to_check:
        section = diagnostic.get(section_name)

        if isinstance(section, dict):
            _check_evidence_refs_in_item(
                item=section,
                location=section_name,
                evidence_ids=evidence_ids,
                issues=issues,
            )
        elif isinstance(section, list):
            for index, item in enumerate(section):
                if isinstance(item, dict):
                    _check_evidence_refs_in_item(
                        item=item,
                        location=f"{section_name}[{index}]",
                        evidence_ids=evidence_ids,
                        issues=issues,
                    )


def _check_evidence_refs_in_item(
    *,
    item: dict[str, Any],
    location: str,
    evidence_ids: set[str],
    issues: list[DiagnosticQualityIssue],
) -> None:
    refs = item.get("evidence_references", [])

    if not isinstance(refs, list) or not refs:
        issues.append(
            DiagnosticQualityIssue(
                severity="warning",
                code="missing_item_evidence",
                location=location,
                message="Item has no evidence references.",
            )
        )
        return

    invalid_refs = [ref for ref in refs if ref not in evidence_ids]

    if invalid_refs:
        issues.append(
            DiagnosticQualityIssue(
                severity="error",
                code="invalid_evidence_reference",
                location=location,
                message=f"Item references evidence IDs not in catalog: {invalid_refs}",
            )
        )