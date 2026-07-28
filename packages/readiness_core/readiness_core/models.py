from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReadinessRecommendation(str, Enum):
    strong_candidate = "strong_candidate"
    good_candidate_with_controls = "good_candidate_with_controls"
    limited_candidate = "limited_candidate"
    not_recommended = "not_recommended"
    insufficient_information = "insufficient_information"


class AutonomyPosture(str, Enum):
    manual_only = "manual_only"
    ai_assist = "ai_assist"
    ai_recommend_human_approve = "ai_recommend_human_approve"
    approval_gated_action = "approval_gated_action"
    limited_automation_candidate = "limited_automation_candidate"
    not_suitable_for_ai = "not_suitable_for_ai"


class OperationType(str, Enum):
    read = "read"
    write = "write"
    mixed = "mixed"
    external_communication = "external_communication"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ImplementationPhase(str, Enum):
    phase_1_read_only_analysis = "phase_1_read_only_analysis"
    phase_2_human_reviewed_recommendations = "phase_2_human_reviewed_recommendations"
    phase_3_approval_gated_actions = "phase_3_approval_gated_actions"
    phase_4_limited_automation = "phase_4_limited_automation"
    not_recommended = "not_recommended"


class EvidenceReference(BaseModel):
    evidence_id: str
    evidence_type: str | None = None
    source_title: str | None = None
    summary: str | None = None


class ReadinessScore(BaseModel):
    dimension: str
    score: int = Field(ge=0, le=100)
    rationale: str
    evidence_references: list[str] = Field(default_factory=list)


class ExecutiveSummary(BaseModel):
    workflow_name: str
    recommendation: ReadinessRecommendation
    summary: str
    primary_value_opportunities: list[str] = Field(default_factory=list)
    primary_constraints: list[str] = Field(default_factory=list)
    confidence: str


class StepAutonomyRecommendation(BaseModel):
    step_id: str
    step_name: str
    current_step_summary: str
    recommended_posture: AutonomyPosture
    why_ai_is_useful: str | None = None
    why_ai_should_be_limited: str | None = None
    allowed_ai_actions: list[str] = Field(default_factory=list)
    blocked_ai_actions: list[str] = Field(default_factory=list)
    required_human_reviewer: str | None = None
    approval_required: bool
    audit_required: bool
    risk_level: RiskLevel
    implementation_phase: ImplementationPhase
    evidence_references: list[str] = Field(default_factory=list)


class ToolCapabilityRecommendation(BaseModel):
    capability_name: str
    capability_description: str
    operation_type: OperationType
    recommended_access: AutonomyPosture
    risk_level: RiskLevel
    approval_required: bool
    audit_required: bool
    mcp_server_candidate: str | None = None
    implementation_phase: ImplementationPhase
    evidence_references: list[str] = Field(default_factory=list)


class HumanApprovalGate(BaseModel):
    gate_name: str
    trigger_condition: str
    required_reviewer: str
    decision_required: str
    agent_allowed_before_approval: list[str] = Field(default_factory=list)
    blocked_without_approval: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)


class RiskControlSummaryItem(BaseModel):
    risk_id: str
    risk_description: str
    risk_level: RiskLevel
    recommended_controls: list[str] = Field(default_factory=list)
    owner_role: str | None = None
    evidence_references: list[str] = Field(default_factory=list)


class ImplementationRoadmapItem(BaseModel):
    phase: ImplementationPhase
    title: str
    objective: str
    recommended_actions: list[str] = Field(default_factory=list)
    exit_criteria: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)


class CostAndOperationsNotes(BaseModel):
    expected_cost_drivers: list[str] = Field(default_factory=list)
    cost_controls: list[str] = Field(default_factory=list)
    operational_controls: list[str] = Field(default_factory=list)
    observability_requirements: list[str] = Field(default_factory=list)


class BlueprintValidationSummary(BaseModel):
    llm_quality_score: int | None = None
    mcp_operational_score: int | None = None
    evidence_grounding_score: int | None = None
    passed_quality_gate: bool | None = None
    passed_mcp_gate: bool | None = None
    passed_evidence_gate: bool | None = None


class AgenticReadinessBlueprint(BaseModel):
    blueprint_version: str = "0.1.0"
    workflow_id: str
    run_id: str
    created_at: str

    executive_summary: ExecutiveSummary
    readiness_scorecard: list[ReadinessScore]
    step_level_autonomy_matrix: list[StepAutonomyRecommendation]
    tooling_blueprint: list[ToolCapabilityRecommendation]
    human_approval_gates: list[HumanApprovalGate]
    risk_control_summary: list[RiskControlSummaryItem]
    implementation_roadmap: list[ImplementationRoadmapItem]
    cost_and_operations_notes: CostAndOperationsNotes
    validation_summary: BlueprintValidationSummary
    evidence_catalog: list[EvidenceReference] = Field(default_factory=list)
    limitations_and_missing_information: list[str] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)