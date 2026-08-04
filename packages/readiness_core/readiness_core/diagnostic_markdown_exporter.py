from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from readiness_core.diagnostic_models import WorkflowAIOpportunityDiagnostic


def render_workflow_ai_opportunity_diagnostic_markdown(
    diagnostic: WorkflowAIOpportunityDiagnostic | Mapping[str, Any],
) -> str:
    """Render a Workflow AI Opportunity Diagnostic as client-facing Markdown."""

    data = _to_dict(diagnostic)

    lines: list[str] = []

    workflow_id = _text(data.get("workflow_id"), "Unknown workflow")
    run_id = _text(data.get("run_id"), "Unknown run")
    version = _text(data.get("diagnostic_version"), "Unknown version")

    lines.append("# Workflow AI Opportunity Diagnostic")
    lines.append("")
    lines.append(f"**Workflow:** `{workflow_id}`  ")
    lines.append(f"**Run:** `{run_id}`  ")
    lines.append(f"**Diagnostic version:** `{version}`")
    lines.append("")

    _render_executive_summary(lines, data)
    _render_non_obvious_insights(lines, data)
    _render_automation_ceiling(lines, data)
    _render_recommended_first_use_case(lines, data)
    _render_automation_misconceptions(lines, data)
    _render_operational_pattern_analysis(lines, data)
    _render_pilot_learning_objectives(lines, data)
    _render_autonomy_unlock_path(lines, data)
    _render_sample_record_patterns(lines, data)
    _render_readiness_blockers(lines, data)
    _render_process_redesign_requirements(lines, data)
    _render_control_gap_remediation(lines, data)
    _render_value_hypotheses(lines, data)
    _render_measurement_plan(lines, data)
    _render_workflow_owner_questions(lines, data)
    _render_quality_summary(lines, data)
    _render_evidence_catalog(lines, data)

    return "\n".join(lines).rstrip() + "\n"


def _render_executive_summary(lines: list[str], data: dict[str, Any]) -> None:
    summary = _dict(data.get("executive_summary"))

    _h2(lines, "Executive Diagnostic")

    headline = _text(summary.get("headline"))
    recommendation = _text(summary.get("recommendation"))
    ceiling = _text(summary.get("current_automation_ceiling"))
    first_pilot = _text(summary.get("recommended_first_pilot"))
    takeaway = _text(summary.get("executive_takeaway"))

    if headline:
        lines.append(f"**Headline:** {headline}")
        lines.append("")

    if takeaway:
        lines.append("> " + takeaway)
        lines.append("")

    _kv(lines, "Current automation ceiling", ceiling)
    _kv(lines, "Recommendation", recommendation)
    _kv(lines, "Recommended first pilot", first_pilot)

    do_not_start = _list(summary.get("do_not_start_with"))
    if do_not_start:
        lines.append("")
        lines.append("**Do not start with:**")
        _bullets(lines, do_not_start)

    top_blockers = _list(summary.get("top_blockers"))
    if top_blockers:
        lines.append("")
        lines.append("**Top blockers:**")
        _bullets(lines, top_blockers)

    next_30_days = _list(summary.get("next_30_days"))
    if next_30_days:
        lines.append("")
        lines.append("**Recommended next 30 days:**")
        _bullets(lines, next_30_days)

    lines.append("")


def _render_non_obvious_insights(lines: list[str], data: dict[str, Any]) -> None:
    insights = _dict_list(data.get("non_obvious_insights"))

    if not insights:
        return

    _h2(lines, "Non-Obvious Insights")

    lines.append(
        "These are the findings most likely to change how a workflow owner thinks about the AI opportunity."
    )
    lines.append("")

    for item in insights:
        _h3(lines, _text(item.get("title"), "Insight"))

        _paragraph(lines, "Insight", item.get("insight"))
        _paragraph(lines, "Why this is not obvious", item.get("why_it_is_not_obvious"))
        _paragraph(lines, "Business implication", item.get("business_implication"))
        _paragraph(lines, "Recommended action", item.get("recommended_action"))
        _evidence(lines, item)

    lines.append("")


