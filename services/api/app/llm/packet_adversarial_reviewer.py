from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.llm.provider import generate_structured_analysis


PACKET_ADVERSARIAL_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "review_verdict",
        "advisory_findings",
        "client_report_guidance",
        "metadata",
    ],
    "properties": {
        "review_verdict": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "overall_assessment",
                "critical_risk_summary",
                "readiness_implication",
                "confidence",
            ],
            "properties": {
                "overall_assessment": {"type": "string"},
                "critical_risk_summary": {"type": "string"},
                "readiness_implication": {"type": "string"},
                "confidence": {"type": "string"},
            },
        },
        "advisory_findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "finding_id",
                    "severity",
                    "category",
                    "finding_type",
                    "title",
                    "evidence",
                    "packet_claim_challenged",
                    "reasoning",
                    "ai_readiness_implication",
                    "recommended_remediation",
                    "confidence",
                    "deterministic_supporting_finding_ids",
                ],
                "properties": {
                    "finding_id": {"type": "string"},
                    "severity": {"type": "string"},
                    "category": {"type": "string"},
                    "finding_type": {
                        "type": "string",
                        "description": "One of: proven_contradiction, unsupported_claim, missing_boundary, implementation_constraint, semantic_concern.",
                    },
                    "title": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "source",
                                "claim_id",
                                "quote_or_value",
                            ],
                            "properties": {
                                "source": {"type": "string"},
                                "claim_id": {"type": "string"},
                                "quote_or_value": {"type": "string"},
                            },
                        },
                    },
                    "packet_claim_challenged": {"type": "string"},
                    "reasoning": {"type": "string"},
                    "ai_readiness_implication": {"type": "string"},
                    "recommended_remediation": {"type": "string"},
                    "confidence": {"type": "string"},
                    "deterministic_supporting_finding_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "client_report_guidance": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "must_address_in_client_report",
                "claims_the_final_report_must_not_make",
                "recommended_first_build_constraints",
                "executive_summary_warning",
            ],
            "properties": {
                "must_address_in_client_report": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "claims_the_final_report_must_not_make": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "recommended_first_build_constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "executive_summary_warning": {"type": "string"},
            },
        },
        "metadata": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "created_at",
                "workflow_id",
                "workflow_name",
                "input_claim_count",
                "deterministic_finding_count",
            ],
            "properties": {
                "created_at": {"type": "string"},
                "workflow_id": {"type": "string"},
                "workflow_name": {"type": "string"},
                "input_claim_count": {"type": "integer"},
                "deterministic_finding_count": {"type": "integer"},
            },
        },
    },
}


SYSTEM_INSTRUCTIONS = """
You are an adversarial AI readiness reviewer.

You are not writing a client report.
You are reviewing a completed Workflow Packet as a set of claims that may be incomplete, inconsistent, or misleading.

Your job is to identify judgment-level risks that deterministic validation may not prove.

Important principles:
- Do not treat the packet's own governance flags as ground truth.
- Challenge claims that appear unsupported, incomplete, contradictory, or unsafe.
- Use deterministic findings as evidence, but look for additional semantic risks.
- Do not invent defects. Every finding must cite packet evidence.
- Prefer fewer, higher-value findings over a long list of generic concerns.
- Assign each finding a finding_type: proven_contradiction, unsupported_claim, missing_boundary, implementation_constraint, or semantic_concern.
- Distinguish proven contradictions from advisory concerns.
- Explicitly review whether AI no-go areas cover high-consequence actions such as release, delivery, disclosure, external communication, legal determination, approval, denial, closure, write/update actions, fees, or irreversible workflow outcomes.
- Treat scoped exclusions as constraints, not defects, unless the packet contradicts itself or proposes AI use inside the excluded scope.
- Do not treat legally allowed bypasses as defects unless the packet creates ambiguity about AI-originated recommendations, final authority, evidence, or control enforcement.
- Focus on AI readiness: model context, autonomy boundaries, human review, controls, no-go areas, and safe first build scope.

Look especially for:
- Data fields whose handling looks unsafe or unsupported.
- High-consequence actions not clearly covered by AI no-go boundaries or human review.
- Workflow states or sample records that contradict stated controls.
- Controls that exist on paper but lack enforceability.
- Process branches implied by statuses, controls, or sample records but missing from workflow steps.
- Escalation, approval, denial, closure, delivery, release, write, or external communication gaps.
- Recommendations the final report must avoid unless these gaps are remediated.
"""


