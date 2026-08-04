from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AutomationCeiling(str, Enum):
    read_only_ai_assist = "read_only_ai_assist"
    human_reviewed_recommendations = "human_reviewed_recommendations"
    approval_gated_actions = "approval_gated_actions"
    limited_automation_candidate = "limited_automation_candidate"
    not_ready_for_agentic_ai = "not_ready_for_agentic_ai"
    insufficient_information = "insufficient_information"


class DiagnosticSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class UseCaseRisk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class UseCaseReadiness(str, Enum):
    ready_for_discovery = "ready_for_discovery"
    ready_for_pilot = "ready_for_pilot"
    needs_process_redesign = "needs_process_redesign"
    needs_control_definition = "needs_control_definition"
    not_recommended = "not_recommended"


class EvidenceLinkedFinding(BaseModel):
    finding_id: str
    title: str
    finding: str
    why_it_matters: str
    severity: DiagnosticSeverity
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class AutomationCeilingAssessment(BaseModel):
    current_ceiling: AutomationCeiling
    ceiling_summary: str
    why_this_is_the_ceiling: list[str] = Field(default_factory=list)
    what_would_raise_the_ceiling: list[str] = Field(default_factory=list)
    what_prevents_higher_autonomy: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class ReadinessBlocker(BaseModel):
    blocker_id: str
    title: str
    description: str
    business_impact: str
    technical_or_control_impact: str
    severity: DiagnosticSeverity
    recommended_remediation: list[str] = Field(default_factory=list)
    owner_role: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class AIUseCaseRecommendation(BaseModel):
    use_case_id: str
    title: str
    description: str
    why_this_is_recommended: list[str] = Field(default_factory=list)
    expected_value: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    required_controls: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)
    risk_level: UseCaseRisk
    readiness: UseCaseReadiness
    suggested_pilot_scope: str
    success_measures: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class UseCaseToAvoid(BaseModel):
    use_case_id: str
    title: str
    why_to_avoid_now: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    conditions_that_would_change_recommendation: list[str] = Field(default_factory=list)
    risk_level: UseCaseRisk
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class ProcessRedesignRequirement(BaseModel):
    requirement_id: str
    title: str
    current_gap: str
    required_change: str
    why_required_for_ai_readiness: str
    unlocks: list[str] = Field(default_factory=list)
    owner_role: str | None = None
    priority: DiagnosticSeverity
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class ControlGapRemediation(BaseModel):
    control_gap_id: str
    title: str
    current_gap: str
    risk_if_unresolved: str
    recommended_control: str
    validation_method: str
    owner_role: str | None = None
    priority: DiagnosticSeverity
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class ValueHypothesis(BaseModel):
    hypothesis_id: str
    value_area: str
    hypothesis: str
    expected_directional_impact: str
    required_measurements: list[str] = Field(default_factory=list)
    baseline_data_needed: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel
    evidence_references: list[str] = Field(default_factory=list)


class MeasurementPlanItem(BaseModel):
    metric_name: str
    why_it_matters: str
    how_to_measure: str
    baseline_required: bool
    target_or_success_signal: str | None = None


class SampleRecordOpportunity(BaseModel):
    record_id: str
    recommended_handling: str
    ai_assistance_opportunities: list[str] = Field(default_factory=list)
    human_review_triggers: list[str] = Field(default_factory=list)
    blocked_or_sensitive_fields: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class FutureStateRecommendation(BaseModel):
    recommendation_id: str
    title: str
    current_state_issue: str
    future_state_change: str
    expected_benefit: str
    required_controls: list[str] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class DiagnosticBacklogItem(BaseModel):
    backlog_id: str
    title: str
    description: str
    priority: DiagnosticSeverity
    owner_role: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)


class WorkflowOwnerQuestion(BaseModel):
    question_id: str
    question: str
    why_it_matters: str
    answer_needed_for: list[str] = Field(default_factory=list)
    priority: DiagnosticSeverity


class ExecutiveDiagnosticSummary(BaseModel):
    headline: str
    recommendation: str
    current_automation_ceiling: AutomationCeiling
    recommended_first_pilot: str
    do_not_start_with: list[str] = Field(default_factory=list)
    top_blockers: list[str] = Field(default_factory=list)
    next_30_days: list[str] = Field(default_factory=list)
    executive_takeaway: str

class NonObviousInsight(BaseModel):
    insight_id: str
    title: str
    insight: str
    why_it_is_not_obvious: str
    business_implication: str
    recommended_action: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class AutomationMisconception(BaseModel):
    misconception_id: str
    tempting_but_wrong_idea: str
    why_it_is_wrong_or_premature: str
    safer_alternative: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class OperationalPatternAnalysis(BaseModel):
    pattern_id: str
    workflow_pattern: str
    operational_dependency: str
    ai_opportunity_created_by_pattern: str
    ai_limitation_created_by_pattern: str
    what_this_means_for_the_pilot: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class PilotLearningObjective(BaseModel):
    objective_id: str
    objective: str
    why_it_matters: str
    how_to_test: str
    pass_fail_signal: str
    expansion_decision_supported: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class AutonomyUnlockStage(BaseModel):
    stage_id: str
    from_ceiling: AutomationCeiling
    to_ceiling: AutomationCeiling
    required_changes: list[str] = Field(default_factory=list)
    validation_required: list[str] = Field(default_factory=list)
    risks_that_must_be_reduced: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class SampleRecordPattern(BaseModel):
    pattern_id: str
    pattern_name: str
    records_observed: list[str] = Field(default_factory=list)
    what_the_pattern_shows: str
    ai_opportunity: str
    risk_or_limitation: str
    recommended_handling: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class WorkflowAIOpportunityDiagnostic(BaseModel):
    diagnostic_version: str = "0.2.0"
    workflow_id: str
    run_id: str
    created_at: str

    executive_summary: ExecutiveDiagnosticSummary
    automation_ceiling: AutomationCeilingAssessment
    key_findings: list[EvidenceLinkedFinding] = Field(default_factory=list)
    
    non_obvious_insights: list[NonObviousInsight] = Field(default_factory=list)
    automation_misconceptions: list[AutomationMisconception] = Field(default_factory=list)
    operational_pattern_analysis: list[OperationalPatternAnalysis] = Field(default_factory=list)
    pilot_learning_objectives: list[PilotLearningObjective] = Field(default_factory=list)
    autonomy_unlock_path: list[AutonomyUnlockStage] = Field(default_factory=list)
    sample_record_patterns: list[SampleRecordPattern] = Field(default_factory=list)
    top_readiness_blockers: list[ReadinessBlocker] = Field(default_factory=list)
    recommended_first_use_case: AIUseCaseRecommendation
    additional_candidate_use_cases: list[AIUseCaseRecommendation] = Field(default_factory=list)
    use_cases_to_avoid: list[UseCaseToAvoid] = Field(default_factory=list)
    process_redesign_requirements: list[ProcessRedesignRequirement] = Field(default_factory=list)
    control_gap_remediation_plan: list[ControlGapRemediation] = Field(default_factory=list)
    value_hypotheses: list[ValueHypothesis] = Field(default_factory=list)
    measurement_plan: list[MeasurementPlanItem] = Field(default_factory=list)
    sample_record_opportunity_analysis: list[SampleRecordOpportunity] = Field(default_factory=list)
    future_state_recommendations: list[FutureStateRecommendation] = Field(default_factory=list)
    diagnostic_backlog: list[DiagnosticBacklogItem] = Field(default_factory=list)
    questions_for_workflow_owner: list[WorkflowOwnerQuestion] = Field(default_factory=list)

    evidence_catalog: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)