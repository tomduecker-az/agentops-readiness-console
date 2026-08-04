from __future__ import annotations

from typing import Any

from readiness_core.models import AgenticReadinessBlueprint


def render_agentic_readiness_blueprint_markdown(
    blueprint: AgenticReadinessBlueprint | dict[str, Any],
) -> str:
    if isinstance(blueprint, dict):
        blueprint_model = AgenticReadinessBlueprint.model_validate(blueprint)
    else:
        blueprint_model = blueprint

    data = blueprint_model.model_dump(mode="json")

    lines: list[str] = []

    lines.extend(_render_header(data))
    lines.extend(_render_executive_summary(data))
    lines.extend(_render_readiness_scorecard(data))
    lines.extend(_render_autonomy_matrix(data))
    lines.extend(_render_step_details(data))
    lines.extend(_render_tooling_blueprint(data))
    lines.extend(_render_human_approval_gates(data))
    lines.extend(_render_risk_control_summary(data))
    lines.extend(_render_implementation_roadmap(data))
    lines.extend(_render_cost_and_operations(data))
    lines.extend(_render_validation_and_reconciliation(data))
    lines.extend(_render_limitations(data))
    lines.extend(_render_evidence_catalog(data))

    return "\n".join(lines).rstrip() + "\n"


def _render_header(data: dict[str, Any]) -> list[str]:
    metadata = data.get("metadata", {})

    return [
        "# Agentic Readiness Blueprint",
        "",
        f"**Workflow ID:** `{_text(data.get('workflow_id'))}`  ",
        f"**Run ID:** `{_text(data.get('run_id'))}`  ",
        f"**Blueprint Version:** `{_text(data.get('blueprint_version'))}`  ",
        f"**Created At:** `{_text(data.get('created_at'))}`  ",
        f"**Generation Mode:** `{_text(metadata.get('generation_mode', 'not_specified'))}`",
        "",
        "---",
        "",
    ]


def _render_executive_summary(data: dict[str, Any]) -> list[str]:
    summary = data.get("executive_summary", {})

    lines = [
        "## Executive Summary",
        "",
        f"**Workflow Name:** {_text(summary.get('workflow_name'))}",
        "",
        f"**Recommendation:** `{_text(summary.get('recommendation'))}`",
        "",
        f"**Confidence:** {_text(summary.get('confidence'))}",
        "",
        _text(summary.get("summary")),
        "",
    ]

    lines.extend(_bullet_section("Primary Value Opportunities", summary.get("primary_value_opportunities", [])))
    lines.extend(_bullet_section("Primary Constraints", summary.get("primary_constraints", [])))

    return lines


def _render_readiness_scorecard(data: dict[str, Any]) -> list[str]:
    rows = []

    for item in data.get("readiness_scorecard", []):
        rows.append(
            [
                item.get("dimension"),
                f"{item.get('score')}/100",
                item.get("rationale"),
                _refs(item.get("evidence_references", [])),
            ]
        )

    return [
        "## Readiness Scorecard",
        "",
        *_table(
            ["Dimension", "Score", "Rationale", "Evidence"],
            rows,
        ),
        "",
    ]


def _render_autonomy_matrix(data: dict[str, Any]) -> list[str]:
    rows = []

    for step in data.get("step_level_autonomy_matrix", []):
        rows.append(
            [
                step.get("step_id"),
                step.get("step_name"),
                step.get("recommended_posture"),
                step.get("risk_level"),
                _yes_no(step.get("approval_required")),
                _yes_no(step.get("audit_required")),
                step.get("implementation_phase"),
                _refs(step.get("evidence_references", [])),
            ]
        )

    return [
        "## Step-Level Autonomy Matrix",
        "",
        *_table(
            [
                "Step",
                "Name",
                "Recommended Posture",
                "Risk",
                "Approval",
                "Audit",
                "Phase",
                "Evidence",
            ],
            rows,
        ),
        "",
    ]


def _render_step_details(data: dict[str, Any]) -> list[str]:
    lines = [
        "## Step Details",
        "",
    ]

    for step in data.get("step_level_autonomy_matrix", []):
        lines.extend(
            [
                f"### {step.get('step_id')}: {_text(step.get('step_name'))}",
                "",
                f"**Current Step Summary:** {_text(step.get('current_step_summary'))}",
                "",
                f"**Recommended Posture:** `{_text(step.get('recommended_posture'))}`  ",
                f"**Risk Level:** `{_text(step.get('risk_level'))}`  ",
                f"**Required Reviewer:** {_text(step.get('required_human_reviewer'))}  ",
                f"**Approval Required:** {_yes_no(step.get('approval_required'))}  ",
                f"**Audit Required:** {_yes_no(step.get('audit_required'))}",
                "",
                f"**Why AI Is Useful:** {_text(step.get('why_ai_is_useful'))}",
                "",
                f"**Why AI Should Be Limited:** {_text(step.get('why_ai_should_be_limited'))}",
                "",
            ]
        )

        lines.extend(_bullet_section("Allowed AI Actions", step.get("allowed_ai_actions", []), heading_level=4))
        lines.extend(_bullet_section("Blocked AI Actions", step.get("blocked_ai_actions", []), heading_level=4))

        lines.extend(
            [
                f"**Evidence:** {_refs(step.get('evidence_references', []))}",
                "",
            ]
        )

    return lines