def _render_automation_ceiling(lines: list[str], data: dict[str, Any]) -> None:
    ceiling = _dict(data.get("automation_ceiling"))

    if not ceiling:
        return

    _h2(lines, "Automation Ceiling")

    _kv(lines, "Current ceiling", _text(ceiling.get("current_ceiling")))
    _paragraph(lines, "Summary", ceiling.get("ceiling_summary"))

    why = _list(ceiling.get("why_this_is_the_ceiling"))
    if why:
        lines.append("**Why this is the ceiling:**")
        _bullets(lines, why)
        lines.append("")

    raise_ceiling = _list(ceiling.get("what_would_raise_the_ceiling"))
    if raise_ceiling:
        lines.append("**What would raise the ceiling:**")
        _bullets(lines, raise_ceiling)
        lines.append("")

    blockers = _list(ceiling.get("what_prevents_higher_autonomy"))
    if blockers:
        lines.append("**What prevents higher autonomy:**")
        _bullets(lines, blockers)
        lines.append("")

    _evidence(lines, ceiling)


def _render_recommended_first_use_case(lines: list[str], data: dict[str, Any]) -> None:
    use_case = _dict(data.get("recommended_first_use_case"))

    if not use_case:
        return

    _h2(lines, "Recommended First AI Use Case")

    _h3(lines, _text(use_case.get("title"), "Recommended first use case"))

    _paragraph(lines, "Description", use_case.get("description"))
    _kv(lines, "Risk level", _text(use_case.get("risk_level")))
    _kv(lines, "Readiness", _text(use_case.get("readiness")))
    _paragraph(lines, "Suggested pilot scope", use_case.get("suggested_pilot_scope"))

    why = _list(use_case.get("why_this_is_recommended"))
    if why:
        lines.append("**Why this is the right first pilot:**")
        _bullets(lines, why)
        lines.append("")

    expected_value = _list(use_case.get("expected_value"))
    if expected_value:
        lines.append("**Expected value:**")
        _bullets(lines, expected_value)
        lines.append("")

    blocked_actions = _list(use_case.get("blocked_actions"))
    if blocked_actions:
        lines.append("**Boundaries / blocked actions:**")
        _bullets(lines, blocked_actions)
        lines.append("")

    success_measures = _list(use_case.get("success_measures"))
    if success_measures:
        lines.append("**Success measures:**")
        _bullets(lines, success_measures)
        lines.append("")

    _evidence(lines, use_case)


def _render_automation_misconceptions(lines: list[str], data: dict[str, Any]) -> None:
    misconceptions = _dict_list(data.get("automation_misconceptions"))

    if not misconceptions:
        return

    _h2(lines, "Automation Misconceptions to Avoid")

    for item in misconceptions:
        _h3(lines, _text(item.get("tempting_but_wrong_idea"), "Tempting but premature idea"))
        _paragraph(lines, "Why it is wrong or premature", item.get("why_it_is_wrong_or_premature"))
        _paragraph(lines, "Safer alternative", item.get("safer_alternative"))
        _evidence(lines, item)


def _render_operational_pattern_analysis(lines: list[str], data: dict[str, Any]) -> None:
    patterns = _dict_list(data.get("operational_pattern_analysis"))

    if not patterns:
        return

    _h2(lines, "Operational Pattern Analysis")

    for item in patterns:
        _h3(lines, _text(item.get("workflow_pattern"), "Workflow pattern"))
        _paragraph(lines, "Operational dependency", item.get("operational_dependency"))
        _paragraph(lines, "AI opportunity created by this pattern", item.get("ai_opportunity_created_by_pattern"))
        _paragraph(lines, "AI limitation created by this pattern", item.get("ai_limitation_created_by_pattern"))
        _paragraph(lines, "What this means for the pilot", item.get("what_this_means_for_the_pilot"))
        _evidence(lines, item)


def _render_pilot_learning_objectives(lines: list[str], data: dict[str, Any]) -> None:
    objectives = _dict_list(data.get("pilot_learning_objectives"))

    if not objectives:
        return

    _h2(lines, "Pilot Learning Objectives")

    for item in objectives:
        _h3(lines, _text(item.get("objective"), "Pilot objective"))
        _paragraph(lines, "Why it matters", item.get("why_it_matters"))
        _paragraph(lines, "How to test", item.get("how_to_test"))
        _paragraph(lines, "Pass/fail signal", item.get("pass_fail_signal"))
        _paragraph(lines, "Expansion decision supported", item.get("expansion_decision_supported"))
        _evidence(lines, item)


