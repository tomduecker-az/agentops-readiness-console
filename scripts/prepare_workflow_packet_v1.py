from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from workflow_core import get_registered_workflow, list_documents, read_document
from workflow_core.packet_v1_document_exporter import (
    export_workflow_packet_v1_documents,
)
from workflow_core.packet_v1_parser import parse_workflow_packet_v1
from workflow_core.packet_v1_validator import validate_workflow_packet_v1

from scripts.install_generated_workflow import install_generated_workflow


DEFAULT_NORMALIZED_OUTPUT_ROOT = "examples/normalized_packets"
DEFAULT_GENERATED_WORKFLOW_ROOT = "examples/generated_workflows"
DEFAULT_WORKFLOW_ROOT = "data/workflows"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare a completed Workflow Packet v1 workbook for analysis."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to completed Workflow Packet v1 workbook.",
    )
    parser.add_argument(
        "--workflow-id",
        default=None,
        help="Installed workflow ID. Defaults to the parsed workflow_id.",
    )
    parser.add_argument(
        "--normalized-output-root",
        default=DEFAULT_NORMALIZED_OUTPUT_ROOT,
        help=f"Where normalized packet JSON should be written. Default: {DEFAULT_NORMALIZED_OUTPUT_ROOT}",
    )
    parser.add_argument(
        "--generated-workflow-root",
        default=DEFAULT_GENERATED_WORKFLOW_ROOT,
        help=f"Where generated workflow docs should be written. Default: {DEFAULT_GENERATED_WORKFLOW_ROOT}",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install generated workflow into data/workflows.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing generated or installed workflow folders.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print result JSON.",
    )

    args = parser.parse_args()

    workbook_path = Path(args.path)

    result = prepare_workflow_packet_v1(
        workbook_path=workbook_path,
        requested_workflow_id=args.workflow_id,
        normalized_output_root=Path(args.normalized_output_root),
        generated_workflow_root=Path(args.generated_workflow_root),
        install=args.install,
        overwrite=args.overwrite,
    )

    _print_result(result)

    if args.print_json:
        print(json.dumps(result, indent=2))


def prepare_workflow_packet_v1(
    *,
    workbook_path: Path,
    requested_workflow_id: str | None,
    normalized_output_root: Path,
    generated_workflow_root: Path,
    install: bool,
    overwrite: bool,
) -> dict[str, Any]:
    validation_result = validate_workflow_packet_v1(workbook_path)

    if not validation_result.valid:
        _print_validation_failure(workbook_path, validation_result)
        raise SystemExit(1)

    packet = parse_workflow_packet_v1(
        workbook_path,
        validate_before_parse=False,
    )

    installed_workflow_id = requested_workflow_id or packet.workflow_id

    normalized_output_path = (
        normalized_output_root / f"{workbook_path.stem}_normalized_packet.json"
    )
    normalized_output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_output_path.write_text(
        json.dumps(asdict(packet), indent=2),
        encoding="utf-8",
    )

    generated_output_dir = generated_workflow_root / packet.workflow_id

    export_result = export_workflow_packet_v1_documents(
        packet=packet,
        output_dir=generated_output_dir,
        overwrite=overwrite,
    )

    install_result: dict[str, Any] | None = None
    smoke_test_result: dict[str, Any] | None = None

    if install:
        destination_dir = Path(DEFAULT_WORKFLOW_ROOT) / installed_workflow_id

        install_result = install_generated_workflow(
            source_dir=generated_output_dir,
            destination_dir=destination_dir,
            workflow_id=installed_workflow_id,
            overwrite=overwrite,
        )

        smoke_test_result = _smoke_test_installed_workflow(installed_workflow_id)

    return {
        "status": "prepared",
        "source_workbook": str(workbook_path),
        "workflow_id": packet.workflow_id,
        "workflow_name": packet.workflow_name,
        "installed_workflow_id": installed_workflow_id if install else None,
        "validation": {
            "valid": validation_result.valid,
            "error_count": validation_result.error_count,
            "warning_count": validation_result.warning_count,
            "issues": [asdict(issue) for issue in validation_result.issues],
        },
        "normalized_packet_path": str(normalized_output_path),
        "generated_workflow": export_result,
        "install": install_result,
        "smoke_test": smoke_test_result,
    }


def _smoke_test_installed_workflow(workflow_id: str) -> dict[str, Any]:
    workflow = get_registered_workflow(workflow_id)
    documents = list_documents(workflow_id)

    preview_document_id = documents[0].document_id if documents else None
    preview_length = 0

    if preview_document_id:
        document_content = read_document(workflow_id, preview_document_id)
        content_text = (
            getattr(document_content, "content", None)
            or getattr(document_content, "text", None)
            or getattr(document_content, "body", None)
            or str(document_content)
        )
        preview_length = len(content_text)

    return {
        "workflow_loaded": True,
        "workflow_id": workflow.workflow_id,
        "display_name": workflow.display_name,
        "packet_path": workflow.packet_path,
        "document_count": len(documents),
        "document_ids": [document.document_id for document in documents],
        "preview_document_id": preview_document_id,
        "preview_length": preview_length,
    }


def _print_result(result: dict[str, Any]) -> None:
    print("Workflow Packet v1 Prepare")
    print(f"- status: {result['status']}")
    print(f"- source_workbook: {result['source_workbook']}")
    print(f"- workflow_id: {result['workflow_id']}")
    print(f"- workflow_name: {result['workflow_name']}")
    print(f"- normalized_packet_path: {result['normalized_packet_path']}")
    print(f"- generated_workflow_dir: {result['generated_workflow']['output_dir']}")
    print(f"- generated_files: {len(result['generated_workflow']['files_written'])}")

    if result.get("install"):
        print(f"- installed_workflow_id: {result['installed_workflow_id']}")
        print(f"- installed_destination: {result['install']['destination_dir']}")

    if result.get("smoke_test"):
        smoke_test = result["smoke_test"]
        print("- smoke_test: passed")
        print(f"- registered_document_count: {smoke_test['document_count']}")


def _print_validation_failure(workbook_path: Path, validation_result: Any) -> None:
    print("Workflow Packet v1 Prepare")
    print(f"- source_workbook: {workbook_path}")
    print("- status: failed validation")
    print(f"- errors: {validation_result.error_count}")
    print(f"- warnings: {validation_result.warning_count}")

    if validation_result.issues:
        print("\nValidation issues:")
        for issue in validation_result.issues:
            print(
                f"- {issue.severity.upper()} | {issue.code} | "
                f"{issue.location} | {issue.message}"
            )


if __name__ == "__main__":
    main()