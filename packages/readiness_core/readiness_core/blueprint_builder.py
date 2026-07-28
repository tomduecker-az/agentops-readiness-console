from __future__ import annotations

import re
from datetime import UTC, datetime
from statistics import mean
from typing import Any, Mapping

from readiness_core.models import (
    AgenticReadinessBlueprint,
    AutonomyPosture,
    BlueprintValidationSummary,
    CostAndOperationsNotes,
    EvidenceReference,
    ExecutiveSummary,
    HumanApprovalGate,
    ImplementationPhase,
    ImplementationRoadmapItem,
    ReadinessRecommendation,
    ReadinessScore,
    RiskControlSummaryItem,
    RiskLevel,
    StepAutonomyRecommendation,
)
from readiness_core.tool_taxonomy import infer_tool_capabilities


def build_agentic_readiness_blueprint(
    *,
    workflow_id: str,
    run_id: str,
    artifacts_by_type: Mapping[str, Any],
    workflow_documents: list[dict[str, Any]] | None = None,
) -> AgenticReadinessBlueprint:
    """Build the primary product artifact from existing analysis artifacts.

    The builder is deterministic. It does not call an LLM.
    It consumes validated analysis artifacts and produces a product-ready blueprint.
    """

    llm_analysis = _get_artifact_content(artifacts_by_type, "llm_workflow_analysis")
    llm_evaluation = _get_artifact_content(artifacts_by_type, "llm_shadow_evaluation")
    mcp_evaluation = _get_artifact_content(artifacts_by_type, "mcp_operational_evaluation")
    evidence_evaluation = _get_artifact_content(artifacts_by_type, "evidence_grounding_evaluation")

    evidence_catalog = _build_evidence_catalog(llm_analysis)
    default_evidence_refs = [item.evidence_id for item in evidence_catalog[:6]]

    workflow_steps = _extract_workflow_steps(
        workflow_documents=workflow_documents or [],
        llm_analysis=llm_analysis,
    )

    validation_summary = _build_validation_summary(
        llm_evaluation=llm_evaluation,
        mcp_evaluation=mcp_evaluation,
        evidence_evaluation=evidence_evaluation,
    )

    readiness_scorecard = _build_readiness_scorecard(
        llm_analysis=llm_analysis,
        validation_summary=validation_summary,
        default_evidence_refs=default_evidence_refs,
    )

    recommendation = _determine_recommendation(
        readiness_scorecard=readiness_scorecard,
        validation_summary=validation_summary,
    )

    autonomy_matrix = _build_autonomy_matrix(
        workflow_steps=workflow_steps,
        default_evidence_refs=default_evidence_refs,
    )

    tooling_blueprint = infer_tool_capabilities(
        autonomy_matrix=autonomy_matrix,
        default_evidence_references=default_evidence_refs,
    )

    human_approval_gates = _build_human_approval_gates(
        llm_analysis=llm_analysis,
        autonomy_matrix=autonomy_matrix,
        default_evidence_refs=default_evidence_refs,
    )

    risk_control_summary = _build_risk_control_summary(
        llm_analysis=llm_analysis,
        default_evidence_refs=default_evidence_refs,
    )

    implementation_roadmap = _build_implementation_roadmap(
        recommendation=recommendation,
        default_evidence_refs=default_evidence_refs,
    )

    executive_summary = _build_executive_summary(
        workflow_id=workflow_id,
        llm_analysis=llm_analysis,
        recommendation=recommendation,
        readiness_scorecard=readiness_scorecard,
    )

    return AgenticReadinessBlueprint(
        workflow_id=workflow_id,
        run_id=run_id,
        created_at=datetime.now(UTC).isoformat(),
        executive_summary=executive_summary,
        readiness_scorecard=readiness_scorecard,
        step_level_autonomy_matrix=autonomy_matrix,
        tooling_blueprint=tooling_blueprint,
        human_approval_gates=human_approval_gates,
        risk_control_summary=risk_control_summary,
        implementation_roadmap=implementation_roadmap,
        cost_and_operations_notes=_build_cost_and_operations_notes(),
        validation_summary=validation_summary,
        evidence_catalog=evidence_catalog,
        limitations_and_missing_information=_extract_missing_information(llm_analysis),
        metadata={
            "source_artifacts": sorted(artifacts_by_type.keys()),
            "builder": "readiness_core.blueprint_builder",
            "builder_version": "0.1.0",
            "generation_mode": "deterministic_from_validated_artifacts",
        },
    )


