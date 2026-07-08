from enum import Enum
from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    workflow_map = "workflow_map"
    risk_control_matrix = "risk_control_matrix"
    hitl_design = "hitl_design"
    implementation_backlog = "implementation_backlog"


class ArtifactStatus(str, Enum):
    draft = "draft"
    ready_for_review = "ready_for_review"
    approved = "approved"
    rejected = "rejected"


class AnalysisArtifact(BaseModel):
    artifact_id: str
    run_id: str
    artifact_type: ArtifactType
    status: ArtifactStatus = ArtifactStatus.draft
    content: dict = Field(default_factory=dict)