def _render_tooling_blueprint(data: dict[str, Any]) -> list[str]:
    rows = []

    for tool in data.get("tooling_blueprint", []):
        rows.append(
            [
                tool.get("capability_name"),
                tool.get("operation_type"),
                tool.get("recommended_access"),
                tool.get("risk_level"),
                _yes_no(tool.get("approval_required")),
                _yes_no(tool.get("audit_required")),
                tool.get("mcp_server_candidate"),
                tool.get("implementation_phase"),
                _refs(tool.get("evidence_references", [])),
            ]
        )

    return [
        "## Tooling Blueprint",
        "",
        *_table(
            [
                "Capability",
                "Operation",
                "Access",
                "Risk",
                "Approval",
                "Audit",
                "MCP Candidate",
                "Phase",
                "Evidence",
            ],
            rows,
        ),
        "",
    ]


def _render_human_approval_gates(data: dict[str, Any]) -> list[str]:
    lines = [
        "## Human Approval Gates",
        "",
    ]

    gates = data.get("human_approval_gates", [])

    if not gates:
        return lines + ["No approval gates specified.", ""]

    for index, gate in enumerate(gates, start=1):
        lines.extend(
            [
                f"### Gate {index}: {_text(gate.get('gate_name'))}",
                "",
                f"**Trigger Condition:** {_text(gate.get('trigger_condition'))}",
                "",
                f"**Required Reviewer:** {_text(gate.get('required_reviewer'))}",
                "",
                f"**Decision Required:** {_text(gate.get('decision_required'))}",
                "",
            ]
        )

        lines.extend(_bullet_section("Agent Allowed Before Approval", gate.get("agent_allowed_before_approval", []), heading_level=4))
        lines.extend(_bullet_section("Blocked Without Approval", gate.get("blocked_without_approval", []), heading_level=4))
        lines.extend(_bullet_section("Required Evidence", gate.get("required_evidence", []), heading_level=4))

        lines.extend(
            [
                f"**Evidence:** {_refs(gate.get('evidence_references', []))}",
                "",
            ]
        )

    return lines


def _render_risk_control_summary(data: dict[str, Any]) -> list[str]:
    lines = [
        "## Risk and Control Summary",
        "",
    ]

    risks = data.get("risk_control_summary", [])

    if not risks:
        return lines + ["No risks specified.", ""]

    for risk in risks:
        lines.extend(
            [
                f"### {_text(risk.get('risk_id'))}",
                "",
                f"**Risk Level:** `{_text(risk.get('risk_level'))}`  ",
                f"**Owner Role:** {_text(risk.get('owner_role'))}",
                "",
                _text(risk.get("risk_description")),
                "",
            ]
        )

        lines.extend(_bullet_section("Recommended Controls", risk.get("recommended_controls", []), heading_level=4))

        lines.extend(
            [
                f"**Evidence:** {_refs(risk.get('evidence_references', []))}",
                "",
            ]
        )

    return lines


def _render_implementation_roadmap(data: dict[str, Any]) -> list[str]:
    lines = [
        "## Implementation Roadmap",
        "",
    ]

    roadmap = data.get("implementation_roadmap", [])

    if not roadmap:
        return lines + ["No roadmap specified.", ""]

    for item in roadmap:
        lines.extend(
            [
                f"### {_text(item.get('title'))}",
                "",
                f"**Phase:** `{_text(item.get('phase'))}`",
                "",
                f"**Objective:** {_text(item.get('objective'))}",
                "",
            ]
        )

        lines.extend(_bullet_section("Recommended Actions", item.get("recommended_actions", []), heading_level=4))
        lines.extend(_bullet_section("Exit Criteria", item.get("exit_criteria", []), heading_level=4))
        lines.extend(_bullet_section("Dependencies", item.get("dependencies", []), heading_level=4))

        lines.extend(
            [
                f"**Evidence:** {_refs(item.get('evidence_references', []))}",
                "",
            ]
        )

    return lines


def _render_cost_and_operations(data: dict[str, Any]) -> list[str]:
    notes = data.get("cost_and_operations_notes", {})

    lines = [
        "## Cost and Operations Notes",
        "",
    ]

    lines.extend(_bullet_section("Expected Cost Drivers", notes.get("expected_cost_drivers", []), heading_level=3))
    lines.extend(_bullet_section("Cost Controls", notes.get("cost_controls", []), heading_level=3))
    lines.extend(_bullet_section("Operational Controls", notes.get("operational_controls", []), heading_level=3))
    lines.extend(_bullet_section("Observability Requirements", notes.get("observability_requirements", []), heading_level=3))

    return lines