def _get_artifact_content(
    artifacts_by_type: Mapping[str, Any],
    artifact_type: str,
) -> dict[str, Any]:
    artifact = artifacts_by_type.get(artifact_type)

    if artifact is None:
        return {}

    if isinstance(artifact, list):
        artifact = artifact[-1] if artifact else {}

    if not isinstance(artifact, dict):
        return {}

    if "content" in artifact and isinstance(artifact["content"], dict):
        return artifact["content"]

    return artifact


def _build_evidence_catalog(llm_analysis: dict[str, Any]) -> list[EvidenceReference]:
    metadata = llm_analysis.get("metadata", {})
    evidence_index = metadata.get("evidence_catalog_index", [])

    if not isinstance(evidence_index, list):
        return []

    references: list[EvidenceReference] = []

    for item in evidence_index:
        if not isinstance(item, dict):
            continue

        evidence_id = item.get("evidence_id")
        if not evidence_id:
            continue

        references.append(
            EvidenceReference(
                evidence_id=str(evidence_id),
                evidence_type=_optional_str(item.get("evidence_type")),
                source_title=_optional_str(item.get("source_title")),
                summary=_optional_str(item.get("summary")),
            )
        )

    return references


def _build_validation_summary(
    *,
    llm_evaluation: dict[str, Any],
    mcp_evaluation: dict[str, Any],
    evidence_evaluation: dict[str, Any],
) -> BlueprintValidationSummary:
    return BlueprintValidationSummary(
        llm_quality_score=_optional_int(llm_evaluation.get("score")),
        mcp_operational_score=_optional_int(mcp_evaluation.get("score")),
        evidence_grounding_score=_optional_int(evidence_evaluation.get("score")),
        passed_quality_gate=_optional_bool(llm_evaluation.get("passed")),
        passed_mcp_gate=_optional_bool(mcp_evaluation.get("passed")),
        passed_evidence_gate=_optional_bool(evidence_evaluation.get("passed")),
    )


def _build_readiness_scorecard(
    *,
    llm_analysis: dict[str, Any],
    validation_summary: BlueprintValidationSummary,
    default_evidence_refs: list[str],
) -> list[ReadinessScore]:
    missing_info = _extract_missing_information(llm_analysis)
    risks = _as_list(llm_analysis.get("risk_observations"))
    hitl = _as_list(llm_analysis.get("hitl_recommendations"))
    data_sensitivity = _as_list(llm_analysis.get("data_sensitivity_observations"))

    evidence_score = _clamp_score(validation_summary.evidence_grounding_score)
    mcp_score = _clamp_score(validation_summary.mcp_operational_score)
    quality_score = _clamp_score(validation_summary.llm_quality_score)

    process_clarity_score = max(45, 90 - min(len(missing_info) * 8, 40))
    data_sensitivity_score = 80 if not data_sensitivity else 68
    write_action_score = 78 if not hitl else 62
    evidence_score_normalized = evidence_score
    governance_score = round(mean([score for score in [mcp_score, evidence_score] if score > 0]) or 50)
    analysis_quality_score = min(max(quality_score, 0), 100) if quality_score else 70

    scorecard = [
        ReadinessScore(
            dimension="process_clarity",
            score=process_clarity_score,
            rationale="Assesses whether the workflow has enough documented structure to support reliable AI assistance.",
            evidence_references=default_evidence_refs,
        ),
        ReadinessScore(
            dimension="data_sensitivity",
            score=data_sensitivity_score,
            rationale="Assesses whether sensitive data can be handled with appropriate controls and limited model exposure.",
            evidence_references=_collect_section_refs(data_sensitivity, default_evidence_refs),
        ),
        ReadinessScore(
            dimension="write_action_risk",
            score=write_action_score,
            rationale="Assesses whether workflow state changes, provisioning, communications, or external updates require approval-gated controls.",
            evidence_references=_collect_section_refs(hitl, default_evidence_refs),
        ),
        ReadinessScore(
            dimension="governance_readiness",
            score=governance_score,
            rationale="Assesses whether MCP operation and evidence grounding checks support governed enterprise use.",
            evidence_references=default_evidence_refs,
        ),
        ReadinessScore(
            dimension="analysis_quality",
            score=analysis_quality_score,
            rationale="Assesses whether the generated workflow analysis passed automated quality checks.",
            evidence_references=default_evidence_refs,
        ),
    ]

    overall_score = round(mean(score.score for score in scorecard))

    scorecard.insert(
        0,
        ReadinessScore(
            dimension="overall_readiness",
            score=overall_score,
            rationale="Composite readiness score based on process clarity, sensitivity, write-action risk, governance readiness, and analysis quality.",
            evidence_references=default_evidence_refs,
        ),
    )

    return scorecard


