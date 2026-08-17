from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.llm.provider import generate_structured_analysis


CLIENT_ASSESSMENT_REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "report_title",
        "executive_brief",
        "assessment_verdict",
        "executive_summary",
        "recommended_product_concept",
        "non_obvious_insights",
        "executive_decisions_needed",
        "ai_opportunity_thesis",
        "what_the_workflow_is_really_asking_for",
        "highest_value_use_cases",
        "where_agents_are_not_ready_yet",
        "recommended_first_build",
        "future_state_workflow",
        "controls_and_human_review",
        "implementation_roadmap",
        "success_metrics",
        "open_questions",
        "closing_recommendation",
        "metadata",
    ],
    "properties": {
        "report_title": {"type": "string"},
        "executive_brief": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "recommendation",
                "first_build",
                "why_this_first",
                "estimated_effort",
                "estimated_cost",
                "roi_value_hypothesis",
                "executive_decisions",
            ],
            "properties": {
                "recommendation": {"type": "string"},
                "first_build": {"type": "string"},
                "why_this_first": {"type": "string"},
                "estimated_effort": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["duration", "workstreams", "confidence"],
                    "properties": {
                        "duration": {"type": "string"},
                        "workstreams": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "string"},
                    },
                },
                "estimated_cost": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["range", "assumptions", "confidence"],
                    "properties": {
                        "range": {"type": "string"},
                        "assumptions": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "string"},
                    },
                },
                "roi_value_hypothesis": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "expected_value",
                        "not_counted_yet",
                        "inputs_needed_to_quantify",
                        "confidence",
                    ],
                    "properties": {
                        "expected_value": {"type": "array", "items": {"type": "string"}},
                        "not_counted_yet": {"type": "array", "items": {"type": "string"}},
                        "inputs_needed_to_quantify": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "string"},
                    },
                },
                "executive_decisions": {"type": "array", "items": {"type": "string"}},
            },
        },
        "executive_summary": {"type": "string"},
        "recommended_product_concept": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "name",
                "one_sentence_pitch",
                "target_users",
                "workflow_moment",
                "before_after",
                "sample_assistant_output",
                "what_ai_does",
                "what_ai_does_not_do",
                "demo_moment",
            ],
            "properties": {
                "name": {"type": "string"},
                "one_sentence_pitch": {"type": "string"},
                "target_users": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "workflow_moment": {"type": "string"},
                "before_after": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["before", "after"],
                    "properties": {
                        "before": {"type": "string"},
                        "after": {"type": "string"},
                    },
                },
                "sample_assistant_output": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["label", "value"],
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                        },
                    },
                },
                "what_ai_does": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "what_ai_does_not_do": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "demo_moment": {"type": "string"},
            },
        },
        "ai_opportunity_thesis": {"type": "string"},
        "what_the_workflow_is_really_asking_for": {"type": "string"},
        "highest_value_use_cases": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["use_case", "why_it_matters", "recommended_autonomy", "business_value"],
                "properties": {
                    "use_case": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "recommended_autonomy": {"type": "string"},
                    "business_value": {"type": "string"},
                },
            },
        },
        "assessment_verdict": {"type": "string"},
        "non_obvious_insights": {
            "type": "array",
            "items": {"type": "string"},
        },
        "executive_decisions_needed": {
            "type": "array",
            "items": {"type": "string"},
        },
        "where_agents_are_not_ready_yet": {
            "type": "array",
            "items": {"type": "string"},
        },
        "recommended_first_build": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "name",
                "description",
                "why_this_first",
                "what_it_should_not_do",
                "expected_user_experience",
            ],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "why_this_first": {"type": "string"},
                "what_it_should_not_do": {"type": "string"},
                "expected_user_experience": {"type": "string"},
            },
        },
        "future_state_workflow": {"type": "string"},
        "controls_and_human_review": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["control_area", "recommendation", "reason"],
                "properties": {
                    "control_area": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
        },
        "implementation_roadmap": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["phase", "focus", "outcome"],
                "properties": {
                    "phase": {"type": "string"},
                    "focus": {"type": "string"},
                    "outcome": {"type": "string"},
                },
            },
        },
        "success_metrics": {
            "type": "array",
            "items": {"type": "string"},
        },
        "open_questions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "closing_recommendation": {"type": "string"},
        "metadata": {
            "type": "object",
            "additionalProperties": True,
        },
    },
}