def generate_packet_adversarial_review(
    *,
    packet_claim_graph: dict[str, Any],
    deterministic_review: dict[str, Any],
) -> dict[str, Any]:
    review_input = _build_review_input(packet_claim_graph, deterministic_review)

    user_prompt = (
        "Review this Workflow Packet claim graph and deterministic review.\n\n"
        "Your output must identify the most important advisory findings that affect AI readiness.\n"
        "Do not summarize the packet. Challenge it.\n\n"
        "Return findings that a sophisticated client or hiring manager would consider meaningful.\n"
        "You must explicitly consider whether the AI no-go areas are complete for the workflow's highest-consequence actions.\n"
        "Do not create a finding just to satisfy that instruction; create one only when packet evidence supports it.\n\n"
        "Review input follows as JSON:\n"
        f"{json.dumps(review_input, indent=2)}"
    )

    result = generate_structured_analysis(
        system_instructions=SYSTEM_INSTRUCTIONS,
        user_prompt=user_prompt,
        json_schema=PACKET_ADVERSARIAL_REVIEW_SCHEMA,
        schema_name="packet_adversarial_review",
        stage="packet_adversarial_review",
    )

    result.setdefault("metadata", {})
    result["metadata"]["created_at"] = datetime.now(UTC).isoformat()
    result["metadata"]["workflow_id"] = packet_claim_graph.get("workflow_id") or ""
    result["metadata"]["workflow_name"] = packet_claim_graph.get("workflow_name") or ""
    result["metadata"]["input_claim_count"] = int(
        packet_claim_graph.get("metadata", {}).get("claim_count") or 0
    )
    result["metadata"]["deterministic_finding_count"] = int(
        deterministic_review.get("summary", {}).get("finding_count") or 0
    )

    return result


def _build_review_input(
    packet_claim_graph: dict[str, Any],
    deterministic_review: dict[str, Any],
) -> dict[str, Any]:
    claims = packet_claim_graph.get("claims", [])

    return {
        "workflow_id": packet_claim_graph.get("workflow_id"),
        "workflow_name": packet_claim_graph.get("workflow_name"),
        "overview": _overview_map(claims),
        "participants": _participant_list(claims),
        "ai_no_go_areas": _ai_no_go_list(claims),
        "workflow_steps": _claims_for_review(claims, "workflow_step_claim"),
        "policy_controls": _claims_for_review(claims, "policy_control_claim"),
        "data_dictionary": _claims_for_review(claims, "data_handling_claim"),
        "target_systems": _claims_for_review(claims, "target_system_claim"),
        "sample_records": _claims_for_review(claims, "sample_record_claim"),
        "deterministic_findings": _compact_deterministic_findings(deterministic_review),
    }


def _overview_map(claims: list[dict[str, Any]]) -> dict[str, Any]:
    overview: dict[str, Any] = {}

    for claim in claims:
        if claim.get("claim_type") != "overview_claim":
            continue

        props = claim.get("properties", {})
        name = props.get("name")
        value = props.get("value")

        if name:
            overview[name] = value

    return overview


def _participant_list(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    participants: list[dict[str, Any]] = []

    for claim in claims:
        if claim.get("claim_type") != "participant_claim":
            continue

        participants.append(
            {
                "claim_id": claim.get("claim_id"),
                "role_name": claim.get("properties", {}).get("role_name"),
                "source": claim.get("source"),
            }
        )

    return participants


def _ai_no_go_list(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    no_go_areas: list[dict[str, Any]] = []

    for claim in claims:
        if claim.get("claim_type") != "ai_no_go_claim":
            continue

        no_go_areas.append(
            {
                "claim_id": claim.get("claim_id"),
                "no_go_text": claim.get("properties", {}).get("no_go_text"),
                "source": claim.get("source"),
            }
        )

    return no_go_areas


def _claims_for_review(
    claims: list[dict[str, Any]],
    claim_type: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for claim in claims:
        if claim.get("claim_type") != claim_type:
            continue

        rows.append(
            {
                "claim_id": claim.get("claim_id"),
                "subject_id": claim.get("subject_id"),
                "properties": claim.get("properties", {}),
                "source": claim.get("source"),
            }
        )

    return rows


def _compact_deterministic_findings(
    deterministic_review: dict[str, Any],
) -> list[dict[str, Any]]:
    compact_findings: list[dict[str, Any]] = []

    for finding in deterministic_review.get("findings", []):
        compact_findings.append(
            {
                "finding_id": finding.get("finding_id"),
                "rule_id": finding.get("rule_id"),
                "severity": finding.get("severity"),
                "category": finding.get("category"),
                "title": finding.get("title"),
                "evidence": finding.get("evidence"),
                "implication": finding.get("implication"),
                "recommendation": finding.get("recommendation"),
                "confidence": finding.get("confidence"),
            }
        )

    return compact_findings