def _determine_recommendation(
    *,
    readiness_scorecard: list[ReadinessScore],
    validation_summary: BlueprintValidationSummary,
) -> ReadinessRecommendation:
    overall = next(
        (score.score for score in readiness_scorecard if score.dimension == "overall_readiness"),
        0,
    )

    if validation_summary.passed_evidence_gate is False or validation_summary.passed_mcp_gate is False:
        return ReadinessRecommendation.insufficient_information

    if overall >= 85:
        return ReadinessRecommendation.strong_candidate

    if overall >= 70:
        return ReadinessRecommendation.good_candidate_with_controls

    if overall >= 55:
        return ReadinessRecommendation.limited_candidate

    return ReadinessRecommendation.not_recommended


def _build_executive_summary(
    *,
    workflow_id: str,
    llm_analysis: dict[str, Any],
    recommendation: ReadinessRecommendation,
    readiness_scorecard: list[ReadinessScore],
) -> ExecutiveSummary:
    workflow_summary = _as_text(llm_analysis.get("workflow_summary"))
    overall_score = next(
        (score.score for score in readiness_scorecard if score.dimension == "overall_readiness"),
        None,
    )

    summary = workflow_summary or (
        f"The workflow '{workflow_id}' was evaluated for AI readiness using governed, evidence-backed analysis."
    )

    if overall_score is not None:
        summary = f"{summary} Overall readiness score: {overall_score}/100."

    return ExecutiveSummary(
        workflow_name=workflow_id,
        recommendation=recommendation,
        summary=summary,
        primary_value_opportunities=_extract_value_opportunities(llm_analysis),
        primary_constraints=_extract_primary_constraints(llm_analysis),
        confidence=_determine_confidence(llm_analysis),
    )


def _extract_workflow_steps(
    *,
    workflow_documents: list[dict[str, Any]],
    llm_analysis: dict[str, Any],
) -> list[str]:
    current_steps_doc = _find_document(workflow_documents, "current_workflow_steps")

    if current_steps_doc:
        parsed_steps = _parse_numbered_steps(_as_text(current_steps_doc.get("content")))
        if parsed_steps:
            return parsed_steps

    observations = _as_list(llm_analysis.get("key_process_observations"))
    fallback_steps = []

    for item in observations:
        text = _item_summary(item)
        if text:
            fallback_steps.append(text)

    return fallback_steps or ["Review workflow documentation and determine AI assistance opportunities."]


def _find_document(
    workflow_documents: list[dict[str, Any]],
    document_id: str,
) -> dict[str, Any] | None:
    for document in workflow_documents:
        if str(document.get("document_id", "")).lower() == document_id.lower():
            return document

    return None


_STEP_PATTERN = re.compile(r"^\s*(?:\d+[\).\-\s]+|[-*]\s+)(.+?)\s*$")


def _parse_numbered_steps(content: str) -> list[str]:
    steps: list[str] = []

    for line in content.splitlines():
        match = _STEP_PATTERN.match(line)
        if not match:
            continue

        step = match.group(1).strip()
        if len(step) >= 8:
            steps.append(step)

    return steps


def _build_autonomy_matrix(
    *,
    workflow_steps: list[str],
    default_evidence_refs: list[str],
) -> list[StepAutonomyRecommendation]:
    recommendations: list[StepAutonomyRecommendation] = []

    for index, step in enumerate(workflow_steps, start=1):
        classification = _classify_step(step)

        recommendations.append(
            StepAutonomyRecommendation(
                step_id=f"STEP-{index:03d}",
                step_name=_shorten(step, 90),
                current_step_summary=step,
                recommended_posture=classification["posture"],
                why_ai_is_useful=classification["why_useful"],
                why_ai_should_be_limited=classification["why_limited"],
                allowed_ai_actions=classification["allowed"],
                blocked_ai_actions=classification["blocked"],
                required_human_reviewer=classification["reviewer"],
                approval_required=classification["approval_required"],
                audit_required=classification["audit_required"],
                risk_level=classification["risk_level"],
                implementation_phase=classification["phase"],
                evidence_references=default_evidence_refs,
            )
        )

    return recommendations


