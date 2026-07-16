import os
from typing import Any

from project_mgmt_core import IssueCreationRequest
from project_mgmt_core import create_issue as core_create_issue


def create_issue(
    title: str,
    body: str,
    labels: list[str] | None = None,
    approval_granted: bool = False,
    approval_reference: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Create a GitHub issue after human approval.

    By default this runs in dry-run mode so the write path can be tested safely.
    Real issue creation requires dry_run=False, approval_granted=True, and an
    approval_reference.
    """

    request = IssueCreationRequest(
        title=title,
        body=body,
        labels=labels or [],
        approval_granted=approval_granted,
        approval_reference=approval_reference,
        dry_run=dry_run,
    )

    result = core_create_issue(
        request=request,
        github_token=os.getenv("GITHUB_TOKEN"),
        github_owner=os.getenv("GITHUB_OWNER"),
        github_repo=os.getenv("GITHUB_REPO"),
    )

    return result.model_dump(mode="json")


def register_project_mgmt_tools(mcp: Any) -> None:
    mcp.tool()(create_issue)