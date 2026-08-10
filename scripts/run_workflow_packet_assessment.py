from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.prepare_workflow_packet_v1 import prepare_workflow_packet_v1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Workflow Packet v1 assessment intake flow."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to completed Workflow Packet v1 workbook.",
    )
    parser.add_argument(
        "--workflow-id",
        required=True,
        help="Workflow ID to install/register for analysis.",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Assessment run ID.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for assessment intake artifacts.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output/install locations.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print result JSON.",
    )

    args = parser.parse_args()

    result = run_workflow_packet_assessment(
        workbook_path=Path(args.path),
        workflow_id=args.workflow_id,
        run_id=args.run_id,
        output_dir=Path(args.output_dir),
        overwrite=args.overwrite,
    )

    _print_result(result)

    if args.print_json:
        print(json.dumps(result, indent=2))


def run_workflow_packet_assessment(
    *,
    workbook_path: Path,
    workflow_id: str,
    run_id: str,
    output_dir: Path,
    overwrite: bool,
) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory already exists and is not empty: {output_dir}. "
            "Use --overwrite to replace assessment intake artifacts."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    technical_dir = output_dir / "technical"
    generated_workflow_root = output_dir / "generated_workflows"

    prepare_result = prepare_workflow_packet_v1(
        workbook_path=workbook_path,
        requested_workflow_id=workflow_id,
        normalized_output_root=technical_dir,
        generated_workflow_root=generated_workflow_root,
        install=True,
        overwrite=overwrite,
    )

    result = {
        "status": "intake_prepared",
        "assessment_stage": "workflow_packet_intake",
        "run_id": run_id,
        "workflow_id": workflow_id,
        "source_workbook": str(workbook_path),
        "output_dir": str(output_dir),
        "prepare_result": prepare_result,
        "analysis": {
            "status": "not_started",
            "reason": (
                "Workflow packet intake is complete. Full analysis is not yet integrated "
                "into this command because upstream analysis artifacts must be generated "
                "before blueprint/diagnostic stages can run."
            ),
            "required_next_capability": "upstream_analysis_artifact_generation",
        },
    }

    manifest_path = output_dir / "assessment_manifest.json"
    manifest_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    readme_path = output_dir / "README.txt"
    readme_path.write_text(
        _render_readme(result),
        encoding="utf-8",
    )

    result["assessment_manifest_path"] = str(manifest_path)
    result["readme_path"] = str(readme_path)

    manifest_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    return result


def _print_result(result: dict[str, Any]) -> None:
    prepare_result = result["prepare_result"]

    print("Workflow Packet Assessment")
    print(f"- status: {result['status']}")
    print(f"- run_id: {result['run_id']}")
    print(f"- workflow_id: {result['workflow_id']}")
    print(f"- source_workbook: {result['source_workbook']}")
    print(f"- output_dir: {result['output_dir']}")
    print(f"- assessment_manifest_path: {result['assessment_manifest_path']}")
    print(f"- normalized_packet_path: {prepare_result['normalized_packet_path']}")
    print(f"- generated_workflow_dir: {prepare_result['generated_workflow']['output_dir']}")
    print(f"- installed_workflow_id: {prepare_result['installed_workflow_id']}")

    smoke_test = prepare_result.get("smoke_test")

    if smoke_test:
        print("- smoke_test: passed")
        print(f"- registered_document_count: {smoke_test['document_count']}")

    print(f"- analysis_status: {result['analysis']['status']}")
    print(f"- next_capability: {result['analysis']['required_next_capability']}")


def _render_readme(result: dict[str, Any]) -> str:
    prepare_result = result["prepare_result"]

    lines = [
        "Workflow Packet Assessment Intake",
        "",
        f"Status: {result['status']}",
        f"Run ID: {result['run_id']}",
        f"Workflow ID: {result['workflow_id']}",
        f"Source Workbook: {result['source_workbook']}",
        "",
        "Generated Artifacts",
        f"- Assessment manifest: {result.get('assessment_manifest_path', 'assessment_manifest.json')}",
        f"- Normalized packet: {prepare_result['normalized_packet_path']}",
        f"- Generated workflow directory: {prepare_result['generated_workflow']['output_dir']}",
        f"- Installed workflow ID: {prepare_result['installed_workflow_id']}",
        "",
        "Current Analysis Status",
        f"- {result['analysis']['status']}",
        "",
        "Next Step",
        "- Add upstream analysis artifact generation so this command can run the full blueprint and diagnostic pipeline.",
        "",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    main()