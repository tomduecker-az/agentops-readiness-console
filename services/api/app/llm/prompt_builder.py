from pathlib import Path

from app.services.workflow_registry import get_registered_workflow


ROOT_DIR = Path(__file__).resolve().parents[4]


def build_workflow_packet_prompt(workflow_id: str) -> str:
    workflow = get_registered_workflow(workflow_id)
    packet_dir = ROOT_DIR / workflow.packet_path

    document_blocks = []

    for document in workflow.documents:
        document_path = packet_dir / document.relative_path
        content = document_path.read_text(encoding="utf-8")

        document_blocks.append(
            "\n".join(
                [
                    f"## Document: {document.title}",
                    f"document_id: {document.document_id}",
                    f"document_type: {document.document_type}",
                    "",
                    content,
                ]
            )
        )

    return "\n\n---\n\n".join(
        [
            "# Workflow Packet",
            f"workflow_id: {workflow.workflow_id}",
            f"display_name: {workflow.display_name}",
            f"description: {workflow.description}",
            "",
            "\n\n---\n\n".join(document_blocks),
        ]
    )