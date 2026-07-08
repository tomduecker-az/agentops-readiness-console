from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    workflow_name: str = Field(
        default="payment_reconciliation",
        description="Name of the workflow packet to analyze.",
    )


class WorkflowRunResponse(BaseModel):
    run_id: str
    workflow_name: str
    status: str
    message: str