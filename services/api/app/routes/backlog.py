from uuid import uuid4

from fastapi import APIRouter, HTTPException

from audit_core import AuditEventType

from app.mcp_clients.project_mgmt_gateway import (
    ProjectMgmtGatewayError,
    create_issue_from_backlog_item,
)
from app.schemas.artifacts import ArtifactStatus, ArtifactType
from app.schemas.backlog import BacklogApprovalRequest, BacklogApprovalResponse
from app.services.artifact_service import (
    get_artifact_for_run_by_type,
    update_artifact_content,
)
from app.services.audit_service import log_audit_event

router = APIRouter()


@router.post(
    "/{run_id}/backlog/{backlog_id}/approve",
    response_model=BacklogApprovalResponse,
)
async def approve_backlog_item(
    run_id: str,
    backlog_id: str,
    request: BacklogApprovalRequest,
) -> BacklogApprovalResponse:
    backlog_artifact = get_artifact_for_run_by_type(
        run_id=run_id,
        artifact_type=ArtifactType.implementation_backlog,
    )

    if backlog_artifact is None:
        raise HTTPException(
            status_code=404,
            detail=f"No implementation backlog artifact found for run '{run_id}'.",
        )

    content = backlog_artifact.content
    backlog_items = content.get("backlog_items", [])

    backlog_item = _find_backlog_item(
        backlog_items=backlog_items,
        backlog_id=backlog_id,
    )

    if backlog_item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Backlog item '{backlog_id}' was not found for run '{run_id}'.",
        )

    approval_reference = request.approval_reference or f"approval_{uuid4().hex}"

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.approval_granted,
        actor=request.approved_by,
        details={
            "backlog_id": backlog_id,
            "approval_reference": approval_reference,
            "dry_run": request.dry_run,
        },
    )

    try:
        issue_creation_result = create_issue_from_backlog_item(
            run_id=run_id,
            backlog_item=backlog_item,
            approval_reference=approval_reference,
            labels=request.labels,
            dry_run=request.dry_run,
        )
    except ProjectMgmtGatewayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    backlog_item["status"] = "approved"
    backlog_item["approval_reference"] = approval_reference
    backlog_item["approved_by"] = request.approved_by
    backlog_item["dry_run"] = request.dry_run
    backlog_item["issue_creation_result"] = issue_creation_result
    backlog_item["github_issue_created"] = (
        issue_creation_result.get("status") == "created"
    )

    content["summary"] = _rebuild_summary(backlog_items)

    update_artifact_content(
        artifact_id=backlog_artifact.artifact_id,
        content=content,
        status=ArtifactStatus.ready_for_review,
    )

    return BacklogApprovalResponse(
        run_id=run_id,
        backlog_id=backlog_id,
        status="approved",
        approval_reference=approval_reference,
        dry_run=request.dry_run,
        issue_creation_result=issue_creation_result,
        message="Backlog item approved and project-management write action completed.",
    )


def _find_backlog_item(
    backlog_items: list[dict],
    backlog_id: str,
) -> dict | None:
    for item in backlog_items:
        if item.get("backlog_id") == backlog_id:
            return item

    return None


def _rebuild_summary(backlog_items: list[dict]) -> dict:
    high_priority_count = sum(
        1 for item in backlog_items if item.get("priority") == "high"
    )

    approval_required_count = sum(
        1
        for item in backlog_items
        if item.get("requires_human_approval_before_execution")
    )

    approved_count = sum(
        1 for item in backlog_items if item.get("status") == "approved"
    )

    github_issues_created = sum(
        1 for item in backlog_items if item.get("github_issue_created")
    )

    return {
        "backlog_item_count": len(backlog_items),
        "high_priority_count": high_priority_count,
        "approval_required_count": approval_required_count,
        "approved_count": approved_count,
        "github_issues_created": github_issues_created,
    }