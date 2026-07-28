from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from audit_core import AuditEventType

from app.core.config import get_settings
from app.llm.mcp_context_builder import build_mcp_retrieved_context
from app.llm.provider import generate_structured_analysis
from app.llm.shadow_analysis import LLM_WORKFLOW_ANALYSIS_SCHEMA
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact
from app.services.audit_service import log_audit_event


_AGENT_NAME = "mcp_llm_shadow_analyzer"


SYSTEM_INSTRUCTIONS = """
You are an enterprise workflow analysis agent operating behind MCP-controlled context access.

Your job is to analyze an unfamiliar workflow packet and produce a grounded workflow-readiness analysis.

You do not have direct filesystem access. The application runtime has retrieved bounded workflow and policy context through MCP tools. Use only that MCP-retrieved context.

Rules:
- Use only the MCP-retrieved workflow packet content, search results, data classifications, and required-control lookups provided.
- Do not invent systems, actors, policies, approvals, or facts.
- Clearly identify missing information instead of guessing.
- Do not recommend autonomous write actions without human approval.
- Treat provisioning, status updates, issue creation, record updates, report distribution, escalation messages, and external communications as governed actions.
- Keep policy enforcement, approval decisions, and write execution outside the model.
- Distinguish workflow evidence from assumptions.
- Use workflow-neutral language.
- Do not borrow language from payment reconciliation or customer onboarding unless it appears in the retrieved context.
- Produce practical recommendations that a business analyst, technology leader, or AI governance reviewer could use.
- Reference evidence IDs from the provided evidence_catalog whenever making workflow, risk, control, HITL, or missing-information claims.
""".strip()


def run_mcp_llm_shadow_analysis(
    run_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    settings = get_settings()

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_started,
        actor=_AGENT_NAME,
        details={
            "workflow_id": workflow_id,
            "analysis_mode": "mcp_llm_shadow_bounded",
            "model": settings.openai_model,
            "reasoning_effort": settings.openai_reasoning_effort,
        },
    )

    mcp_context, tool_trace = build_mcp_retrieved_context(
        run_id=run_id,
        workflow_id=workflow_id,
    )
    evidence_catalog_index = _build_evidence_catalog_index(mcp_context)

    user_prompt = "\n\n".join(
        [
            f"Analyze workflow_id={workflow_id}.",
            "Return only the structured JSON object requested by the schema.",
            "Focus on grounded, practical workflow-readiness analysis.",
            "Use the MCP-retrieved context below as the only source of workflow and policy evidence.",
            "Use evidence_id values from evidence_catalog to ground important observations, risks, controls, HITL gates, implementation recommendations, and missing-information claims.",
            json.dumps(mcp_context, indent=2, default=str),
        ]
    )

    analysis = generate_structured_analysis(
        system_instructions=SYSTEM_INSTRUCTIONS,
        user_prompt=user_prompt,
        json_schema=LLM_WORKFLOW_ANALYSIS_SCHEMA,
    )

    model = settings.openai_model.strip() or "gpt-5.6-sol"
    reasoning_effort = settings.openai_reasoning_effort.strip() or "high"

    analysis["metadata"] = {
        "analysis_mode": "mcp_llm_shadow_bounded",
        "workflow_id": workflow_id,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "created_at": datetime.now(UTC).isoformat(),
        "source": "bounded_mcp_tool_retrieved_context",
        "tool_call_count": len(tool_trace),
        "tool_trace": tool_trace,
        "evidence_catalog_index": evidence_catalog_index,
        "governance_note": (
            "This artifact is advisory bounded MCP shadow analysis only. "
            "The application retrieved workflow and policy context through controlled MCP tools. "
            "The model did not receive direct filesystem access and does not replace deterministic "
            "policy checks, approval requirements, or write-action controls."
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
        actor=_AGENT_NAME,
        details={
            "workflow_id": workflow_id,
            "analysis_mode": "mcp_llm_shadow_bounded",
            "artifact_id": artifact.artifact_id,
            "tool_call_count": len(tool_trace),
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

def _build_evidence_catalog_index(
        mcp_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        evidence_catalog = mcp_context.get("evidence_catalog", [])

        index = []

        for item in evidence_catalog:
            index.append(
                {
                    "evidence_id": item.get("evidence_id"),
                    "evidence_type": item.get("evidence_type"),
                    "workflow_id": item.get("workflow_id"),
                    "source_id": item.get("source_id"),
                    "source_title": item.get("source_title"),
                    "query": item.get("query"),
                    "summary": item.get("summary"),
                }
            )

        return index