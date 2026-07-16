from typing import Any

from pydantic import BaseModel, Field


class BacklogApprovalRequest(BaseModel):
    approved_by: str = Field(
        default="human_reviewer",
        description="Person or reviewer role approving the backlog write action.",
    )
    approval_reference: str | None = Field(
        default=None,
        description="Optional external approval reference. If omitted, one is generated.",
    )
    dry_run: bool = Field(
        default=True,
        description="When true, simulate issue creation without writing to GitHub.",
    )
    labels: list[str] = Field(
        default_factory=lambda: ["agentops", "approved-backlog"],
        description="Labels to apply if a GitHub issue is created.",
    )


class BacklogApprovalResponse(BaseModel):
    run_id: str
    backlog_id: str
    status: str
    approval_reference: str
    dry_run: bool
    issue_creation_result: dict[str, Any]
    message: str