def _classify_step(step: str) -> dict[str, Any]:
    text = step.lower()

    if any(keyword in text for keyword in ["provision", "permission", "entitlement", "grant access"]):
        return {
            "posture": AutonomyPosture.approval_gated_action,
            "why_useful": "AI can prepare the action, verify required evidence, and check whether prerequisites are complete.",
            "why_limited": "Provisioning or permission changes alter system access and should not be executed without explicit approval and audit controls.",
            "allowed": [
                "Prepare recommended provisioning instructions.",
                "Check whether required approvals and evidence are present.",
                "Flag missing or conflicting prerequisites.",
            ],
            "blocked": [
                "Provision access without approval.",
                "Override policy or reviewer decisions.",
                "Close or finalize the workflow without audit evidence.",
            ],
            "reviewer": "Authorized workflow or security approver",
            "approval_required": True,
            "audit_required": True,
            "risk_level": RiskLevel.critical,
            "phase": ImplementationPhase.phase_3_approval_gated_actions,
        }

    if any(keyword in text for keyword in ["approve", "reject", "approval", "security review", "owner review"]):
        return {
            "posture": AutonomyPosture.ai_recommend_human_approve,
            "why_useful": "AI can summarize context, organize evidence, and highlight risks before the reviewer makes a decision.",
            "why_limited": "Approval decisions carry accountability and should remain with an authorized human reviewer.",
            "allowed": [
                "Summarize the request and supporting evidence.",
                "Identify missing or inconsistent information.",
                "Recommend reviewer questions or next steps.",
            ],
            "blocked": [
                "Approve or reject the request autonomously.",
                "Bypass required reviewers.",
                "Record final decisions without human confirmation.",
            ],
            "reviewer": "Required business, application, or security approver",
            "approval_required": True,
            "audit_required": True,
            "risk_level": RiskLevel.high,
            "phase": ImplementationPhase.phase_2_human_reviewed_recommendations,
        }

    if any(keyword in text for keyword in ["update", "ticket", "status", "record", "tracking", "evidence"]):
        return {
            "posture": AutonomyPosture.approval_gated_action,
            "why_useful": "AI can reduce administrative effort by preparing structured record updates.",
            "why_limited": "Workflow records and evidence trails affect auditability and should be updated only under controlled rules.",
            "allowed": [
                "Draft record updates.",
                "Identify required fields.",
                "Validate that evidence is attached before final update.",
            ],
            "blocked": [
                "Change official workflow status without approval.",
                "Remove or alter audit evidence.",
                "Write incomplete or unsupported updates.",
            ],
            "reviewer": "Workflow owner or control reviewer",
            "approval_required": True,
            "audit_required": True,
            "risk_level": RiskLevel.high,
            "phase": ImplementationPhase.phase_3_approval_gated_actions,
        }

    if any(keyword in text for keyword in ["missing", "unclear", "conflicting", "verify", "check", "review", "validate"]):
        return {
            "posture": AutonomyPosture.ai_assist,
            "why_useful": "AI can help inspect information, identify gaps, and organize review findings.",
            "why_limited": "The model should not make final policy or business decisions without human review.",
            "allowed": [
                "Identify missing information.",
                "Compare request details against documented requirements.",
                "Prepare a reviewer summary.",
            ],
            "blocked": [
                "Make final approval decisions.",
                "Execute write actions.",
                "Assume missing facts that are not present in evidence.",
            ],
            "reviewer": "Workflow analyst or responsible reviewer",
            "approval_required": False,
            "audit_required": True,
            "risk_level": RiskLevel.medium,
            "phase": ImplementationPhase.phase_1_read_only_analysis,
        }

    if any(keyword in text for keyword in ["report", "weekly", "metrics"]):
        return {
            "posture": AutonomyPosture.ai_assist,
            "why_useful": "AI can summarize workflow status and prepare draft reporting outputs.",
            "why_limited": "Reports should be reviewed before distribution if they include sensitive or operationally significant information.",
            "allowed": [
                "Draft summary reports.",
                "Highlight exceptions and trends.",
                "Identify records requiring follow-up.",
            ],
            "blocked": [
                "Distribute reports externally without review.",
                "Include unsupported conclusions.",
                "Expose sensitive data unnecessarily.",
            ],
            "reviewer": "Workflow owner or reporting reviewer",
            "approval_required": False,
            "audit_required": True,
            "risk_level": RiskLevel.medium,
            "phase": ImplementationPhase.phase_2_human_reviewed_recommendations,
        }

    return {
        "posture": AutonomyPosture.ai_assist,
        "why_useful": "AI can assist with summarization, classification, and preparation of reviewer-ready information.",
        "why_limited": "The workflow should begin with assistive use until risks, controls, and approval requirements are validated.",
        "allowed": [
            "Summarize available context.",
            "Identify apparent next steps.",
            "Flag missing evidence.",
        ],
        "blocked": [
            "Execute workflow changes autonomously.",
            "Communicate final decisions without approval.",
            "Invent missing policy or process facts.",
        ],
        "reviewer": "Workflow owner",
        "approval_required": False,
        "audit_required": True,
        "risk_level": RiskLevel.medium,
        "phase": ImplementationPhase.phase_1_read_only_analysis,
    }


