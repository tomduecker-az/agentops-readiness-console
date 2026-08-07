from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkflowStepV1:
    step_id: str
    step_name: str
    sequence: int | float
    owner_role: str
    trigger_or_input: str
    activity: str
    decision_or_rule: str
    systems_used: list[str]
    data_used: list[str]
    output: str
    exceptions_or_escalations: str
    current_pain_points: str


@dataclass(frozen=True)
class PolicyControlV1:
    control_id: str
    control_name: str
    control_type: str
    applies_to_steps: list[str]
    requirement: str
    approval_required: bool
    approval_role: str
    evidence_required: str
    write_action_allowed: bool
    retention_requirement: str
    source_reference: str


@dataclass(frozen=True)
class DataFieldV1:
    field_name: str
    business_meaning: str
    source_system: str
    data_category: str
    required_for_workflow: bool
    model_context_allowed: bool
    redaction_required: bool
    allowed_values: list[str]
    used_in_steps: list[str]
    notes: str


@dataclass(frozen=True)
class TargetSystemV1:
    system_name: str
    system_type: str
    read_access_possible: bool
    write_access_possible: bool
    owner_role: str
    authentication_method: str
    notes: str


@dataclass(frozen=True)
class WorkflowPacketV1:
    packet_version: str
    workflow_id: str
    workflow_name: str
    overview: dict[str, str]
    workflow_steps: list[WorkflowStepV1]
    policy_controls: list[PolicyControlV1]
    data_dictionary: list[DataFieldV1]
    sample_records: list[dict[str, Any]]
    goals_metrics: dict[str, str] = field(default_factory=dict)
    target_systems: list[TargetSystemV1] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)