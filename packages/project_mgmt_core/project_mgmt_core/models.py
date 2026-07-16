from pydantic import BaseModel, Field


class IssueCreationRequest(BaseModel):
    title: str
    body: str
    labels: list[str] = Field(default_factory=list)
    approval_granted: bool = False
    approval_reference: str | None = None
    dry_run: bool = True


class IssueCreationResult(BaseModel):
    status: str
    title: str
    issue_number: int | None = None
    issue_url: str | None = None
    dry_run: bool
    approval_reference: str | None = None
    message: str