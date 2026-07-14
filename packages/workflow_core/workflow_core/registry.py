from pathlib import Path

from workflow_core.exceptions import WorkflowNotFoundError, WorkflowPacketInvalidError
from workflow_core.models import WorkflowDefinition, WorkflowDocument


PROJECT_ROOT = Path(__file__).resolve().parents[3]


REGISTERED_WORKFLOWS: dict[str, WorkflowDefinition] = {
    "payment_reconciliation": WorkflowDefinition(
        workflow_id="payment_reconciliation",
        display_name="Payment Reconciliation",
        description=(
            "An anonymized payment reconciliation and exception-handling workflow "
            "used to demonstrate governed enterprise workflow analysis."
        ),
        packet_path="data/sample_workflow_packet",
        documents=[
            WorkflowDocument(
                document_id="process_narrative",
                title="Process Narrative",
                relative_path="process_narrative.md",
                document_type="markdown",
            ),
            WorkflowDocument(
                document_id="current_workflow_steps",
                title="Current Workflow Steps",
                relative_path="current_workflow_steps.md",
                document_type="markdown",
            ),
            WorkflowDocument(
                document_id="policy_and_controls",
                title="Policy and Controls",
                relative_path="policy_and_controls.md",
                document_type="markdown",
            ),
            WorkflowDocument(
                document_id="sample_records",
                title="Sample Records",
                relative_path="sample_records.csv",
                document_type="csv",
            ),
        ],
    )
}


def list_registered_workflows() -> list[WorkflowDefinition]:
    return list(REGISTERED_WORKFLOWS.values())


def get_registered_workflow(workflow_id: str) -> WorkflowDefinition:
    workflow = REGISTERED_WORKFLOWS.get(workflow_id)

    if workflow is None:
        raise WorkflowNotFoundError(f"Workflow '{workflow_id}' is not registered.")

    validate_workflow_packet(workflow)

    return workflow


def validate_workflow_packet(workflow: WorkflowDefinition) -> None:
    packet_dir = PROJECT_ROOT / workflow.packet_path

    if not packet_dir.exists() or not packet_dir.is_dir():
        raise WorkflowPacketInvalidError(
            f"Workflow packet directory does not exist: {workflow.packet_path}"
        )

    missing_required_files: list[str] = []

    for document in workflow.documents:
        document_path = packet_dir / document.relative_path

        if document.required and not document_path.exists():
            missing_required_files.append(document.relative_path)

    if missing_required_files:
        missing = ", ".join(missing_required_files)
        raise WorkflowPacketInvalidError(
            f"Workflow '{workflow.workflow_id}' is missing required files: {missing}"
        )