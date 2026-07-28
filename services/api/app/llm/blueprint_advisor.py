from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from readiness_core.models import (
    AutonomyPosture,
    ImplementationPhase,
    OperationType,
    ReadinessRecommendation,
    RiskLevel,
)

from app.llm.provider import generate_structured_analysis


_ALLOWED_TOOL_CAPABILITIES = [
    "workflow_document_search",
    "policy_lookup",
    "data_classification",
    "intake_validation",
    "approval_request",
    "workflow_record_update",
    "system_access_provisioning",
    "controlled_notification",
    "report_generation",
    "audit_event_write",
]

_ALLOWED_MCP_SERVER_CANDIDATES = [
    "document_server",
    "policy_server",
    "approval_server",
    "project_mgmt_server",
    "provisioning_server",
    "notification_server",
    "reporting_server",
    "audit_server",
]

_SYSTEM_INSTRUCTIONS = """You are an enterprise AI workflow readiness advisor.

Your job is to propose an Agentic Readiness Blueprint for a business workflow.

Rules:
- Use only the workflow packet, analysis artifacts, and evidence catalog provided.
- Do not invent systems, vendors, policies, approvals, or workflow facts.
- Every recommendation must reference evidence IDs from the provided evidence catalog.
- Do not recommend autonomous write actions.
- Approval decisions must remain human-controlled.
- Provisioning, ticket/status updates, record updates, external communications, report distribution, and system changes are governed actions.
- Write, mixed, and external-communication capabilities must require approval and audit unless the capability is audit_event_write.
- Use only the allowed tool capabilities.
- Use only the allowed autonomy postures, operation types, risk levels, and implementation phases.
- If information is missing, state that clearly rather than guessing.
- Output only the JSON object requested by the schema.
"""


LLM_BLUEPRINT_PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "executive_summary": {
            "type": "object",
            "properties": {
                "workflow_name": {"type": "string"},
                "recommendation": {
                    "type": "string",
                    "enum": [item.value for item in ReadinessRecommendation],
                },
                "summary": {"type": "string"},
                "primary_value_opportunities": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "primary_constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "confidence": {"type": "string"},
                "evidence_references": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "workflow_name",
                "recommendation",
                "summary",
                "primary_value_opportunities",
                "primary_constraints",
                "confidence",
                "evidence_references",
            ],
        },
        "step_level_autonomy_matrix": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "string"},
                    "step_name": {"type": "string"},
                    "current_step_summary": {"type": "string"},
                    "recommended_posture": {
                        "type": "string",
                        "enum": [item.value for item in AutonomyPosture],
                    },
                    "why_ai_is_useful": {"type": "string"},
                    "why_ai_should_be_limited": {"type": "string"},
                    "allowed_ai_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "blocked_ai_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "required_human_reviewer": {"type": "string"},
                    "approval_required": {"type": "boolean"},
                    "audit_required": {"type": "boolean"},
                    "risk_level": {
                        "type": "string",
                        "enum": [item.value for item in RiskLevel],
                    },
                    "implementation_phase": {
                        "type": "string",
                        "enum": [item.value for item in ImplementationPhase],
                    },
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "step_id",
                    "step_name",
                    "current_step_summary",
                    "recommended_posture",
                    "why_ai_is_useful",
                    "why_ai_should_be_limited",
                    "allowed_ai_actions",
                    "blocked_ai_actions",
                    "required_human_reviewer",
                    "approval_required",
                    "audit_required",
                    "risk_level",
                    "implementation_phase",
                    "evidence_references",
                ],
            },
        },
        "tooling_blueprint": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "capability_name": {
                        "type": "string",
                        "enum": _ALLOWED_TOOL_CAPABILITIES,
                    },
                    "capability_description": {"type": "string"},
                    "operation_type": {
                        "type": "string",
                        "enum": [item.value for item in OperationType],
                    },
                    "recommended_access": {
                        "type": "string",
                        "enum": [item.value for item in AutonomyPosture],
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": [item.value for item in RiskLevel],
                    },
                    "approval_required": {"type": "boolean"},
                    "audit_required": {"type": "boolean"},
                    "mcp_server_candidate": {
                        "type": "string",
                        "enum": _ALLOWED_MCP_SERVER_CANDIDATES,
                    },
                    "implementation_phase": {
                        "type": "string",
                        "enum": [item.value for item in ImplementationPhase],
                    },
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "capability_name",
                    "capability_description",
                    "operation_type",
                    "recommended_access",
                    "risk_level",
                    "approval_required",
                    "audit_required",
                    "mcp_server_candidate",
                    "implementation_phase",
                    "evidence_references",
                ],
            },
        },
        "human_approval_gates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "gate_name": {"type": "string"},
                    "trigger_condition": {"type": "string"},
                    "required_reviewer": {"type": "string"},
                    "decision_required": {"type": "string"},
                    "agent_allowed_before_approval": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "blocked_without_approval": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "required_evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "gate_name",
                    "trigger_condition",
                    "required_reviewer",
                    "decision_required",
                    "agent_allowed_before_approval",
                    "blocked_without_approval",
                    "required_evidence",
                    "evidence_references",
                ],
            },
        },
        "risk_control_summary": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "risk_id": {"type": "string"},
                    "risk_description": {"type": "string"},
                    "risk_level": {
                        "type": "string",
                        "enum": [item.value for item in RiskLevel],
                    },
                    "recommended_controls": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "owner_role": {"type": "string"},
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "risk_id",
                    "risk_description",
                    "risk_level",
                    "recommended_controls",
                    "owner_role",
                    "evidence_references",
                ],
            },
        },
        "implementation_roadmap": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "enum": [item.value for item in ImplementationPhase],
                    },
                    "title": {"type": "string"},
                    "objective": {"type": "string"},
                    "recommended_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "exit_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "phase",
                    "title",
                    "objective",
                    "recommended_actions",
                    "exit_criteria",
                    "dependencies",
                    "evidence_references",
                ],
            },
        },
        "limitations_and_missing_information": {
            "type": "array",
            "items": {"type": "string"},
        },
        "advisor_notes": {
            "type": "object",
            "properties": {
                "key_assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "deterministic_baseline_disagreements": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "recommended_human_review_focus": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "key_assumptions",
                "deterministic_baseline_disagreements",
                "recommended_human_review_focus",
            ],
        },
    },
    "required": [
        "executive_summary",
        "step_level_autonomy_matrix",
        "tooling_blueprint",
        "human_approval_gates",
        "risk_control_summary",
        "implementation_roadmap",
        "limitations_and_missing_information",
        "advisor_notes",
    ],
}


