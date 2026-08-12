from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.services.assessment_orchestrator import (
    AssessmentOptions,
    run_workflow_packet_assessment,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a Workflow Packet assessment."
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
        help="Output directory for assessment artifacts.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output/install locations.",
    )
    parser.add_argument(
        "--run-llm",
        action="store_true",
        help=(
            "Run MCP-enabled LLM shadow analysis and write "
            "llm_workflow_analysis locally. This may incur model cost."
        ),
    )
    parser.add_argument(
        "--run-analysis",
        action="store_true",
        help="Run local evaluators and deterministic blueprint generation.",
    )
    parser.add_argument(
        "--evaluation-profile-id",
        default=None,
        help=(
            "LLM shadow evaluation profile to use. "
            "For the access request packet demo, use access_request_review."
        ),
    )
    parser.add_argument(
        "--export-client-report",
        action="store_true",
        help="Generate a client-facing Markdown assessment report. This may incur model cost.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print result JSON.",
    )

    args = parser.parse_args()

    options = AssessmentOptions(
        workbook_path=Path(args.path),
        workflow_id=args.workflow_id,
        run_id=args.run_id,
        output_dir=Path(args.output_dir),
        overwrite=args.overwrite,
        run_llm=args.run_llm,
        run_analysis=args.run_analysis,
        evaluation_profile_id=args.evaluation_profile_id,
        export_client_report=args.export_client_report,
    )

    result = run_workflow_packet_assessment(options)

    _print_result(result)

    if args.print_json:
        print(json.dumps(result, indent=2))


def _print_result(result: dict[str, Any]) -> None:
    prepare_result = result["prepare_result"]
    analysis = result["analysis"]

    print("\nWorkflow Packet Assessment")
    print(f"- status: {result['status']}")
    print(f"- run_id: {result['run_id']}")
    print(f"- workflow_id: {result['workflow_id']}")
    print(f"- source_workbook: {result['source_workbook']}")
    print(f"- output_dir: {result['output_dir']}")
    print(f"- artifacts_dir: {result['artifacts_dir']}")
    print(f"- reports_dir: {result['reports_dir']}")
    print(f"- assessment_manifest_path: {result['assessment_manifest_path']}")
    print(f"- normalized_packet_path: {prepare_result['normalized_packet_path']}")
    print(f"- generated_workflow_dir: {prepare_result['generated_workflow']['output_dir']}")
    print(f"- installed_workflow_id: {prepare_result['installed_workflow_id']}")

    smoke_test = prepare_result.get("smoke_test")

    if smoke_test:
        print("- smoke_test: passed")
        print(f"- registered_document_count: {smoke_test['document_count']}")

    print(f"- analysis_status: {analysis['status']}")
    print(f"- run_llm: {analysis['run_llm']}")
    print(f"- run_analysis: {analysis['run_analysis']}")
    print(f"- export_client_report: {analysis['export_client_report']}")

    artifact_paths = analysis.get("artifact_paths", {})

    if artifact_paths:
        print("- local_artifacts:")
        for artifact_type, path in artifact_paths.items():
            print(f"  - {artifact_type}: {path}")

    report_paths = analysis.get("report_paths", {})

    if report_paths:
        print("- reports:")
        for report_type, path in report_paths.items():
            print(f"  - {report_type}: {path}")


if __name__ == "__main__":
    main()