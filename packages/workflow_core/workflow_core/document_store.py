from pathlib import Path

from workflow_core.exceptions import DocumentNotFoundError, UnsafeDocumentPathError
from workflow_core.models import DocumentContent, WorkflowDefinition, WorkflowDocument
from workflow_core.registry import PROJECT_ROOT, get_registered_workflow


def list_documents(workflow_id: str) -> list[WorkflowDocument]:
    workflow = get_registered_workflow(workflow_id)
    return workflow.documents


def get_document_definition(
    workflow: WorkflowDefinition,
    document_id: str,
) -> WorkflowDocument:
    for document in workflow.documents:
        if document.document_id == document_id:
            return document

    raise DocumentNotFoundError(
        f"Document '{document_id}' is not registered for workflow '{workflow.workflow_id}'."
    )


def resolve_document_path(workflow_id: str, document_id: str) -> Path:
    workflow = get_registered_workflow(workflow_id)
    document = get_document_definition(workflow, document_id)

    packet_dir = PROJECT_ROOT / workflow.packet_path
    document_path = packet_dir / document.relative_path

    resolved_packet_dir = packet_dir.resolve()
    resolved_document_path = document_path.resolve()

    if not resolved_document_path.is_relative_to(resolved_packet_dir):
        raise UnsafeDocumentPathError(
            f"Resolved document path is outside the workflow packet: {document_id}"
        )

    if not resolved_document_path.exists() or not resolved_document_path.is_file():
        raise DocumentNotFoundError(
            f"Document file does not exist for '{document_id}'."
        )

    return resolved_document_path


def read_document(workflow_id: str, document_id: str) -> DocumentContent:
    workflow = get_registered_workflow(workflow_id)
    document = get_document_definition(workflow, document_id)
    document_path = resolve_document_path(workflow_id, document_id)

    content = document_path.read_text(encoding="utf-8")

    return DocumentContent(
        workflow_id=workflow_id,
        document_id=document.document_id,
        title=document.title,
        document_type=document.document_type,
        content=content,
    )