def _build_human_approval_gates(
    *,
    llm_analysis: dict[str, Any],
    autonomy_matrix: list[StepAutonomyRecommendation],
    default_evidence_refs: list[str],
) -> list[HumanApprovalGate]:
    gates: list[HumanApprovalGate] = []

    for item in _as_list(llm_analysis.get("hitl_recommendations")):
        if not isinstance(item, dict):
            continue

        gates.append(
            HumanApprovalGate(
                gate_name=_first_present(item, ["review_point", "gate_name", "name"]) or "Human review gate",
                trigger_condition=_first_present(item, ["trigger_condition", "review_point", "required_evidence"]) or "A human decision or controlled action is required.",
                required_reviewer=_first_present(item, ["human_reviewer", "required_reviewer", "reviewer"]) or "Authorized reviewer",
                decision_required=_first_present(item, ["decision_required", "blocked_without_approval"]) or "Approve, reject, or request more information.",
                agent_allowed_before_approval=_as_string_list(item.get("agent_allowed_before_approval")),
                blocked_without_approval=_as_string_list(item.get("blocked_without_approval")),
                required_evidence=_as_string_list(item.get("required_evidence")),
                evidence_references=_evidence_refs_from_item(item, default_evidence_refs),
            )
        )

    if gates:
        return gates

    for step in autonomy_matrix:
        if not step.approval_required:
            continue

        gates.append(
            HumanApprovalGate(
                gate_name=f"Approval required for {step.step_id}",
                trigger_condition=step.current_step_summary,
                required_reviewer=step.required_human_reviewer or "Authorized reviewer",
                decision_required="Confirm whether the AI-prepared recommendation or action may proceed.",
                agent_allowed_before_approval=step.allowed_ai_actions,
                blocked_without_approval=step.blocked_ai_actions,
                required_evidence=step.evidence_references,
                evidence_references=step.evidence_references,
            )
        )

    return gates


def _build_risk_control_summary(
    *,
    llm_analysis: dict[str, Any],
    default_evidence_refs: list[str],
) -> list[RiskControlSummaryItem]:
    items: list[RiskControlSummaryItem] = []

    for index, risk in enumerate(_as_list(llm_analysis.get("risk_observations")), start=1):
        if not isinstance(risk, dict):
            continue

        items.append(
            RiskControlSummaryItem(
                risk_id=_first_present(risk, ["risk_id", "id"]) or f"RISK-BP-{index:03d}",
                risk_description=_first_present(risk, ["risk", "risk_description", "description", "observation"]) or _item_summary(risk),
                risk_level=_risk_level_from_text(_first_present(risk, ["risk_level", "severity", "level"]) or _item_summary(risk)),
                recommended_controls=_extract_controls_for_risk(llm_analysis, default_evidence_refs),
                owner_role=_first_present(risk, ["owner_role", "owner", "responsible_role"]),
                evidence_references=_evidence_refs_from_item(risk, default_evidence_refs),
            )
        )

    if items:
        return items

    return [
        RiskControlSummaryItem(
            risk_id="RISK-BP-001",
            risk_description="Workflow requires controlled AI adoption with evidence grounding, human review, and audited actions.",
            risk_level=RiskLevel.medium,
            recommended_controls=[
                "Use read-only AI assistance first.",
                "Require approval before workflow write actions.",
                "Log tool calls, approvals, and generated artifacts.",
            ],
            owner_role="Workflow owner",
            evidence_references=default_evidence_refs,
        )
    ]


