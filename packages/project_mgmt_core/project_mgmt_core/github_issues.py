import httpx

from project_mgmt_core.exceptions import (
    ApprovalRequiredError,
    IssueCreationError,
    ProjectMgmtConfigurationError,
)
from project_mgmt_core.models import IssueCreationRequest, IssueCreationResult


def create_issue(
    request: IssueCreationRequest,
    github_token: str | None = None,
    github_owner: str | None = None,
    github_repo: str | None = None,
) -> IssueCreationResult:
    if not request.approval_granted or not request.approval_reference:
        raise ApprovalRequiredError(
            "GitHub issue creation requires human approval and an approval reference."
        )

    if request.dry_run:
        return IssueCreationResult(
            status="dry_run",
            title=request.title,
            issue_number=None,
            issue_url=None,
            dry_run=True,
            approval_reference=request.approval_reference,
            message="Dry run succeeded. No GitHub issue was created.",
        )

    if not github_token or not github_owner or not github_repo:
        raise ProjectMgmtConfigurationError(
            "GitHub token, owner, and repo are required for real issue creation."
        )

    url = f"https://api.github.com/repos/{github_owner}/{github_repo}/issues"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    payload = {
        "title": request.title,
        "body": request.body,
        "labels": request.labels,
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise IssueCreationError(f"GitHub issue creation failed: {exc}") from exc

    data = response.json()

    return IssueCreationResult(
        status="created",
        title=request.title,
        issue_number=data.get("number"),
        issue_url=data.get("html_url"),
        dry_run=False,
        approval_reference=request.approval_reference,
        message="GitHub issue created successfully.",
    )