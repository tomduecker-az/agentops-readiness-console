from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.llm.client_report_advisor import (
    generate_client_assessment_report,
    render_client_assessment_report_markdown,
)
from app.schemas.artifacts import ArtifactType
from scripts.local_artifacts import load_local_artifacts, write_local_artifact


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a client-facing AI workflow assessment report."
    )
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument("--normalized-packet-path", required=True)
    parser.add_argument("--packet-quality-review-path", required=False)
    parser.add_argument("--reports-dir", required=True)
    parser.add_argument("--print-json", action="store_true")

    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts_dir)
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    normalized_packet = _read_json(Path(args.normalized_packet_path))
    artifacts = load_local_artifacts(artifacts_dir)

    llm_workflow_analysis = _required_artifact_content(
        artifacts=artifacts,
        artifact_type=ArtifactType.llm_workflow_analysis.value,
    )

    agentic_readiness_blueprint = _required_artifact_content(
        artifacts=artifacts,
        artifact_type=ArtifactType.agentic_readiness_blueprint.value,
    )

    packet_quality_review = None
    if args.packet_quality_review_path:
        packet_quality_review = _read_json(Path(args.packet_quality_review_path))
    else:
        packet_quality_review = _optional_artifact_content(
            artifacts=artifacts,
            artifact_type="packet_quality_review",
        )

    print("Generating client assessment report...")
    print(f"- workflow_id: {args.workflow_id}")
    print(f"- run_id: {args.run_id}")

    report = generate_client_assessment_report(
        workflow_id=args.workflow_id,
        run_id=args.run_id,
        normalized_packet=normalized_packet,
        llm_workflow_analysis=llm_workflow_analysis,
        agentic_readiness_blueprint=agentic_readiness_blueprint,
        packet_quality_review=packet_quality_review,
    )

    report_json_path = write_local_artifact(
        artifacts_dir=artifacts_dir,
        artifact_type=ArtifactType.client_assessment_report.value,
        content=report,
    )

    markdown = render_client_assessment_report_markdown(report)
    report_md_path = reports_dir / "client_assessment_report.md"
    report_md_path.write_text(markdown, encoding="utf-8")

    print("\nClient report generated")
    print(f"- report_json_path: {report_json_path}")
    print(f"- report_markdown_path: {report_md_path}")
    print(f"- title: {report.get('report_title')}")

    if args.print_json:
        print(json.dumps(report, indent=2))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_artifact_content(
    *,
    artifacts: list[dict[str, Any]],
    artifact_type: str,
) -> dict[str, Any]:
    for artifact in artifacts:
        if artifact.get("artifact_type") == artifact_type:
            content = artifact.get("content")
            if isinstance(content, dict):
                return content

    raise FileNotFoundError(f"Missing required local artifact: {artifact_type}.json")


def _optional_artifact_content(
    *,
    artifacts: list[dict[str, Any]],
    artifact_type: str,
) -> dict[str, Any] | None:
    for artifact in artifacts:
        if artifact.get("artifact_type") == artifact_type:
            content = artifact.get("content")
            if isinstance(content, dict):
                return content

    return None


if __name__ == "__main__":
    main()