def _extract_controls_for_risk(
    llm_analysis: dict[str, Any],
    default_evidence_refs: list[str],
) -> list[str]:
    controls = []

    for control in _as_list(llm_analysis.get("control_recommendations"))[:5]:
        text = _item_summary(control)
        if text:
            controls.append(text)

    return controls or [
        "Require human approval for controlled actions.",
        "Maintain audit logs for tool calls and workflow updates.",
        "Ground AI recommendations in approved evidence.",
    ]


def _build_implementation_roadmap(
    *,
    recommendation: ReadinessRecommendation,
    default_evidence_refs: list[str],
) -> list[ImplementationRoadmapItem]:
    roadmap = [
        ImplementationRoadmapItem(
            phase=ImplementationPhase.phase_1_read_only_analysis,
            title="Read-only workflow intelligence",
            objective="Introduce AI assistance for summarization, evidence review, policy lookup, and gap detection without allowing workflow writes.",
            recommended_actions=[
                "Connect approved workflow and policy documents through governed retrieval.",
                "Generate evidence-backed workflow analysis.",
                "Review data sensitivity and missing information findings.",
            ],
            exit_criteria=[
                "Analysis output passes quality, MCP operational, and evidence-grounding checks.",
                "Business reviewers confirm the output is useful and sufficiently grounded.",
            ],
            dependencies=[
                "Validated workflow packet",
                "Configured LLM provider",
                "Audit logging",
            ],
            evidence_references=default_evidence_refs,
        ),
        ImplementationRoadmapItem(
            phase=ImplementationPhase.phase_2_human_reviewed_recommendations,
            title="Human-reviewed AI recommendations",
            objective="Allow AI to prepare recommendations, reviewer summaries, and approval packages while keeping decisions with accountable humans.",
            recommended_actions=[
                "Define reviewer roles and approval gates.",
                "Add structured review queues for AI-prepared recommendations.",
                "Track acceptance, rejection, and revision reasons.",
            ],
            exit_criteria=[
                "Reviewers can trace recommendations to evidence.",
                "Approval decisions remain human-controlled.",
            ],
            dependencies=[
                "Defined approval policy",
                "Reviewer role mapping",
            ],
            evidence_references=default_evidence_refs,
        ),
        ImplementationRoadmapItem(
            phase=ImplementationPhase.phase_3_approval_gated_actions,
            title="Approval-gated workflow actions",
            objective="Introduce controlled write actions only where approvals, policy checks, and audit logging are enforced.",
            recommended_actions=[
                "Implement policy checks before write-capable tools.",
                "Require explicit approval tokens for controlled actions.",
                "Log every write attempt, approval, and result.",
            ],
            exit_criteria=[
                "No write-capable tool can execute without required approval.",
                "Audit trail is complete and reviewable.",
            ],
            dependencies=[
                "Policy enforcement",
                "Approval token design",
                "Write-tool audit logging",
            ],
            evidence_references=default_evidence_refs,
        ),
    ]

    if recommendation in {
        ReadinessRecommendation.strong_candidate,
        ReadinessRecommendation.good_candidate_with_controls,
    }:
        roadmap.append(
            ImplementationRoadmapItem(
                phase=ImplementationPhase.phase_4_limited_automation,
                title="Limited automation for low-risk repeatable actions",
                objective="Consider limited automation only for well-documented, low-risk steps with clear rollback and monitoring.",
                recommended_actions=[
                    "Identify low-risk repetitive actions.",
                    "Run parallel monitoring before autonomous execution.",
                    "Define rollback and exception-handling procedures.",
                ],
                exit_criteria=[
                    "Automation scope is narrow and documented.",
                    "Monitoring confirms accuracy, safety, and cost expectations.",
                ],
                dependencies=[
                    "Production monitoring",
                    "Exception handling",
                    "Rollback process",
                ],
                evidence_references=default_evidence_refs,
            )
        )

    return roadmap


