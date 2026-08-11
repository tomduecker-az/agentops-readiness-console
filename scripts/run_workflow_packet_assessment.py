from __future__ import annotations

import argparse
import json
import subprocess
import sys
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
        "--run-llm",
        action="store_true",
        help="Run MCP-enabled LLM shadow analysis and write llm_workflow_analysis locally. This may incur model cost.",
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
        run_llm=args.run_llm,
        run_analysis=args.run_analysis,
        evaluation_profile_id=args.evaluation_profile_id,
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
    run_llm: bool,
    run_analysis: bool,
    evaluation_profile_id: str | None,
) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory already exists and is not empty: {output_dir}. "
            "Use --overwrite to replace assessment intake artifacts."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    technical_dir = output_dir / "technical"
    generated_workflow_root = output_dir / "generated_workflows"
    artifacts_dir = technical_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    prepare_result = prepare_workflow_packet_v1(
        workbook_path=workbook_path,
        requested_workflow_id=workflow_id,
        normalized_output_root=technical_dir,
        generated_workflow_root=generated_workflow_root,
        install=True,
        overwrite=overwrite,
    )

    analysis_steps: list[dict[str, Any]] = []

    if run_llm:
        _run_command(
            [
                sys.executable,
                "-m",
                "scripts.run_mcp_llm_shadow_analysis",
                "--workflow-id",
                workflow_id,
                "--run-id",
                run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
                "--skip-audit",
            ],
            step_name="mcp_llm_shadow_analysis",
            analysis_steps=analysis_steps,
        )

    if run_analysis:
        llm_artifact_path = artifacts_dir / "llm_workflow_analysis.json"

        if not llm_artifact_path.exists():
            raise FileNotFoundError(
                f"Missing local LLM workflow analysis artifact: {llm_artifact_path}. "
                "Run with --run-llm or provide an existing local artifact bundle."
            )

        resolved_evaluation_profile_id = evaluation_profile_id or workflow_id

        _run_command(
            [
                sys.executable,
                "-m",
                "scripts.evaluate_llm_shadow_analysis",
                "--workflow-id",
                workflow_id,
                "--evaluation-profile-id",
                resolved_evaluation_profile_id,
                "--run-id",
                run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
            ],
            step_name="llm_shadow_evaluation",
            analysis_steps=analysis_steps,
        )

        _run_command(
            [
                sys.executable,
                "-m",
                "scripts.evaluate_mcp_operational_readiness",
                "--workflow-id",
                workflow_id,
                "--run-id",
                run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
            ],
            step_name="mcp_operational_evaluation",
            analysis_steps=analysis_steps,
        )

        _run_command(
            [
                sys.executable,
                "-m",
                "scripts.evaluate_evidence_grounding",
                "--workflow-id",
                workflow_id,
                "--run-id",
                run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
            ],
            step_name="evidence_grounding_evaluation",
            analysis_steps=analysis_steps,
        )

        _run_command(
            [
                sys.executable,
                "-m",
                "scripts.generate_agentic_readiness_blueprint",
                "--workflow-id",
                workflow_id,
                "--run-id",
                run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
                "--skip-audit",
                "--export-json",
            ],
            step_name="agentic_readiness_blueprint",
            analysis_steps=analysis_steps,
        )

    result = {
        "status": "assessment_completed" if run_analysis else "intake_prepared",
        "assessment_stage": (
            "workflow_packet_analysis" if run_analysis else "workflow_packet_intake"
        ),
        "run_id": run_id,
        "workflow_id": workflow_id,
        "source_workbook": str(workbook_path),
        "output_dir": str(output_dir),
        "artifacts_dir": str(artifacts_dir),
        "prepare_result": prepare_result,
        "analysis": {
            "status": _analysis_status(
                run_llm=run_llm,
                run_analysis=run_analysis,
            ),
            "run_llm": run_llm,
            "run_analysis": run_analysis,
            "evaluation_profile_id": evaluation_profile_id,
            "steps": analysis_steps,
            "artifact_paths": _artifact_paths(artifacts_dir),
        },
    }

    manifest_path = output_dir / "assessment_manifest.json"
    readme_path = output_dir / "README.txt"

    result["assessment_manifest_path"] = str(manifest_path)
    result["readme_path"] = str(readme_path)

    manifest_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    readme_path.write_text(
        _render_readme(result),
        encoding="utf-8",
    )

    return result