def _render_autonomy_unlock_path(lines: list[str], data: dict[str, Any]) -> None:
    stages = _dict_list(data.get("autonomy_unlock_path"))

    if not stages:
        return

    _h2(lines, "Autonomy Unlock Path")

    lines.append(
        "This path distinguishes the current safe posture from future autonomy that may become possible after process, data, and control changes."
    )
    lines.append("")

    for item in stages:
        from_ceiling = _text(item.get("from_ceiling"), "current")
        to_ceiling = _text(item.get("to_ceiling"), "future")
        _h3(lines, f"{from_ceiling} → {to_ceiling}")

        required_changes = _list(item.get("required_changes"))
        if required_changes:
            lines.append("**Required changes:**")
            _bullets(lines, required_changes)
            lines.append("")

        validation = _list(item.get("validation_required"))
        if validation:
            lines.append("**Validation required:**")
            _bullets(lines, validation)
            lines.append("")

        risks = _list(item.get("risks_that_must_be_reduced"))
        if risks:
            lines.append("**Risks that must be reduced:**")
            _bullets(lines, risks)
            lines.append("")

        _evidence(lines, item)


def _render_sample_record_patterns(lines: list[str], data: dict[str, Any]) -> None:
    patterns = _dict_list(data.get("sample_record_patterns"))

    if not patterns:
        return

    _h2(lines, "Sample Record Patterns")

    for item in patterns:
        _h3(lines, _text(item.get("pattern_name"), "Sample pattern"))

        records = _list(item.get("records_observed"))
        if records:
            lines.append(f"**Records observed:** {', '.join(records)}")
            lines.append("")

        _paragraph(lines, "What the pattern shows", item.get("what_the_pattern_shows"))
        _paragraph(lines, "AI opportunity", item.get("ai_opportunity"))
        _paragraph(lines, "Risk or limitation", item.get("risk_or_limitation"))
        _paragraph(lines, "Recommended handling", item.get("recommended_handling"))
        _evidence(lines, item)


def _render_readiness_blockers(lines: list[str], data: dict[str, Any]) -> None:
    blockers = _dict_list(data.get("top_readiness_blockers"))

    if not blockers:
        return

    _h2(lines, "Top Readiness Blockers")

    for item in blockers:
        title = _text(item.get("title"), "Readiness blocker")
        severity = _text(item.get("severity"))
        heading = f"{severity.upper()} — {title}" if severity else title

        _h3(lines, heading)
        _paragraph(lines, "Description", item.get("description"))
        _paragraph(lines, "Business impact", item.get("business_impact"))
        _paragraph(lines, "Technical/control impact", item.get("technical_or_control_impact"))

        remediation = _list(item.get("recommended_remediation"))
        if remediation:
            lines.append("**Recommended remediation:**")
            _bullets(lines, remediation)
            lines.append("")

        owner = _text(item.get("owner_role"))
        if owner:
            _kv(lines, "Likely owner", owner)

        _evidence(lines, item)


def _render_process_redesign_requirements(lines: list[str], data: dict[str, Any]) -> None:
    requirements = _dict_list(data.get("process_redesign_requirements"))

    if not requirements:
        return

    _h2(lines, "Process Redesign Requirements")

    for item in requirements:
        title = _text(item.get("title"), "Process redesign requirement")
        priority = _text(item.get("priority"))
        heading = f"{priority.upper()} — {title}" if priority else title

        _h3(lines, heading)
        _paragraph(lines, "Current gap", item.get("current_gap"))
        _paragraph(lines, "Required change", item.get("required_change"))
        _paragraph(lines, "Why this is required for AI readiness", item.get("why_required_for_ai_readiness"))

        unlocks = _list(item.get("unlocks"))
        if unlocks:
            lines.append("**Unlocks:**")
            _bullets(lines, unlocks)
            lines.append("")

        _evidence(lines, item)


def _render_control_gap_remediation(lines: list[str], data: dict[str, Any]) -> None:
    controls = _dict_list(data.get("control_gap_remediation_plan"))

    if not controls:
        return

    _h2(lines, "Control Gap Remediation Plan")

    for item in controls:
        title = _text(item.get("title"), "Control gap")
        priority = _text(item.get("priority"))
        heading = f"{priority.upper()} — {title}" if priority else title

        _h3(lines, heading)
        _paragraph(lines, "Current gap", item.get("current_gap"))
        _paragraph(lines, "Risk if unresolved", item.get("risk_if_unresolved"))
        _paragraph(lines, "Recommended control", item.get("recommended_control"))
        _paragraph(lines, "Validation method", item.get("validation_method"))
        _evidence(lines, item)