def _build_cost_and_operations_notes() -> CostAndOperationsNotes:
    return CostAndOperationsNotes(
        expected_cost_drivers=[
            "LLM calls for workflow analysis and blueprint generation.",
            "Document retrieval and search volume.",
            "Model reasoning effort and context size.",
            "Repeated evaluation runs during testing or model comparison.",
        ],
        cost_controls=[
            "Use premium models only for milestone quality gates.",
            "Use cheaper models for schema, parsing, and smoke tests where appropriate.",
            "Cache workflow packet context and evidence catalogs when inputs have not changed.",
            "Track model usage, latency, and estimated cost per run.",
        ],
        operational_controls=[
            "Require governed tool access through MCP or equivalent policy-controlled interfaces.",
            "Log tool calls, approvals, artifact generation, and write attempts.",
            "Fail closed when policy, evidence, or approval requirements are missing.",
        ],
        observability_requirements=[
            "Model provider, model name, reasoning effort, token usage, and latency.",
            "Tool-call count and tool-call outcomes.",
            "Evaluation scores for quality, MCP operation, and evidence grounding.",
            "Audit-event latency and persistence errors.",
        ],
    )


def _extract_missing_information(llm_analysis: dict[str, Any]) -> list[str]:
    missing = []

    for item in _as_list(llm_analysis.get("missing_information")):
        text = _item_summary(item)
        if text:
            missing.append(text)

    return missing


def _extract_value_opportunities(llm_analysis: dict[str, Any]) -> list[str]:
    opportunities = []

    for item in _as_list(llm_analysis.get("implementation_recommendations"))[:5]:
        text = _item_summary(item)
        if text:
            opportunities.append(text)

    if opportunities:
        return opportunities

    return [
        "Use AI to summarize workflow context and identify missing information.",
        "Use AI to prepare human-review packages.",
        "Use AI to support evidence-backed decision making without autonomous writes.",
    ]


def _extract_primary_constraints(llm_analysis: dict[str, Any]) -> list[str]:
    constraints = []

    for item in _as_list(llm_analysis.get("risk_observations"))[:5]:
        text = _item_summary(item)
        if text:
            constraints.append(text)

    for item in _extract_missing_information(llm_analysis)[:3]:
        constraints.append(item)

    return constraints or [
        "Workflow actions should remain human-controlled until policy, approval, and audit controls are validated."
    ]


def _determine_confidence(llm_analysis: dict[str, Any]) -> str:
    confidence = llm_analysis.get("confidence_by_section")

    if isinstance(confidence, dict):
        values = [str(value).lower() for value in confidence.values()]
        if values and all(value in {"high", "strong"} for value in values):
            return "high"
        if any(value in {"low", "weak"} for value in values):
            return "mixed"

    return "moderate"


def _collect_section_refs(
    items: list[Any],
    default_evidence_refs: list[str],
) -> list[str]:
    refs: list[str] = []

    for item in items:
        refs.extend(_evidence_refs_from_item(item, []))

    return sorted(set(refs)) or default_evidence_refs


def _evidence_refs_from_item(
    item: Any,
    default_evidence_refs: list[str],
) -> list[str]:
    if not isinstance(item, dict):
        return default_evidence_refs

    value = item.get("evidence_references")
    refs = _as_string_list(value)

    return refs or default_evidence_refs


def _risk_level_from_text(text: str) -> RiskLevel:
    lowered = text.lower()

    if any(keyword in lowered for keyword in ["critical", "provision", "privileged", "access"]):
        return RiskLevel.critical

    if any(keyword in lowered for keyword in ["high", "approval", "write", "security", "sensitive"]):
        return RiskLevel.high

    if any(keyword in lowered for keyword in ["low", "minor"]):
        return RiskLevel.low

    return RiskLevel.medium


def _first_present(item: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue

        text = _as_text(value).strip()
        if text:
            return text

    return None


def _item_summary(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()

    if not isinstance(item, dict):
        return ""

    for key in [
        "summary",
        "observation",
        "description",
        "risk",
        "risk_description",
        "recommendation",
        "control",
        "control_description",
        "implementation_step",
        "action",
        "review_point",
    ]:
        value = item.get(key)
        if value:
            return _as_text(value).strip()

    return _as_text(item).strip()


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value

    if value is None:
        return []

    return [value]


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    return []


def _as_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return "; ".join(f"{key}: {_as_text(val)}" for key, val in value.items())

    if isinstance(value, list):
        return "; ".join(_as_text(item) for item in value)

    return str(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    if value is None:
        return None

    lowered = str(value).lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    return None

def _clamp_score(value: Any) -> int:
    score = _optional_int(value)

    if score is None:
        return 0

    return min(max(score, 0), 100)


def _shorten(value: str, max_length: int) -> str:
    value = value.strip()

    if len(value) <= max_length:
        return value

    return f"{value[: max_length - 3].rstrip()}..."