def _run_command(
    command: list[str],
    *,
    step_name: str,
    analysis_steps: list[dict[str, Any]],
) -> None:
    print(f"\nRunning analysis step: {step_name}")
    print("+ " + " ".join(command))

    subprocess.run(command, check=True)

    analysis_steps.append(
        {
            "step_name": step_name,
            "status": "completed",
            "command": command,
        }
    )


def _artifact_paths(artifacts_dir: Path) -> dict[str, str]:
    artifact_names = [
        "llm_workflow_analysis",
        "llm_shadow_evaluation",
        "mcp_operational_evaluation",
        "evidence_grounding_evaluation",
        "agentic_readiness_blueprint",
    ]

    paths: dict[str, str] = {}

    for artifact_name in artifact_names:
        path = artifacts_dir / f"{artifact_name}.json"

        if path.exists():
            paths[artifact_name] = str(path)

    return paths


def _analysis_status(
    *,
    run_llm: bool,
    run_analysis: bool,
) -> str:
    if run_analysis:
        return "completed"

    if run_llm:
        return "llm_artifact_created"

    return "not_started"


def _print_result(result: dict[str, Any]) -> None:
    prepare_result = result["prepare_result"]

    print("\nWorkflow Packet Assessment")
    print(f"- status: {result['status']}")
    print(f"- run_id: {result['run_id']}")
    print(f"- workflow_id: {result['workflow_id']}")
    print(f"- source_workbook: {result['source_workbook']}")
    print(f"- output_dir: {result['output_dir']}")
    print(f"- artifacts_dir: {result['artifacts_dir']}")
    print(f"- assessment_manifest_path: {result['assessment_manifest_path']}")
    print(f"- normalized_packet_path: {prepare_result['normalized_packet_path']}")
    print(f"- generated_workflow_dir: {prepare_result['generated_workflow']['output_dir']}")
    print(f"- installed_workflow_id: {prepare_result['installed_workflow_id']}")

    smoke_test = prepare_result.get("smoke_test")

    if smoke_test:
        print("- smoke_test: passed")
        print(f"- registered_document_count: {smoke_test['document_count']}")

    print(f"- analysis_status: {result['analysis']['status']}")

    artifact_paths = result["analysis"]["artifact_paths"]

    if artifact_paths:
        print("- local_artifacts:")
        for artifact_type, path in artifact_paths.items():
            print(f"  - {artifact_type}: {path}")


def _render_readme(result: dict[str, Any]) -> str:
    prepare_result = result["prepare_result"]
    analysis = result["analysis"]

    lines = [
        "Workflow Packet Assessment",
        "",
        f"Status: {result['status']}",
        f"Run ID: {result['run_id']}",
        f"Workflow ID: {result['workflow_id']}",
        f"Source Workbook: {result['source_workbook']}",
        "",
        "Generated Intake Artifacts",
        f"- Assessment manifest: {result.get('assessment_manifest_path', 'assessment_manifest.json')}",
        f"- Normalized packet: {prepare_result['normalized_packet_path']}",
        f"- Generated workflow directory: {prepare_result['generated_workflow']['output_dir']}",
        f"- Installed workflow ID: {prepare_result['installed_workflow_id']}",
        "",
        "Analysis Status",
        f"- {analysis['status']}",
        "",
        "Local Analysis Artifacts",
    ]

    artifact_paths = analysis.get("artifact_paths", {})

    if artifact_paths:
        for artifact_type, path in artifact_paths.items():
            lines.append(f"- {artifact_type}: {path}")
    else:
        lines.append("- No local analysis artifacts generated yet.")

    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()