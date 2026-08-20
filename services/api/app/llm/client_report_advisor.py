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
        "recommended_product_concept",
        "non_obvious_insights",
        "highest_value_use_cases",
        "where_agents_are_not_ready_yet",
        "recommended_first_build",
        "controls_and_human_review",
        "implementation_roadmap",
        "success_metrics",
        "open_questions",
        "packet_quality_findings"
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

        "highest_value_use_cases": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "use_case",
                    "why_it_matters",
                    "recommended_autonomy",
                    "business_value",
                ],
                "properties": {
                    "use_case": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "recommended_autonomy": {"type": "string"},
                    "business_value": {"type": "string"},
                },
            },
        },

        "packet_quality_findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "severity",
                    "finding",
                    "evidence_reference",
                    "why_it_matters",
                    "recommended_resolution",
                    "detection_source",
                ],
                "properties": {
                    "severity": {"type": "string"},
                    "finding": {"type": "string"},
                    "evidence_reference": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "recommended_resolution": {"type": "string"},
                    "detection_source": {"type": "string"},
                },
            },
        },

        "non_obvious_insights": {
            "type": "array",
            "items": {"type": "string"},
        },
        
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
                
    },
}


SYSTEM_INSTRUCTIONS = """
You are a senior AI transformation consultant preparing a client-facing workflow AI assessment.

Write for business and technology leaders. Be specific, practical, candid, and concise. Make a clear recommendation about what to build first, what not to automate yet, and why.

Use only the supplied workflow packet, LLM workflow analysis, readiness blueprint, and packet-quality review as evidence. Do not invent workflow facts, systems, approvals, roles, policies, metrics, or constraints.

For cost, you may provide an order-of-magnitude planning range when exact pricing is not supported, but only when you clearly label it as planning guidance rather than a vendor quote. Make the uncertainty visible by stating confidence level, assumptions, exclusions, and inputs needed to refine the estimate.

You may synthesize strategic implications from the evidence, but distinguish documented facts from interpretation. When risk, readiness, business value, cost, or ROI depends on missing information, say so directly.

Avoid generic AI hype, compliance-checklist language, and repeated safety disclaimers. Prefer clear consulting language over cautious system language.

Do not recommend autonomous write actions, external communications, release, disclosure, denial, closure, fee actions, redaction execution, or system updates unless the provided readiness blueprint explicitly supports them.

Make packet-quality findings a visible part of the product value. Do not hide material findings merely to shorten the report. Compress lower-severity findings when needed, but preserve traceability and actionability.

The final report should help an executive understand four things: where AI can create value, where the workflow is not ready, what the safest useful first build should be, and what issues the packet-quality review surfaced that must be resolved before broader automation.
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
            "The report should be readable, strategic, concise, and specific to the workflow.",
            "Target total report length: 2,000 to 3,400 words when packet-quality findings are substantial. Prioritize complete material finding inventory over forcing the report below target length.",
            "Prefer fewer, stronger findings over exhaustive lists.",
            "Do not restate the same recommendation across sections.",
            "Each section must add new information rather than repeat the Executive Brief.",
            "State major no-go boundaries only in the Executive Brief and Controls and Human Review section unless a specific finding requires mention elsewhere.",
            "Limit Non-Obvious Insights to 5 bullets.",
            "Limit Highest-Value AI Use Cases to 4 use cases.",
            "Limit Controls and Human Review to 6 to 8 controls.",
            "Limit Implementation Roadmap to 4 phases.",
            "Limit Success Metrics to 6 to 8 metrics.",
            "Limit Open Questions to 8 questions.",
            "Use the provided materials as evidence. Do not invent facts not supported by these materials.",
            "For cost, provide an order-of-magnitude planning range when exact pricing is not supported. Make uncertainty visible with confidence, assumptions, exclusions, and inputs needed. Label the range as planning guidance, not a vendor quote.",
            "For ROI, distinguish theoretical value ceiling from forecast. State confidence, exclusions, and required inputs rather than pretending precision.",
            "The PACKET QUALITY REVIEW is mandatory governance evidence when provided.",
            "Packet Quality Findings must be a complete material finding inventory, not a severity-filtered summary.",
            "Include all reconciled packet-quality findings supplied by the packet-quality review, regardless of severity, up to 12 findings.",
            "If more than 12 reconciled findings are supplied, include all Critical and High findings, then summarize Medium and Low findings by theme.",
            "Do not omit Medium or Low findings solely to reduce report length; compress their prose instead.",
            "Critical and High findings should include clear why-it-matters and recommended-resolution language.",
            "Medium and Low findings should be concise but still traceable and actionable.",
            "If a client no-go list, governance boundary, or automation policy omits irreversible external actions, consequential workflow decisions, or write actions, include that as a Critical packet-quality finding.",
            "Use packet record IDs when provided, such as REC-002. Do not replace them with generic phrases or altered IDs.",
            "Detection source must clearly identify the primary detection layer as either deterministic or adversarial.",
            "Do not bury packet-quality defects only inside recommendations, roadmap items, controls, or Open Questions.",
            "Packet-quality defects should appear as distinct Packet Quality Findings when they are material, traceable, and actionable, even if severity is Medium or Low.",
            "If a finding concerns vague escalation authority, missing appeal/challenge path, undeclared ownership, missing participant authority, missing system inventory, or omitted irreversible actions, include it as a distinct packet-quality finding when supported by the packet-quality review.",
            "Do not repeat the same packet-quality finding across assessment verdict, executive summary, controls, roadmap, and open questions.",
            "Critical and High packet-quality findings must appear in the Packet Quality Findings section, not only in narrative discussion or Open Questions.",
            "Do not claim the workflow is model-safe, release-ready, automation-ready, or suitable for the recommended first build unless the report explains how critical packet-quality findings are constrained, remediated, or excluded from scope.",
            "Do not include workflow_id, run_id, local run IDs, test slugs, file paths, policy-server names, evaluation-profile names, unrelated harness/configuration issues, or implementation/debug identifiers in client-facing text.",
            "Use the business workflow name only. If the supplied artifacts contain conflicting internal identifiers, omit them from the client report and focus on the business workflow.",
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
        strict=True,
    )

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

    _sanitize_client_facing_report_title(
        report=report,
        workflow_id=workflow_id,
        run_id=run_id,
    )

    _validate_client_assessment_report(report)

    return report


def _sanitize_client_facing_report_title(
    *,
    report: dict[str, Any],
    workflow_id: str,
    run_id: str,
) -> None:
    title = str(report.get("report_title") or "").strip()

    if " (workflow_id=" in title:
        title = title.split(" (workflow_id=", 1)[0].strip()

    for token in [workflow_id, run_id]:
        title = title.replace(token, "").strip(" -_(),")

    report["report_title"] = title or "AI Workflow Assessment"


def _validate_no_internal_client_leaks(
    report: dict[str, Any],
    *,
    workflow_id: str,
    run_id: str,
) -> None:
    client_facing_report = {
        key: value
        for key, value in report.items()
        if key != "metadata"
    }

    serialized = json.dumps(client_facing_report, ensure_ascii=False).lower()

    blocked_terms = [
        workflow_id.lower(),
        run_id.lower(),
        "workflow_id=",
        "run_id=",
        "public_records_test",
        "run_local_",
        "policy-server",
        "policy_server",
        "employee-access workflow",
        "employee access workflow",
    ]

    found_terms = sorted(
        {
            term
            for term in blocked_terms
            if term and term in serialized
        }
    )

    if found_terms:
        raise ValueError(
            "Generated report contains internal implementation identifiers: "
            + ", ".join(found_terms)
        )

def _validate_client_assessment_report(report: dict[str, Any]) -> None:
    _validate_executive_brief(report)

    required_string_fields = [
        "report_title",
    ]

    for field_name in required_string_fields:
        _require_nonblank_string(report, field_name, f"Generated report.{field_name}")

    required_list_fields = [
        "non_obvious_insights",
        "highest_value_use_cases",
        "where_agents_are_not_ready_yet",
        "controls_and_human_review",
        "implementation_roadmap",
        "success_metrics",
        "open_questions",
        "packet_quality_findings",
    ]

    for field_name in required_list_fields:
        _require_nonempty_list(report, field_name, f"Generated report.{field_name}")

    product_concept = _require_nonempty_dict(
        report,
        "recommended_product_concept",
        "Generated report.recommended_product_concept",
    )
    _validate_recommended_product_concept(product_concept)

    first_build = _require_nonempty_dict(
        report,
        "recommended_first_build",
        "Generated report.recommended_first_build",
    )
    _validate_recommended_first_build(first_build)

    metadata = _require_nonempty_dict(report, "metadata", "Generated report.metadata")

    for index, item in enumerate(report["highest_value_use_cases"]):
        if not isinstance(item, dict):
            raise ValueError(
                f"Generated report.highest_value_use_cases[{index}] is not an object."
            )
        for field_name in [
            "use_case",
            "why_it_matters",
            "recommended_autonomy",
            "business_value",
        ]:
            _require_nonblank_string(
                item,
                field_name,
                f"Generated report.highest_value_use_cases[{index}].{field_name}",
            )

    for index, item in enumerate(report["packet_quality_findings"]):
        if not isinstance(item, dict):
            raise ValueError(
                f"Generated report.packet_quality_findings[{index}] is not an object."
            )

        for field_name in [
            "severity",
            "finding",
            "evidence_reference",
            "why_it_matters",
            "recommended_resolution",
            "detection_source",
        ]:
            _require_nonblank_string(
                item,
                field_name,
                f"Generated report.packet_quality_findings[{index}].{field_name}",
            )

    for index, item in enumerate(report["controls_and_human_review"]):
        if not isinstance(item, dict):
            raise ValueError(
                f"Generated report.controls_and_human_review[{index}] is not an object."
            )
        for field_name in ["control_area", "recommendation", "reason"]:
            _require_nonblank_string(
                item,
                field_name,
                f"Generated report.controls_and_human_review[{index}].{field_name}",
            )

    for index, item in enumerate(report["implementation_roadmap"]):
        if not isinstance(item, dict):
            raise ValueError(
                f"Generated report.implementation_roadmap[{index}] is not an object."
            )
        for field_name in ["phase", "focus", "outcome"]:
            _require_nonblank_string(
                item,
                field_name,
                f"Generated report.implementation_roadmap[{index}].{field_name}",
            )

    workflow_id = str(metadata.get("workflow_id") or "")
    run_id = str(metadata.get("run_id") or "")

    _validate_no_internal_client_leaks(
        report,
        workflow_id=workflow_id,
        run_id=run_id,
    )
    # Do not hard-fail on report length after a paid model call.
    # Length is checked as a post-run quality signal instead.


def _validate_recommended_product_concept(product_concept: dict[str, Any]) -> None:
    for field_name in [
        "name",
        "one_sentence_pitch",
        "workflow_moment",
        "demo_moment",
    ]:
        _require_nonblank_string(
            product_concept,
            field_name,
            f"Generated report.recommended_product_concept.{field_name}",
        )

    for field_name in [
        "target_users",
        "sample_assistant_output",
        "what_ai_does",
        "what_ai_does_not_do",
    ]:
        _require_nonempty_list(
            product_concept,
            field_name,
            f"Generated report.recommended_product_concept.{field_name}",
        )

    before_after = _require_nonempty_dict(
        product_concept,
        "before_after",
        "Generated report.recommended_product_concept.before_after",
    )

    for field_name in ["before", "after"]:
        _require_nonblank_string(
            before_after,
            field_name,
            f"Generated report.recommended_product_concept.before_after.{field_name}",
        )

    for index, item in enumerate(product_concept["sample_assistant_output"]):
        if not isinstance(item, dict):
            raise ValueError(
                "Generated report.recommended_product_concept."
                f"sample_assistant_output[{index}] is not an object."
            )
        for field_name in ["label", "value"]:
            _require_nonblank_string(
                item,
                field_name,
                "Generated report.recommended_product_concept."
                f"sample_assistant_output[{index}].{field_name}",
            )

def _validate_recommended_first_build(first_build: dict[str, Any]) -> None:
    for field_name in [
        "name",
        "description",
        "why_this_first",
        "what_it_should_not_do",
        "expected_user_experience",
    ]:
        _require_nonblank_string(
            first_build,
            field_name,
            f"Generated report.recommended_first_build.{field_name}",
        )


def _require_nonblank_string(
    source: dict[str, Any],
    field_name: str,
    label: str,
) -> str:
    value = source.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is blank.")
    return value


def _require_nonempty_list(
    source: dict[str, Any],
    field_name: str,
    label: str,
) -> list[Any]:
    value = source.get(field_name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} is blank.")

    if not any(_has_nonblank_content(item) for item in value):
        raise ValueError(f"{label} is blank.")

    return value


def _require_nonempty_dict(
    source: dict[str, Any],
    field_name: str,
    label: str,
) -> dict[str, Any]:
    value = source.get(field_name)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} is missing.")

    if not _has_nonblank_content(value):
        raise ValueError(f"{label} is blank.")

    return value


def _has_nonblank_content(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, list):
        return any(_has_nonblank_content(item) for item in value)

    if isinstance(value, dict):
        return any(_has_nonblank_content(item) for item in value.values())

    return True

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

    lines.append("## Packet Quality Findings")
    lines.append("")

    severity_rank = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    packet_quality_findings = sorted(
        report.get("packet_quality_findings", []),
        key=lambda item: (
            severity_rank.get(str(item.get("severity", "")).strip().lower(), 99),
            str(item.get("finding", "")).strip().lower(),
        ),
    )

    for item in packet_quality_findings:
    
        lines.append(f"### {item.get('severity')}: {item.get('finding')}")
        lines.append("")
        lines.append(f"**Evidence reference:** {item.get('evidence_reference')}")
        lines.append("")
        lines.append(f"**Why it matters:** {item.get('why_it_matters')}")
        lines.append("")
        lines.append(f"**Recommended resolution:** {item.get('recommended_resolution')}")
        lines.append("")
        lines.append(f"**Detection source:** {item.get('detection_source')}")
        lines.append("")

    lines.append("## Non-Obvious Insights")
    lines.append("")
    for item in report.get("non_obvious_insights", []):
        lines.append(f"- {item}")
    lines.append("")

    
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