def _render_value_hypotheses(lines: list[str], data: dict[str, Any]) -> None:
    hypotheses = _dict_list(data.get("value_hypotheses"))

    if not hypotheses:
        return

    _h2(lines, "Value Hypotheses")

    lines.append(
        "These are directional hypotheses to test during a controlled pilot, not guaranteed ROI claims."
    )
    lines.append("")

    for item in hypotheses:
        _h3(lines, _text(item.get("value_area"), "Value hypothesis"))
        _paragraph(lines, "Hypothesis", item.get("hypothesis"))
        _paragraph(lines, "Expected directional impact", item.get("expected_directional_impact"))

        measurements = _list(item.get("required_measurements"))
        if measurements:
            lines.append("**Required measurements:**")
            _bullets(lines, measurements)
            lines.append("")

        baseline = _list(item.get("baseline_data_needed"))
        if baseline:
            lines.append("**Baseline data needed:**")
            _bullets(lines, baseline)
            lines.append("")

        _evidence(lines, item)


def _render_measurement_plan(lines: list[str], data: dict[str, Any]) -> None:
    metrics = _dict_list(data.get("measurement_plan"))

    if not metrics:
        return

    _h2(lines, "Measurement Plan")

    for item in metrics:
        _h3(lines, _text(item.get("metric_name"), "Metric"))
        _paragraph(lines, "Why it matters", item.get("why_it_matters"))
        _paragraph(lines, "How to measure", item.get("how_to_measure"))
        _kv(lines, "Baseline required", str(bool(item.get("baseline_required"))))

        target = _text(item.get("target_or_success_signal"))
        if target:
            _paragraph(lines, "Target or success signal", target)


def _render_workflow_owner_questions(lines: list[str], data: dict[str, Any]) -> None:
    questions = _dict_list(data.get("questions_for_workflow_owner"))

    if not questions:
        return

    _h2(lines, "Questions for the Workflow Owner")

    for item in questions:
        priority = _text(item.get("priority"), "priority")
        question = _text(item.get("question"), "Question")

        lines.append(f"- **{priority.upper()}** — {question}")

        why = _text(item.get("why_it_matters"))
        if why:
            lines.append(f"  - Why it matters: {why}")

        answer_needed_for = _list(item.get("answer_needed_for"))
        if answer_needed_for:
            lines.append(f"  - Answer needed for: {', '.join(answer_needed_for)}")

    lines.append("")


def _render_quality_summary(lines: list[str], data: dict[str, Any]) -> None:
    metadata = _dict(data.get("metadata"))
    quality = _dict(metadata.get("diagnostic_quality_evaluation"))

    if not quality:
        return

    _h2(lines, "Diagnostic Quality Gate")

    _kv(lines, "Quality passed", str(bool(quality.get("quality_passed"))))
    _kv(lines, "Errors", str(quality.get("error_count", 0)))
    _kv(lines, "Warnings", str(quality.get("warning_count", 0)))
    lines.append("")


def _render_evidence_catalog(lines: list[str], data: dict[str, Any]) -> None:
    catalog = _dict_list(data.get("evidence_catalog"))

    if not catalog:
        return

    _h2(lines, "Evidence Catalog")

    for item in catalog:
        evidence_id = _text(item.get("evidence_id"), "UNKNOWN")
        title = (
            _text(item.get("title"))
            or _text(item.get("source_name"))
            or _text(item.get("document_id"))
            or "Evidence item"
        )
        summary = _text(item.get("summary")) or _text(item.get("content_summary"))

        lines.append(f"- **{evidence_id}** — {title}")
        if summary:
            lines.append(f"  - {summary}")

    lines.append("")


def _to_dict(
    diagnostic: WorkflowAIOpportunityDiagnostic | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(diagnostic, WorkflowAIOpportunityDiagnostic):
        return diagnostic.model_dump(mode="json")

    if isinstance(diagnostic, Mapping):
        return dict(diagnostic)

    return WorkflowAIOpportunityDiagnostic.model_validate(diagnostic).model_dump(mode="json")


def _h2(lines: list[str], title: str) -> None:
    lines.append(f"## {title}")
    lines.append("")


def _h3(lines: list[str], title: str) -> None:
    lines.append(f"### {title}")
    lines.append("")


def _kv(lines: list[str], label: str, value: str) -> None:
    if value:
        lines.append(f"**{label}:** {value}")
        lines.append("")


def _paragraph(lines: list[str], label: str, value: Any) -> None:
    text = _text(value)

    if text:
        lines.append(f"**{label}:** {text}")
        lines.append("")


def _evidence(lines: list[str], item: dict[str, Any]) -> None:
    refs = _list(item.get("evidence_references"))

    if refs:
        lines.append(f"**Evidence:** {', '.join(refs)}")
        lines.append("")


def _bullets(lines: list[str], items: list[str]) -> None:
    for item in items:
        if item:
            lines.append(f"- {item}")


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, dict)]


def _list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [_text(item) for item in value if _text(item)]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default

    text = str(value).strip()

    return text if text else default