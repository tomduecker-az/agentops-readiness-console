from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    workflow_id: str = Field(
        default="payment_reconciliation",
        description="Registered workflow identifier to analyze.",
    )


class WorkflowRunResponse(BaseModel):
    run_id: str
    workflow_id: str
    status: str
    message: str