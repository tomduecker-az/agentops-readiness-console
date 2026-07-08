from enum import Enum
from pydantic import BaseModel, Field


class BacklogPriority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class BacklogItemStatus(str, Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    created = "created"


class BacklogItem(BaseModel):
    item_id: str
    run_id: str
    title: str
    user_story: str
    business_value: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: BacklogPriority = BacklogPriority.medium
    related_workflow_step: str | None = None
    related_control: str | None = None
    status: BacklogItemStatus = BacklogItemStatus.proposed
    github_issue_url: str | None = None