def _render_validation_and_reconciliation(data: dict[str, Any]) -> list[str]:
    metadata = data.get("metadata", {})
    validation = metadata.get("blueprint_safety_validation", {})
    reconciliation = metadata.get("reconciliation_report", {})
    comparison_summary = metadata.get("blueprint_comparison_summary", {})

    lines = [
        "## Validation and Reconciliation",
        "",
        "### Safety Validation",
        "",
        f"**Passed:** {_yes_no(validation.get('passed'))}  ",
        f"**Issue Count:** {_text(validation.get('issue_count', 0))}",
        "",
    ]

    validation_issues = validation.get("issues", [])

    if validation_issues:
        lines.extend(["#### Validation Issues", ""])
        for issue in validation_issues:
            lines.append(
                f"- **{_text(issue.get('severity'))}** `{_text(issue.get('code'))}` "
                f"at `{_text(issue.get('location'))}`: {_text(issue.get('message'))}"
            )
        lines.append("")
    else:
        lines.extend(["No validation issues were reported.", ""])

    if reconciliation:
        lines.extend(
            [
                "### Reconciliation",
                "",
                f"**Strategy:** `{_text(reconciliation.get('strategy'))}`  ",
                f"**Safety Overrides:** {_text(len(reconciliation.get('safety_overrides', [])))}  ",
                f"**Review Items:** {_text(len(reconciliation.get('review_items', [])))}",
                "",
            ]
        )

        accepted_sections = reconciliation.get("accepted_sections", [])
        lines.extend(_bullet_section("Accepted Sections", accepted_sections, heading_level=4))

        safety_overrides = reconciliation.get("safety_overrides", [])
        if safety_overrides:
            lines.extend(["#### Safety Overrides", ""])
            for override in safety_overrides:
                lines.append(
                    f"- `{_text(override.get('location'))}`: {_text(override.get('reason'))}"
                )
            lines.append("")

    if comparison_summary:
        lines.extend(
            [
                "### Baseline vs. LLM Proposal Comparison",
                "",
                *_table(
                    ["Metric", "Value"],
                    [[key, value] for key, value in comparison_summary.items()],
                ),
                "",
            ]
        )

    return lines


def _render_limitations(data: dict[str, Any]) -> list[str]:
    return [
        "## Limitations and Missing Information",
        "",
        *_bullets(data.get("limitations_and_missing_information", [])),
        "",
    ]


def _render_evidence_catalog(data: dict[str, Any]) -> list[str]:
    rows = []

    for evidence in data.get("evidence_catalog", []):
        rows.append(
            [
                evidence.get("evidence_id"),
                evidence.get("evidence_type"),
                evidence.get("source_title"),
                evidence.get("summary"),
            ]
        )

    return [
        "## Evidence Catalog",
        "",
        *_table(
            ["Evidence ID", "Type", "Source", "Summary"],
            rows,
        ),
        "",
    ]


def _bullet_section(
    title: str,
    items: list[Any],
    *,
    heading_level: int = 3,
) -> list[str]:
    hashes = "#" * heading_level

    return [
        f"{hashes} {title}",
        "",
        *_bullets(items),
        "",
    ]


def _bullets(items: list[Any]) -> list[str]:
    if not items:
        return ["- None specified."]

    return [f"- {_text(item)}" for item in items]


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["No items specified."]

    lines = [
        "| " + " | ".join(_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for row in rows:
        normalized_row = list(row)

        if len(normalized_row) < len(headers):
            normalized_row.extend([""] * (len(headers) - len(normalized_row)))

        if len(normalized_row) > len(headers):
            normalized_row = normalized_row[: len(headers)]

        lines.append("| " + " | ".join(_cell(value) for value in normalized_row) + " |")

    return lines


def _cell(value: Any) -> str:
    return _text(value).replace("|", "\\|").replace("\n", " ")


def _text(value: Any) -> str:
    if value is None:
        return "Not specified"

    if isinstance(value, bool):
        return _yes_no(value)

    if isinstance(value, list):
        return ", ".join(_text(item) for item in value)

    if isinstance(value, dict):
        return ", ".join(f"{key}: {_text(item)}" for key, item in value.items())

    text = str(value).strip()

    return text if text else "Not specified"


def _yes_no(value: Any) -> str:
    if value is True:
        return "Yes"

    if value is False:
        return "No"

    return "Not specified"


def _refs(refs: list[Any]) -> str:
    if not refs:
        return "None"

    return ", ".join(f"`{_text(ref)}`" for ref in refs)