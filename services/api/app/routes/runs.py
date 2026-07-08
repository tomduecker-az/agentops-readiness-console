from fastapi import APIRouter
from app.schemas.runs import WorkflowRunRequest, WorkflowRunResponse

router = APIRouter()


@router.post("", response_model=WorkflowRunResponse)
async def create_workflow_run(request: WorkflowRunRequest) -> WorkflowRunResponse:
    return WorkflowRunResponse(
        run_id="local-dev-placeholder",
        workflow_id=request.workflow_id,
        status="received",
        message="Workflow run accepted. Agent orchestration is not implemented yet.",
    )