SYSTEM_INSTRUCTIONS = """
You are a senior AI transformation consultant preparing a client-facing workflow AI assessment.

Your job is to turn structured workflow evidence, LLM workflow analysis, and the agentic readiness blueprint into a persuasive but grounded report.

Important balance:
- Be more insightful than a compliance checklist.
- Identify non-obvious opportunities and workflow redesign implications.
- You are expected to synthesize strategic implications from the evidence, as long as you clearly distinguish interpretation from documented fact.
- You may recommend future-state workflow improvements.
- You may be candid about risk, organizational readiness, missing data, and where automation should not be used yet.
- Do not invent workflow facts, systems, approvals, actors, or policies.
- Clearly separate grounded observations from strategic interpretation.
- Do not recommend autonomous write actions unless the blueprint supports them.
- Preserve human approval where the evidence or blueprint requires it.
- Write for business and technology leaders, not engineers.
- Avoid generic AI hype.
- Avoid dry artifact language.
- Make the report feel useful enough that a leader would want to discuss it with their team.
- Do not merely summarize the source artifacts. Make clear strategic judgments.
- Start with a decisive assessment verdict in the executive summary.
- Name the recommended first build clearly and explain why it is the right starting point.
- Include at least three non-obvious insights that a workflow owner may not have considered.
- Be willing to say "do not automate this yet" when autonomy would create risk.
- Prefer concrete consulting language over cautious system language.
- Use phrases like "The first build should...", "Do not start with...", "The hidden value is...", and "The main readiness gap is..." when supported by evidence.
- Make the report feel like it came from a senior AI implementation advisor who is trying to help an executive decide what to build first, what not to build yet, and why.
- Write with a clear point of view. The report should make a recommendation, not just list observations.
- Use executive consulting language: "The real opportunity is...", "The first build should...", "Do not start with...", "The hidden bottleneck is...", "The unlock is..."
- Avoid repeating safety constraints in every section. State the major boundaries clearly, then focus on business value, user experience, and implementation strategy.
- Make the recommendation feel like a product concept, not just a control posture.
- Describe what the first build would actually do for a user during the workflow.
- Include practical examples of the assistant's output or behavior when useful.
- Explain why the recommended first build is better than the obvious but riskier automation target.
- Prioritize insight over completeness. Do not turn every section into a checklist.
- The executive summary should open with a verdict sentence, then a product recommendation, then the primary business reason, then the main constraint.
- Keep the executive summary to two concise paragraphs.
- For the recommended product concept, avoid generic capability descriptions.
- Describe one concrete moment in the workflow where the product changes the user's experience.
- Include a sample assistant output that looks like something the user would actually see on screen.
- Make the product concept section suitable for a live demo or hiring-manager walkthrough.
- Avoid vague benefit language such as "improves efficiency" unless you explain exactly what work changes.
""".strip()


