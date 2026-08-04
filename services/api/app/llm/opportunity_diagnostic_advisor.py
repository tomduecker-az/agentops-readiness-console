from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from readiness_core import (
    WorkflowAIOpportunityDiagnostic,
)

from app.llm.provider import generate_structured_analysis


_SYSTEM_INSTRUCTIONS = """You are an enterprise AI workflow transformation advisor.

Your job is to produce a Workflow AI Opportunity Diagnostic.

This diagnostic must help a workflow owner understand:
- where AI can create business value,
- what is blocking safe agentic use,
- what should be piloted first,
- what should not be automated first,
- what process/control redesign is required,
- how value should be measured,
- what non-obvious operational insight the workflow owner may be missing.

Rules:
- Use only the provided workflow packet, reconciled blueprint, analysis artifacts, and evidence catalog.
- Do not invent systems, vendors, policies, metrics, approvals, or workflow facts.
- Every major finding must reference evidence IDs from the provided evidence catalog.
- Be specific and business-useful. Avoid generic AI transformation language.
- Distinguish current readiness from future potential.
- Do not recommend autonomous approval, autonomous provisioning, autonomous external communication, or autonomous system-of-record updates.
- Treat missing control mappings, missing decision criteria, missing data boundaries, missing reviewer authority rules, missing state-transition rules, and missing measurement baselines as readiness blockers.
- If information is missing, state the question the workflow owner must answer.
- Output only the JSON object requested by the schema.

The diagnostic must not read like a governance checklist. It must explain the operational meaning of the findings.

The most important output is not the list of controls. The most important output is the insight:
- what the organization is likely to misunderstand about agentic readiness,
- why the best first use case may be different from the obvious automation target,
- what process/data/control changes unlock higher autonomy,
- what the pilot must prove before expansion.

Required analytical posture:
- Identify at least three non-obvious insights.
- Identify at least two tempting automation misconceptions.
- Identify the operational pattern that creates both the AI opportunity and the AI limitation.
- Identify pilot learning objectives that would determine whether expansion is justified.
- Identify a staged autonomy unlock path from the current ceiling to any higher future ceiling.
- Analyze sample record patterns when sample records are available.
- Explain why the recommended first use case is better than more aggressive automation.
"""


def generate_workflow_ai_opportunity_diagnostic(
    *,
    workflow_id: str,
    run_id: str,
    workflow_documents: list[dict[str, Any]],
    artifacts_by_type: dict[str, list[dict[str, Any]]],
    reconciled_blueprint: dict[str, Any],
) -> WorkflowAIOpportunityDiagnostic:
    """Generate the business-value diagnostic for a workflow.

    This is intentionally separate from the Agentic Readiness Blueprint.
    The blueprint is the implementation/control artifact.
    The diagnostic is the business insight artifact.
    """

    evidence_catalog = _extract_evidence_catalog(
        artifacts_by_type=artifacts_by_type,
        reconciled_blueprint=reconciled_blueprint,
    )

    if not evidence_catalog:
        raise ValueError("Evidence catalog is required for opportunity diagnostic generation.")

    llm_workflow_analysis = _latest_artifact_content(
        artifacts_by_type,
        "llm_workflow_analysis",
    )

    risk_control_matrix = _latest_artifact_content(
        artifacts_by_type,
        "risk_control_matrix",
    )

    hitl_design = _latest_artifact_content(
        artifacts_by_type,
        "hitl_design",
    )

    implementation_backlog = _latest_artifact_content(
        artifacts_by_type,
        "implementation_backlog",
    )

    prompt = _build_user_prompt(
        workflow_id=workflow_id,
        run_id=run_id,
        workflow_documents=workflow_documents,
        reconciled_blueprint=reconciled_blueprint,
        llm_workflow_analysis=llm_workflow_analysis,
        risk_control_matrix=risk_control_matrix,
        hitl_design=hitl_design,
        implementation_backlog=implementation_backlog,
        evidence_catalog=evidence_catalog,
    )

    raw_diagnostic = generate_structured_analysis(
        system_instructions=_SYSTEM_INSTRUCTIONS,
        user_prompt=prompt,
        json_schema=WorkflowAIOpportunityDiagnostic.model_json_schema(),
        schema_name="workflow_ai_opportunity_diagnostic",
    )

    raw_diagnostic.setdefault("workflow_id", workflow_id)
    raw_diagnostic.setdefault("run_id", run_id)
    raw_diagnostic.setdefault("created_at", datetime.now(UTC).isoformat())
    raw_diagnostic["evidence_catalog"] = evidence_catalog

    raw_diagnostic.setdefault("metadata", {})
    raw_diagnostic["metadata"].update(
        {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "created_at": datetime.now(UTC).isoformat(),
            "generation_mode": "llm_generated_opportunity_diagnostic",
            "source": "workflow_packet_reconciled_blueprint_and_validated_artifacts",
            "governance_note": (
                "This diagnostic is advisory. It identifies AI opportunity, readiness blockers, "
                "and implementation priorities, but does not approve automation or execute workflow actions."
            ),
        }
    )

    return WorkflowAIOpportunityDiagnostic.model_validate(raw_diagnostic)


