import json
from pathlib import Path

from pydantic import ValidationError

from workflow_core.exceptions import WorkflowNotFoundError, WorkflowPacketInvalidError
from workflow_core.models import WorkflowDefinition


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"


def list_registered_workflows() -> list[WorkflowDefinition]:
    workflows = _load_registered_workflows()
    return list(workflows.values())


def get_registered_workflow(workflow_id: str) -> WorkflowDefinition:
    workflows = _load_registered_workflows()

    workflow = workflows.get(workflow_id)

    if workflow is None:
        available = ", ".join(sorted(workflows.keys())) or "none"
        raise WorkflowNotFoundError(
            f"Workflow '{workflow_id}' is not registered. Available workflows: {available}."
        )

    return workflow


def validate_workflow_packet(workflow: WorkflowDefinition) -> None:
    packet_dir = (PROJECT_ROOT / workflow.packet_path).resolve()
    data_dir = DATA_DIR.resolve()

    if not packet_dir.exists() or not packet_dir.is_dir():
        raise WorkflowPacketInvalidError(
            f"Workflow packet path does not exist or is not a directory: {workflow.packet_path}"
        )

    if not packet_dir.is_relative_to(data_dir):
        raise WorkflowPacketInvalidError(
            f"Workflow packet must live under the data directory: {workflow.packet_path}"
        )

    missing_required_files: list[str] = []

    for document in workflow.documents:
        document_path = (packet_dir / document.relative_path).resolve()

        if not document_path.is_relative_to(packet_dir):
            raise WorkflowPacketInvalidError(
                f"Document path escapes workflow packet directory: {document.relative_path}"
            )

        if document.required and not document_path.exists():
            missing_required_files.append(document.relative_path)

    if missing_required_files:
        raise WorkflowPacketInvalidError(
            "Workflow packet is missing required files: "
            + ", ".join(missing_required_files)
        )


def _load_registered_workflows() -> dict[str, WorkflowDefinition]:
    workflows: dict[str, WorkflowDefinition] = {}

    for manifest_path in _find_manifest_paths():
        workflow = _load_workflow_manifest(manifest_path)
        validate_workflow_packet(workflow)

        if workflow.workflow_id in workflows:
            raise WorkflowPacketInvalidError(
                f"Duplicate workflow_id found in workflow manifests: {workflow.workflow_id}"
            )

        workflows[workflow.workflow_id] = workflow

    return workflows


def _find_manifest_paths() -> list[Path]:
    if not DATA_DIR.exists():
        return []

    return sorted(DATA_DIR.glob("workflows/*/workflow_manifest.json"))


def _load_workflow_manifest(manifest_path: Path) -> WorkflowDefinition:
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        workflow = WorkflowDefinition.model_validate(raw_manifest)
    except json.JSONDecodeError as exc:
        raise WorkflowPacketInvalidError(
            f"Workflow manifest is not valid JSON: {manifest_path}"
        ) from exc
    except ValidationError as exc:
        raise WorkflowPacketInvalidError(
            f"Workflow manifest does not match expected schema: {manifest_path}. {exc}"
        ) from exc

    manifest_parent = manifest_path.parent.resolve()
    packet_dir = (PROJECT_ROOT / workflow.packet_path).resolve()

    if packet_dir != manifest_parent:
        raise WorkflowPacketInvalidError(
            "Workflow manifest packet_path must match the manifest directory. "
            f"Manifest: {manifest_path}, packet_path: {workflow.packet_path}"
        )

    return workflow