def generate_llm_blueprint_proposal(
    *,
    workflow_id: str,
    run_id: str,
    artifacts_by_type: dict[str, list[dict[str, Any]]],
    workflow_documents: list[dict[str, Any]],
    deterministic_blueprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    llm_analysis = _latest_artifact_content(
        artifacts_by_type,
        "llm_workflow_analysis",
    )

    if not llm_analysis:
        raise ValueError("llm_workflow_analysis artifact is required.")

    evidence_catalog = _extract_evidence_catalog(llm_analysis)

    if not evidence_catalog:
        raise ValueError("Evidence catalog is required for LLM blueprint proposal.")

    workflow_steps = _extract_workflow_steps(workflow_documents)

    user_prompt = _build_user_prompt(
        workflow_id=workflow_id,
        run_id=run_id,
        workflow_documents=workflow_documents,
        workflow_steps=workflow_steps,
        llm_analysis=llm_analysis,
        evidence_catalog=evidence_catalog,
        deterministic_blueprint=deterministic_blueprint,
    )

    proposal = generate_structured_analysis(
        system_instructions=_SYSTEM_INSTRUCTIONS,
        user_prompt=user_prompt,
        json_schema=LLM_BLUEPRINT_PROPOSAL_SCHEMA,
        schema_name="llm_blueprint_proposal",
    )

    proposal["metadata"] = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "analysis_mode": "llm_blueprint_advisor_proposal",
        "generation_mode": "llm_assisted_proposal_only",
        "schema_name": "llm_blueprint_proposal",
        "allowed_tool_capabilities": _ALLOWED_TOOL_CAPABILITIES,
        "allowed_mcp_server_candidates": _ALLOWED_MCP_SERVER_CANDIDATES,
        "evidence_catalog": evidence_catalog,
        "workflow_step_count": len(workflow_steps),
        "governance_note": (
            "This is an LLM-generated blueprint proposal. It is not the final "
            "Agentic Readiness Blueprint until deterministic safety validation "
            "and reconciliation are applied."
        ),
    }

    return proposal