def _build_user_prompt(
    *,
    workflow_id: str,
    run_id: str,
    workflow_documents: list[dict[str, Any]],
    reconciled_blueprint: dict[str, Any],
    llm_workflow_analysis: dict[str, Any],
    risk_control_matrix: dict[str, Any],
    hitl_design: dict[str, Any],
    implementation_backlog: dict[str, Any],
    evidence_catalog: list[dict[str, Any]],
) -> str:
    payload = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "diagnostic_goal": (
            "Identify the most valuable and safest AI/agentic opportunities in this workflow, "
            "the readiness blockers that prevent higher autonomy, and the practical path to a pilot."
        ),
        "required_business_questions_to_answer": [
            "What is the current safe automation ceiling?",
            "What hidden blockers prevent higher autonomy?",
            "What is the best first AI use case and why?",
            "What should the organization avoid automating first?",
            "What process redesign is required before higher autonomy?",
            "What controls must be added or clarified?",
            "What value hypotheses can be tested?",
            "What measurements should be collected?",
            "What sample-record patterns show opportunity or risk?",
            "What questions must the workflow owner answer before implementation?",
        ],
        "evidence_catalog": evidence_catalog,
        "workflow_documents": [
            {
                "document_id": document.get("document_id"),
                "title": document.get("title"),
                "document_type": document.get("document_type"),
                "content": _truncate(str(document.get("content", "")), 5000),
            }
            for document in workflow_documents
        ],
        "reconciled_agentic_readiness_blueprint": reconciled_blueprint,
        "validated_llm_workflow_analysis": llm_workflow_analysis,
        "risk_control_matrix": risk_control_matrix,
        "hitl_design": hitl_design,
        "implementation_backlog": implementation_backlog,
        "output_guidance": {
            "executive_summary": (
                "Lead with the strongest business insight. Do not simply repeat the autonomy matrix."
            ),
            "automation_ceiling": (
                "State the highest safe current autonomy level and explain what prevents the next level."
            ),
            "top_readiness_blockers": (
                "Rank blockers by business/control impact, not by technical curiosity."
            ),
            "recommended_first_use_case": (
                "Recommend one best first pilot. It should be practical, measurable, and low enough risk to start."
            ),
            "use_cases_to_avoid": (
                "Identify where the organization may be tempted to automate but should not start."
            ),
            "process_redesign_requirements": (
                "Describe concrete process/control changes needed to unlock higher autonomy."
            ),
            "value_hypotheses": (
                "Do not invent ROI numbers. State directional hypotheses and required measurements."
            ),
            "sample_record_opportunity_analysis": (
                "Use sample records if available. Keep the analysis advisory and avoid exposing sensitive values."
            ),
            "non_obvious_insights": (
                "Provide at least three findings that a workflow owner may not already realize. "
                "Do not repeat obvious statements such as 'approval requires humans' unless you explain "
                "a less obvious business implication."
            ),
            "automation_misconceptions": (
                "Identify tempting but premature automation targets. Explain why the safer first pilot is different."
            ),
            "operational_pattern_analysis": (
                "Explain the workflow pattern that creates value. For example: repeated intake review, "
                "evidence assembly, exception routing, reviewer packet preparation, or SLA queue preparation."
            ),
            "pilot_learning_objectives": (
                "Define what the pilot must prove before the organization can justify expansion."
            ),
            "autonomy_unlock_path": (
                "Show the staged path from the current automation ceiling to higher autonomy. "
                "Each stage must include required process/control/data changes and validation."
            ),
            "sample_record_patterns": (
                "Analyze sample records as operational patterns. Do not merely restate each row."
            ),
        },
    }

    return (
        "Create a Workflow AI Opportunity Diagnostic from the following evidence-grounded inputs.\n\n"
        "The result must be useful to a business workflow owner. It should reveal what is actually "
        "blocking or enabling AI adoption, not merely classify each step.\n\n"
        "Return only JSON matching the schema.\n\n"
        f"{json.dumps(payload, indent=2)}"
    )


def _extract_evidence_catalog(
    *,
    artifacts_by_type: dict[str, list[dict[str, Any]]],
    reconciled_blueprint: dict[str, Any],
) -> list[dict[str, Any]]:
    blueprint_catalog = reconciled_blueprint.get("evidence_catalog", [])

    if isinstance(blueprint_catalog, list) and blueprint_catalog:
        return [
            item
            for item in blueprint_catalog
            if isinstance(item, dict) and item.get("evidence_id")
        ]

    llm_analysis = _latest_artifact_content(
        artifacts_by_type,
        "llm_workflow_analysis",
    )

    metadata = llm_analysis.get("metadata", {})
    evidence_index = metadata.get("evidence_catalog_index", [])

    if not isinstance(evidence_index, list):
        return []

    return [
        item
        for item in evidence_index
        if isinstance(item, dict) and item.get("evidence_id")
    ]


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


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[: max_length - 3].rstrip()}..."