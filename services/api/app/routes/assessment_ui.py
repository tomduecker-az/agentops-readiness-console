from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import markdown as markdown_lib
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.assessment_orchestrator import (
    AssessmentOptions,
    run_workflow_packet_assessment,
)


router = APIRouter(tags=["assessment-ui"])

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
_LOCAL_OUTPUT_ROOT = _REPO_ROOT / "local_assessments"

_DEMO_REPORT_PATH = (
    _REPO_ROOT
    / "examples"
    / "assessment_outputs"
    / "access_request_review_packet_demo"
    / "reports"
    / "client_assessment_report.md"
)

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "assessment_home.html",
        {
            "request": request,
            "demo_report_exists": _DEMO_REPORT_PATH.exists(),
        },
    )


@router.get("/assessments/new", response_class=HTMLResponse)
async def new_assessment(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "assessment_new.html",
        {
            "request": request,
            "default_workflow_id": "access_request_review_local",
            "default_evaluation_profile_id": "access_request_review",
        },
    )


@router.post("/assessments", response_class=HTMLResponse)
async def create_assessment(
    request: Request,
    workbook: UploadFile = File(...),
    assessment_name: str = Form(...),
    evaluation_profile_id: str = Form("access_request_review"),
    run_llm: bool = Form(False),
    export_client_report: bool = Form(False),
) -> HTMLResponse:
    workflow_id = _slug(assessment_name)

    if not workflow_id:
        return _error_response(
            request=request,
            title="Invalid assessment name",
            message="Assessment name is required.",
            status_code=400,
        )

    if not workbook.filename or not workbook.filename.lower().endswith(".xlsx"):
        return _error_response(
            request=request,
            title="Invalid file",
            message="Please upload a completed .xlsx Workflow Packet workbook.",
            status_code=400,
        )

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_id = f"run_local_{workflow_id}_{timestamp}"

    output_dir = _LOCAL_OUTPUT_ROOT / workflow_id / run_id
    input_dir = output_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = input_dir / "workflow_packet.xlsx"
    workbook_path.write_bytes(await workbook.read())

    try:
        result = run_workflow_packet_assessment(
            AssessmentOptions(
                workbook_path=workbook_path,
                workflow_id=workflow_id,
                run_id=run_id,
                output_dir=output_dir,
                overwrite=True,
                run_llm=run_llm,
                run_analysis=True,
                evaluation_profile_id=evaluation_profile_id,
                export_client_report=export_client_report,
            )
        )
    except Exception as exc:
        return _error_response(
            request=request,
            title="Assessment failed",
            message=str(exc),
            status_code=500,
        )

    report_path = Path(
        result.get("analysis", {})
        .get("report_paths", {})
        .get("client_assessment_report", "")
    )

    return _report_response(
        request=request,
        title="Assessment Result",
        workflow_id=workflow_id,
        run_id=run_id,
        output_dir=output_dir,
        report_path=report_path if report_path.exists() else None,
        result=result,
    )


@router.get("/demo/access-review", response_class=HTMLResponse)
async def demo_access_review_report(request: Request) -> HTMLResponse:
    if not _DEMO_REPORT_PATH.exists():
        return _error_response(
            request=request,
            title="Demo report not found",
            message=f"Expected demo report at {_DEMO_REPORT_PATH}",
            status_code=404,
        )

    return _report_response(
        request=request,
        title="Access Review Packet Copilot Demo",
        workflow_id="access_request_review_packet_demo",
        run_id="run_packet_demo_001",
        output_dir=_DEMO_REPORT_PATH.parents[1],
        report_path=_DEMO_REPORT_PATH,
        result=None,
    )


def _report_response(
    *,
    request: Request,
    title: str,
    workflow_id: str,
    run_id: str,
    output_dir: Path,
    report_path: Path | None,
    result: dict | None,
) -> HTMLResponse:
    report_markdown = ""
    report_html = ""

    if report_path and report_path.exists():
        report_markdown = report_path.read_text(encoding="utf-8")
        report_html = markdown_lib.markdown(
            report_markdown,
            extensions=["tables", "fenced_code"],
        )

    return templates.TemplateResponse(
        "assessment_result.html",
        {
            "request": request,
            "title": title,
            "workflow_id": workflow_id,
            "run_id": run_id,
            "output_dir": output_dir,
            "report_path": report_path,
            "report_html": report_html,
            "result": result,
        },
    )


def _error_response(
    *,
    request: Request,
    title: str,
    message: str,
    status_code: int,
) -> HTMLResponse:
    return templates.TemplateResponse(
        "assessment_error.html",
        {
            "request": request,
            "title": title,
            "message": message,
        },
        status_code=status_code,
    )


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")