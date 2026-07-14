from enum import Enum
from pydantic import BaseModel, Field


class DataSensitivity(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    pii = "pii"
    financial_internal = "financial_internal"


class ToolAccessLevel(str, Enum):
    read = "read"
    append = "append"
    write = "write"


class AutonomyLevel(str, Enum):
    no_ai = "no_ai"
    assistive = "assistive"
    recommend_only = "recommend_only"
    draft_action = "draft_action"
    execute_with_approval = "execute_with_approval"
    autonomous_execution = "autonomous_execution"


class PolicyDecision(str, Enum):
    allow = "allow"
    block = "block"
    require_approval = "require_approval"


class DataClassificationResult(BaseModel):
    data_element: str
    sensitivity: DataSensitivity
    allowed_in_model_context: bool
    requires_redaction: bool
    rationale: str


class ToolPermissionResult(BaseModel):
    tool_name: str
    agent_name: str
    access_level: ToolAccessLevel
    decision: PolicyDecision
    requires_human_approval: bool
    rationale: str


class RequiredControl(BaseModel):
    control_id: str
    name: str
    description: str
    applies_to: list[str] = Field(default_factory=list)


class RequiredControlsResult(BaseModel):
    workflow_step: str
    controls: list[RequiredControl] = Field(default_factory=list)