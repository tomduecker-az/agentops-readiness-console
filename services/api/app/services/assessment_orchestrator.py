from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.prepare_workflow_packet_v1 import prepare_workflow_packet_v1


@dataclass(frozen=True)
class AssessmentOptions:
    workbook_path: Path
    workflow_id: str
    run_id: str
    output_dir: Path
    overwrite: bool = False
    run_llm: bool = False
    run_analysis: bool = False
    evaluation_profile_id: str | None = None
    export_client_report: bool = False


def run_workflow_packet_assessment(
    options: AssessmentOptions,
) -> dict[str, Any]:
    output_dir = options.output_dir

    if output_dir.exists() and any(output_dir.iterdir()) and not options.overwrite:
        raise FileExistsError(
            f"Output directory already exists and is not empty: {output_dir}. "
            "Use overwrite=True to replace assessment artifacts."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    technical_dir = output_dir / "technical"
    generated_workflow_root = output_dir / "generated_workflows"
    artifacts_dir = technical_dir / "artifacts"
    reports_dir = output_dir / "reports"

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    prepare_result = prepare_workflow_packet_v1(
        workbook_path=options.workbook_path,
        requested_workflow_id=options.workflow_id,
        normalized_output_root=technical_dir,
        generated_workflow_root=generated_workflow_root,
        install=True,
        overwrite=options.overwrite,
    )

    if options.export_client_report and not options.run_analysis:
        raise ValueError("export_client_report requires run_analysis=True.")

    analysis_steps: list[dict[str, Any]] = []

    if options.run_llm:
        _run_module(
            [
                "scripts.run_mcp_llm_shadow_analysis",
                "--workflow-id",
                options.workflow_id,
                "--run-id",
                options.run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
                "--skip-audit",
            ],
            step_name="mcp_llm_shadow_analysis",
            analysis_steps=analysis_steps,
        )

    if options.run_analysis:
        llm_artifact_path = artifacts_dir / "llm_workflow_analysis.json"

        if not llm_artifact_path.exists():
            raise FileNotFoundError(
                f"Missing local LLM workflow analysis artifact: {llm_artifact_path}. "
                "Run with run_llm=True or provide an existing local artifact bundle."
            )

        evaluation_profile_id = options.evaluation_profile_id or options.workflow_id

        _run_module(
            [
                "scripts.evaluate_llm_shadow_analysis",
                "--workflow-id",
                options.workflow_id,
                "--evaluation-profile-id",
                evaluation_profile_id,
                "--run-id",
                options.run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
            ],
            step_name="llm_shadow_evaluation",
            analysis_steps=analysis_steps,
        )

        _run_module(
            [
                "scripts.evaluate_mcp_operational_readiness",
                "--workflow-id",
                options.workflow_id,
                "--run-id",
                options.run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
            ],
            step_name="mcp_operational_evaluation",
            analysis_steps=analysis_steps,
        )

        _run_module(
            [
                "scripts.evaluate_evidence_grounding",
                "--workflow-id",
                options.workflow_id,
                "--run-id",
                options.run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
            ],
            step_name="evidence_grounding_evaluation",
            analysis_steps=analysis_steps,
        )

        _run_module(
            [
                "scripts.generate_agentic_readiness_blueprint",
                "--workflow-id",
                options.workflow_id,
                "--run-id",
                options.run_id,
                "--artifacts-dir",
                str(artifacts_dir),
                "--skip-persist",
                "--skip-audit",
                "--export-json",
            ],
            step_name="agentic_readiness_blueprint",
            analysis_steps=analysis_steps,
        )

        if options.export_client_report:
            _run_module(
                [
                    "scripts.run_client_assessment_report",
                    "--workflow-id",
                    options.workflow_id,
                    "--run-id",
                    options.run_id,
                    "--artifacts-dir",
                    str(artifacts_dir),
                    "--normalized-packet-path",
                    prepare_result["normalized_packet_path"],
                    "--reports-dir",
                    str(reports_dir),
                ],
                step_name="client_assessment_report",
                analysis_steps=analysis_steps,
            )

    result = {
        "status": "assessment_completed" if options.run_analysis else "intake_prepared",
        "assessment_stage": (
            "workflow_packet_analysis"
            if options.run_analysis
            else "workflow_packet_intake"
        ),
        "run_id": options.run_id,
        "workflow_id": options.workflow_id,
        "source_workbook": str(options.workbook_path),
        "output_dir": str(output_dir),
        "artifacts_dir": str(artifacts_dir),
        "reports_dir": str(reports_dir),
        "prepare_result": prepare_result,
        "analysis": {
            "status": _analysis_status(
                run_llm=options.run_llm,
                run_analysis=options.run_analysis,
            ),
            "run_llm": options.run_llm,
            "run_analysis": options.run_analysis,
            "export_client_report": options.export_client_report,
            "evaluation_profile_id": options.evaluation_profile_id,
            "steps": analysis_steps,
            "artifact_paths": _artifact_paths(artifacts_dir),
            "report_paths": _report_paths(reports_dir),
        },
    }

    manifest_path = output_dir / "assessment_manifest.json"
    readme_path = output_dir / "README.txt"

    result["assessment_manifest_path"] = str(manifest_path)
    result["readme_path"] = str(readme_path)

    manifest_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    readme_path.write_text(_render_readme(result), encoding="utf-8")

    return result


def _run_module(
    args: list[str],
    *,
    step_name: str,
    analysis_steps: list[dict[str, Any]],
) -> None:
    command = [sys.executable, "-m", *args]

    print(f"\nRunning assessment step: {step_name}")
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
        "client_assessment_report",
    ]

    return {
        artifact_name: str(artifacts_dir / f"{artifact_name}.json")
        for artifact_name in artifact_names
        if (artifacts_dir / f"{artifact_name}.json").exists()
    }


def _report_paths(reports_dir: Path) -> dict[str, str]:
    report_names = [
        "client_assessment_report",
    ]

    return {
        report_name: str(reports_dir / f"{report_name}.md")
        for report_name in report_names
        if (reports_dir / f"{report_name}.md").exists()
    }


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
    lines.append("Reports")

    report_paths = analysis.get("report_paths", {})

    if report_paths:
        for report_type, path in report_paths.items():
            lines.append(f"- {report_type}: {path}")
    else:
        lines.append("- No reports generated yet.")

    lines.append("")

    return "\n".join(lines)