def _build_user_prompt(
    *,
    workflow_id: str,
    run_id: str,
    workflow_documents: list[dict[str, Any]],
    workflow_steps: list[str],
    llm_analysis: dict[str, Any],
    evidence_catalog: list[dict[str, Any]],
    deterministic_blueprint: dict[str, Any] | None,
) -> str:
    payload = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "workflow_steps": [
            {
                "step_id": f"STEP-{index:03d}",
                "step_text": step,
            }
            for index, step in enumerate(workflow_steps, start=1)
        ],
        "allowed_values": {
            "autonomy_postures": [item.value for item in AutonomyPosture],
            "readiness_recommendations": [item.value for item in ReadinessRecommendation],
            "operation_types": [item.value for item in OperationType],
            "risk_levels": [item.value for item in RiskLevel],
            "implementation_phases": [item.value for item in ImplementationPhase],
            "tool_capabilities": _ALLOWED_TOOL_CAPABILITIES,
            "mcp_server_candidates": _ALLOWED_MCP_SERVER_CANDIDATES,
        },
        "hard_constraints": [
            "Do not recommend autonomous write actions.",
            "Approval decisions must remain human-controlled.",
            "Access provisioning must require approval and audit.",
            "Workflow record, ticket, and evidence updates must require approval and audit.",
            "External communications and escalations must require human review before sending.",
            "All write, mixed, and external-communication tools must require audit logging.",
            "Use only evidence IDs from evidence_catalog.",
            "Use only tool capabilities from allowed_values.tool_capabilities.",
        ],
        "evidence_catalog": evidence_catalog,
        "workflow_documents": [
            {
                "document_id": document.get("document_id"),
                "title": document.get("title"),
                "document_type": document.get("document_type"),
                "content": _truncate(str(document.get("content", "")), 4500),
            }
            for document in workflow_documents
        ],
        "validated_llm_workflow_analysis": llm_analysis,
        "deterministic_baseline_blueprint": deterministic_blueprint,
    }

    return (
        "Create an LLM-assisted Agentic Readiness Blueprint proposal using the "
        "provided workflow packet, validated analysis, evidence catalog, allowed "
        "tool taxonomy, and hard constraints.\n\n"
        "Important interpretation guidance:\n"
        "- Verification and triage steps are usually AI-assist unless they make a final decision or write to a system.\n"
        "- Approval/rejection decisions should be AI-recommend/human-approve.\n"
        "- Provisioning and record updates should be approval-gated actions.\n"
        "- Escalations and workflow-impacting communications should be human-reviewed before sending.\n"
        "- Reporting preparation may be AI-assist, but distribution should remain controlled if sensitive.\n\n"
        "Return only the JSON object matching the schema.\n\n"
        f"{json.dumps(payload, indent=2)}"
    )


def _latest_artifact_content(
    artifacts_by_type: dict[str, list[dict[str, Any]]],
    artifact_type: str,
) -> dict[str, Any]:
    artifacts = artifacts_by_type.get(artifact_type, [])

    if not artifacts:
        return {}

    latest = artifacts[-1]

    if isinstance(latest, dict) and "content" in latest and isinstance(latest["content"], dict):
        return latest["content"]

    if isinstance(latest, dict):
        return latest

    return {}


def _extract_evidence_catalog(llm_analysis: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = llm_analysis.get("metadata", {})
    evidence_index = metadata.get("evidence_catalog_index", [])

    if not isinstance(evidence_index, list):
        return []

    cleaned: list[dict[str, Any]] = []

    for item in evidence_index:
        if not isinstance(item, dict):
            continue

        evidence_id = item.get("evidence_id")
        if not evidence_id:
            continue

        cleaned.append(
            {
                "evidence_id": evidence_id,
                "evidence_type": item.get("evidence_type"),
                "workflow_id": item.get("workflow_id"),
                "source_id": item.get("source_id"),
                "source_title": item.get("source_title"),
                "query": item.get("query"),
                "summary": item.get("summary"),
            }
        )

    return cleaned


def _extract_workflow_steps(workflow_documents: list[dict[str, Any]]) -> list[str]:
    current_steps = None

    for document in workflow_documents:
        if document.get("document_id") == "current_workflow_steps":
            current_steps = str(document.get("content", ""))
            break

    if not current_steps:
        return []

    steps = []

    for line in current_steps.splitlines():
        match = re.match(r"^\s*(?:\d+[\).\-\s]+|[-*]\s+)(.+?)\s*$", line)
        if not match:
            continue

        step = match.group(1).strip()
        if len(step) >= 8:
            steps.append(step)

    return steps


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[: max_length - 3].rstrip()}..."