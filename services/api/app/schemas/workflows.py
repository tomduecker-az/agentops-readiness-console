from pydantic import BaseModel, Field


class WorkflowDocument(BaseModel):
    document_id: str
    title: str
    relative_path: str
    document_type: str
    required: bool = True


class WorkflowDefinition(BaseModel):
    workflow_id: str
    display_name: str
    description: str
    packet_path: str
    documents: list[WorkflowDocument] = Field(default_factory=list)