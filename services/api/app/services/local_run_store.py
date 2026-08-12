from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LocalAssessmentRun:
    workflow_id: str
    run_id: str
    assessment_name: str
    output_dir: Path
    input_dir: Path
    workbook_path: Path
    status_path: Path
    manifest_path: Path
    reports_dir: Path
    artifacts_dir: Path


def create_local_assessment_run(
    *,
    assessment_name: str,
    output_root: Path,
) -> LocalAssessmentRun:
    workflow_id = slugify(assessment_name)

    if not workflow_id:
        raise ValueError("Assessment name is required.")

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_id = f"run_local_{workflow_id}_{timestamp}"

    output_dir = output_root / workflow_id / run_id
    input_dir = output_dir / "input"
    reports_dir = output_dir / "reports"
    artifacts_dir = output_dir / "technical" / "artifacts"

    input_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    run = LocalAssessmentRun(
        workflow_id=workflow_id,
        run_id=run_id,
        assessment_name=assessment_name,
        output_dir=output_dir,
        input_dir=input_dir,
        workbook_path=input_dir / "workflow_packet.xlsx",
        status_path=output_dir / "run_status.json",
        manifest_path=output_dir / "assessment_manifest.json",
        reports_dir=reports_dir,
        artifacts_dir=artifacts_dir,
    )

    write_run_status(
        run,
        status="created",
        stage="upload",
        message="Assessment run created.",
    )

    return run


def get_local_assessment_run(
    *,
    output_root: Path,
    workflow_id: str,
    run_id: str,
) -> LocalAssessmentRun:
    safe_workflow_id = slugify(workflow_id)
    safe_run_id = slugify(run_id)

    output_dir = output_root / safe_workflow_id / safe_run_id

    return LocalAssessmentRun(
        workflow_id=safe_workflow_id,
        run_id=safe_run_id,
        assessment_name=safe_workflow_id,
        output_dir=output_dir,
        input_dir=output_dir / "input",
        workbook_path=output_dir / "input" / "workflow_packet.xlsx",
        status_path=output_dir / "run_status.json",
        manifest_path=output_dir / "assessment_manifest.json",
        reports_dir=output_dir / "reports",
        artifacts_dir=output_dir / "technical" / "artifacts",
    )


def write_input_workbook(
    *,
    run: LocalAssessmentRun,
    workbook_bytes: bytes,
) -> None:
    run.input_dir.mkdir(parents=True, exist_ok=True)
    run.workbook_path.write_bytes(workbook_bytes)


def write_run_status(
    run: LocalAssessmentRun,
    *,
    status: str,
    stage: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    now = datetime.now(UTC).isoformat()

    existing = read_run_status(run) or {}

    payload = {
        "workflow_id": run.workflow_id,
        "run_id": run.run_id,
        "assessment_name": run.assessment_name,
        "status": status,
        "stage": stage,
        "message": message,
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "output_dir": str(run.output_dir),
        "input_workbook": str(run.workbook_path),
        "manifest_path": str(run.manifest_path),
        "reports_dir": str(run.reports_dir),
        "artifacts_dir": str(run.artifacts_dir),
        "details": details or {},
    }

    run.status_path.parent.mkdir(parents=True, exist_ok=True)
    run.status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_run_status(run: LocalAssessmentRun) -> dict[str, Any] | None:
    if not run.status_path.exists():
        return None

    return json.loads(run.status_path.read_text(encoding="utf-8"))


def read_manifest(run: LocalAssessmentRun) -> dict[str, Any] | None:
    if not run.manifest_path.exists():
        return None

    return json.loads(run.manifest_path.read_text(encoding="utf-8"))


def client_report_path(run: LocalAssessmentRun) -> Path:
    return run.reports_dir / "client_assessment_report.md"


def package_zip_path(run: LocalAssessmentRun) -> Path:
    return run.output_dir.parent / f"{run.run_id}_assessment_package.zip"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")