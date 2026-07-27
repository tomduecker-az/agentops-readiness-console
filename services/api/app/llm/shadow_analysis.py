from datetime import UTC, datetime
from typing import Any

from audit_core import AuditEventType

from app.core.config import get_settings
from app.llm.prompt_builder import build_workflow_packet_prompt
from app.llm.provider import generate_structured_analysis
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact
from app.services.audit_service import log_audit_event


SYSTEM_INSTRUCTIONS = """
You are an enterprise workflow analysis assistant.

Your job is to analyze a workflow packet and produce a grounded workflow-readiness analysis.

Rules:
- Use only the workflow packet content provided.
- Do not invent systems, actors, policies, approvals, or facts.
- Clearly identify missing information instead of guessing.
- Do not recommend autonomous write actions without human approval.
- Treat provisioning, status updates, issue creation, record updates, and external communications as governed actions.
- Keep policy enforcement, approval decisions, and write execution outside the model.
- Use workflow-neutral language.
- Do not borrow language from payment reconciliation or customer onboarding unless it appears in the packet.
- Produce practical recommendations that a business analyst, technology leader, or AI governance reviewer could use.
""".strip()


LLM_WORKFLOW_ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_summary": {
            "type": "string"
        },
        "key_process_observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "observation": {"type": "string"},
                    "workflow_evidence": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["observation", "workflow_evidence", "why_it_matters","evidence_references"],
            },
        },
        "data_sensitivity_observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field_or_data_type": {"type": "string"},
                    "sensitivity_reason": {"type": "string"},
                    "recommended_handling": {"type": "string"},
                    "workflow_evidence": {"type": "string"},
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "field_or_data_type",
                    "sensitivity_reason",
                    "recommended_handling",
                    "workflow_evidence",
                    "evidence_references",
                ],
            },
        },
        "risk_observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "risk": {"type": "string"},
                    "risk_category": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "workflow_evidence": {"type": "string"},
                    "recommended_control": {"type": "string"},
                },
                "required": [
                    "risk",
                    "risk_category",
                    "severity",
                    "workflow_evidence",
                    "recommended_control",
                    "evidence_references",
                ],
            },
        },
        "control_recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "control": {"type": "string"},
                    "control_type": {"type": "string"},
                    "applies_to": {"type": "string"},
                    "implementation_note": {"type": "string"},
                    "evidence_references":{
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": [
                    "control",
                    "control_type",
                    "applies_to",
                    "implementation_note",
                    "evidence_references",
                ],
            },
        },
                "hitl_recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "review_point": {"type": "string"},
                    "human_reviewer": {"type": "string"},
                    "agent_allowed_before_approval": {"type": "string"},
                    "blocked_without_approval": {"type": "string"},
                    "required_evidence": {"type": "string"},
                    "evidence_references": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "review_point",
                    "human_reviewer",
                    "agent_allowed_before_approval",
                    "blocked_without_approval",
                    "required_evidence",
                    "evidence_references",
                ],
            },
        },
        "implementation_recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "description": {"type": "string"},
                    "suggested_owner": {"type": "string"},
                    "approval_required": {"type": "boolean"},
                    "evidence_references":{
                       "type": "array",
                       "items": {"type": "string"},
                    },
                },
                "required": [
                    "title",
                    "priority",
                    "description",
                    "suggested_owner",
                    "approval_required",
                    "evidence_references",
                ],
            },
        },
        "missing_information": {
            "type": "array",
            "items": {"type": "string"},
        },
        "grounding_notes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "hallucination_risk_notes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confidence_by_section": {
            "type": "object",
            "properties": {
                "workflow_understanding": {"type": "string"},
                "data_sensitivity": {"type": "string"},
                "risk_identification": {"type": "string"},
                "control_mapping": {"type": "string"},
                "implementation_planning": {"type": "string"},
            },
            "required": [
                "workflow_understanding",
                "data_sensitivity",
                "risk_identification",
                "control_mapping",
                "implementation_planning",
            ],
        },
    },
    "required": [
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
    ],
}


def run_llm_shadow_analysis(
    run_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    settings = get_settings()

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_started,
        actor="llm_shadow_analyzer",
        details={
            "workflow_id": workflow_id,
            "analysis_mode": "llm_shadow",
            "model": settings.openai_model,
        },
    )

    workflow_packet_prompt = build_workflow_packet_prompt(workflow_id)

    user_prompt = "\n\n".join(
        [
            "Analyze the following workflow packet.",
            "Return only the structured JSON object requested by the schema.",
            "Focus on grounded, practical workflow-readiness analysis.",
            workflow_packet_prompt,
        ]
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.tool_called,
        actor="llm_shadow_analyzer",
        details={
            "tool_name": "openai.responses.create",
            "analysis_mode": "llm_shadow",
            "model": settings.openai_model,
        },
    )

    analysis = generate_structured_analysis(
        system_instructions=SYSTEM_INSTRUCTIONS,
        user_prompt=user_prompt,
        json_schema=LLM_WORKFLOW_ANALYSIS_SCHEMA,
    )

    analysis["metadata"] = {
        "analysis_mode": "llm_shadow",
        "workflow_id": workflow_id,
        "model": settings.openai_model,
        "created_at": datetime.now(UTC).isoformat(),
        "source": "workflow_packet",
        "governance_note": (
            "This artifact is advisory shadow analysis only. It does not replace "
            "deterministic policy checks, approval requirements, or write-action controls."
        ),
    }

    artifact = create_artifact(
        run_id=run_id,
        artifact_type=ArtifactType.llm_workflow_analysis,
        content=analysis,
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_completed,
        actor="llm_shadow_analyzer",
        details={
            "workflow_id": workflow_id,
            "analysis_mode": "llm_shadow",
            "artifact_id": artifact.artifact_id,
            "risk_observation_count": len(analysis.get("risk_observations", [])),
            "implementation_recommendation_count": len(
                analysis.get("implementation_recommendations", [])
            ),
        },
    )

    return {
        "artifact_id": artifact.artifact_id,
        "run_id": run_id,
        "workflow_id": workflow_id,
        "analysis": analysis,
    }