def generate_client_assessment_report(
    *,
    workflow_id: str,
    run_id: str,
    normalized_packet: dict[str, Any],
    llm_workflow_analysis: dict[str, Any],
    agentic_readiness_blueprint: dict[str, Any],
    packet_quality_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()

    packet_quality_review_prompt = (
        json.dumps(packet_quality_review, indent=2, default=str)
        if packet_quality_review
        else "Not provided."
    )

    user_prompt = "\n\n".join(
        [
            f"Create a client-facing AI workflow assessment report for workflow_id={workflow_id}, run_id={run_id}.",
            "The report should be readable, strategic, and specific to the workflow.",
            "Start with a one-page executive brief suitable for a C-level reader.",
            "The executive brief must answer: proceed or not, what to build first, why, what it will take, what it may cost if assumptions allow, expected ROI/value, and what decisions are needed.",
            "For cost and ROI, do not fake precision. Provide ranges, confidence, assumptions, and inputs needed to quantify when exact values are not supported.",
            "Use the provided materials as evidence. Do not invent facts not supported by these materials.",
            "You may offer strategic interpretation and future-state recommendations when clearly grounded in the materials.",
            "The PACKET QUALITY REVIEW is mandatory governance evidence when provided.",
            "You must explicitly address every reconciled critical/high packet-quality finding in the assessment verdict, executive summary, recommended first build, controls, roadmap, or open questions.",
            "Do not claim the workflow is model-safe, release-ready, automation-ready, or suitable for the recommended first build unless the report explains how critical packet-quality findings are constrained, remediated, or excluded from scope.",
            "Do not bury critical packet-quality findings only in open questions.",
            "Return only the structured JSON requested by the schema.",
            "",
            "NORMALIZED WORKFLOW PACKET:",
            json.dumps(normalized_packet, indent=2, default=str),
            "",
            "LLM WORKFLOW ANALYSIS:",
            json.dumps(llm_workflow_analysis, indent=2, default=str),
            "",
            "AGENTIC READINESS BLUEPRINT:",
            json.dumps(agentic_readiness_blueprint, indent=2, default=str),
            "",
            "PACKET QUALITY REVIEW:",
            packet_quality_review_prompt,
        ]
    )

    report = generate_structured_analysis(
        system_instructions=SYSTEM_INSTRUCTIONS,
        user_prompt=user_prompt,
        json_schema=CLIENT_ASSESSMENT_REPORT_SCHEMA,
        schema_name="client_assessment_report",
    )

    _validate_executive_brief(report)

    report["metadata"] = {
        **report.get("metadata", {}),
        "workflow_id": workflow_id,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "model": settings.openai_model,
        "reasoning_effort": settings.openai_reasoning_effort,
        "report_type": "client_assessment_report",
        "source_artifacts": [
            "normalized_packet",
            "llm_workflow_analysis",
            "agentic_readiness_blueprint",
            *(
                ["packet_quality_review"]
                if packet_quality_review
                else []
            ),
        ],
    }

    return report


def _validate_executive_brief(report: dict[str, Any]) -> None:
    executive_brief = report.get("executive_brief")

    if not isinstance(executive_brief, dict):
        raise ValueError("Generated report is missing executive_brief.")

    required_string_fields = [
        "recommendation",
        "first_build",
        "why_this_first",
    ]

    for field_name in required_string_fields:
        value = executive_brief.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Generated executive_brief.{field_name} is blank.")

    executive_decisions = executive_brief.get("executive_decisions")
    if not isinstance(executive_decisions, list) or not executive_decisions:
        raise ValueError("Generated executive_brief.executive_decisions is blank.")

    for object_field in [
        "estimated_effort",
        "estimated_cost",
        "roi_value_hypothesis",
    ]:
        value = executive_brief.get(object_field)
        if not isinstance(value, dict):
            raise ValueError(f"Generated executive_brief.{object_field} is missing.")


def render_client_assessment_report_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append(f"# {report.get('report_title', 'AI Workflow Assessment Report')}")
    lines.append("")

    _render_executive_brief(lines, report.get("executive_brief", {}))

    _section(lines, "Assessment Verdict", report.get("assessment_verdict"))
    _section(lines, "Executive Summary", report.get("executive_summary"))

    product_concept = report.get("recommended_product_concept", {})

    lines.append("## Recommended Product Concept")
    lines.append("")

    lines.append(f"### {product_concept.get('name', 'Recommended Product Concept')}")
    lines.append("")

    lines.append(f"**Pitch:** {product_concept.get('one_sentence_pitch', '')}")
    lines.append("")

    lines.append("**Target users:**")
    lines.append("")
    for item in product_concept.get("target_users", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("**Workflow moment:**")
    lines.append("")
    lines.append(product_concept.get("workflow_moment", ""))
    lines.append("")

    before_after = product_concept.get("before_after", {})

    lines.append("**Before:**")
    lines.append("")
    lines.append(before_after.get("before", ""))
    lines.append("")

    lines.append("**After:**")
    lines.append("")
    lines.append(before_after.get("after", ""))
    lines.append("")

    lines.append("**Sample assistant output:**")
    lines.append("")
    for item in product_concept.get("sample_assistant_output", []):
        lines.append(f"- **{item.get('label')}:** {item.get('value')}")
    lines.append("")

    lines.append("**What AI does:**")
    lines.append("")
    for item in product_concept.get("what_ai_does", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("**What AI does not do:**")
    lines.append("")
    for item in product_concept.get("what_ai_does_not_do", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("**Demo moment:**")
    lines.append("")
    lines.append(product_concept.get("demo_moment", ""))
    lines.append("")

    lines.append("## Non-Obvious Insights")
    lines.append("")
    for item in report.get("non_obvious_insights", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Executive Decisions Needed")
    lines.append("")
    for item in report.get("executive_decisions_needed", []):
        lines.append(f"- {item}")
    lines.append("")

    _section(lines, "AI Opportunity Thesis", report.get("ai_opportunity_thesis"))
    _section(
        lines,
        "What This Workflow Is Really Asking For",
        report.get("what_the_workflow_is_really_asking_for"),
    )

    lines.append("## Highest-Value AI Use Cases")
    lines.append("")
    for item in report.get("highest_value_use_cases", []):
        lines.append(f"### {item.get('use_case')}")
        lines.append("")
        lines.append(f"**Why it matters:** {item.get('why_it_matters')}")
        lines.append("")
        lines.append(f"**Recommended autonomy:** {item.get('recommended_autonomy')}")
        lines.append("")
        lines.append(f"**Business value:** {item.get('business_value')}")
        lines.append("")
    
    lines.append("## Where Agents Are Not Ready Yet")
    lines.append("")
    for item in report.get("where_agents_are_not_ready_yet", []):
        lines.append(f"- {item}")
    lines.append("")

    first_build = report.get("recommended_first_build", {})
    lines.append("## Recommended First Build")
    lines.append("")
    lines.append(f"### {first_build.get('name', 'Recommended First Build')}")
    lines.append("")
    lines.append(first_build.get("description", ""))
    lines.append("")
    lines.append(f"**Why this first:** {first_build.get('why_this_first', '')}")
    lines.append("")
    lines.append(f"**What it should not do:** {first_build.get('what_it_should_not_do', '')}")
    lines.append("")
    lines.append(f"**Expected user experience:** {first_build.get('expected_user_experience', '')}")
    lines.append("")

    _section(lines, "Future-State Workflow", report.get("future_state_workflow"))

    lines.append("## Controls and Human Review")
    lines.append("")
    for item in report.get("controls_and_human_review", []):
        lines.append(f"### {item.get('control_area')}")
        lines.append("")
        lines.append(f"**Recommendation:** {item.get('recommendation')}")
        lines.append("")
        lines.append(f"**Reason:** {item.get('reason')}")
        lines.append("")

    lines.append("## Implementation Roadmap")
    lines.append("")
    for item in report.get("implementation_roadmap", []):
        lines.append(f"### {item.get('phase')}")
        lines.append("")
        lines.append(f"**Focus:** {item.get('focus')}")
        lines.append("")
        lines.append(f"**Outcome:** {item.get('outcome')}")
        lines.append("")

    lines.append("## Success Metrics")
    lines.append("")
    for item in report.get("success_metrics", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Open Questions")
    lines.append("")
    for item in report.get("open_questions", []):
        lines.append(f"- {item}")
    lines.append("")

    _section(lines, "Closing Recommendation", report.get("closing_recommendation"))

    return "\n".join(lines).strip() + "\n"


def _render_executive_brief(lines: list[str], executive_brief: dict[str, Any]) -> None:
    lines.append("## Executive Brief")
    lines.append("")

    lines.append(f"**Recommendation:** {executive_brief.get('recommendation', '')}")
    lines.append("")
    lines.append(f"**First build:** {executive_brief.get('first_build', '')}")
    lines.append("")
    lines.append(f"**Why this first:** {executive_brief.get('why_this_first', '')}")
    lines.append("")

    estimated_effort = executive_brief.get("estimated_effort", {})
    lines.append("**Estimated effort:**")
    lines.append("")
    lines.append(f"- Duration: {estimated_effort.get('duration', '')}")
    lines.append(f"- Confidence: {estimated_effort.get('confidence', '')}")
    lines.append("- Workstreams:")
    for item in estimated_effort.get("workstreams", []):
        lines.append(f"  - {item}")
    lines.append("")

    estimated_cost = executive_brief.get("estimated_cost", {})
    lines.append("**Estimated cost:**")
    lines.append("")
    lines.append(f"- Range: {estimated_cost.get('range', '')}")
    lines.append(f"- Confidence: {estimated_cost.get('confidence', '')}")
    lines.append("- Assumptions:")
    for item in estimated_cost.get("assumptions", []):
        lines.append(f"  - {item}")
    lines.append("")

    roi = executive_brief.get("roi_value_hypothesis", {})
    lines.append("**ROI / value hypothesis:**")
    lines.append("")
    lines.append(f"- Confidence: {roi.get('confidence', '')}")
    lines.append("- Expected value:")
    for item in roi.get("expected_value", []):
        lines.append(f"  - {item}")
    lines.append("- Not counted yet:")
    for item in roi.get("not_counted_yet", []):
        lines.append(f"  - {item}")
    lines.append("- Inputs needed to quantify:")
    for item in roi.get("inputs_needed_to_quantify", []):
        lines.append(f"  - {item}")
    lines.append("")

    lines.append("**Executive decisions needed:**")
    lines.append("")
    for item in executive_brief.get("executive_decisions", []):
        lines.append(f"- {item}")
    lines.append("")


def _section(lines: list[str], title: str, content: str | None) -> None:
    lines.append(f"## {title}")
    lines.append("")
    lines.append(content or "")
    lines.append("")