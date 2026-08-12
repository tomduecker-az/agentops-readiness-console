from __future__ import annotations

import re
from datetime import UTC, datetime
import shutil
from pathlib import Path

import markdown as markdown_lib
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, BackgroundTasks, File, Form, Request, UploadFile

from app.services.assessment_orchestrator import (
    AssessmentOptions,
    run_workflow_packet_assessment,
)
from app.services.local_run_store import (
    client_report_path,
    create_local_assessment_run,
    get_local_assessment_run,
    package_zip_path,
    read_manifest,
    read_run_status,
    slugify,
    write_input_workbook,
    write_run_status,
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
    run_analysis: bool = Form(False),
    run_llm: bool = Form(False),
    export_client_report: bool = Form(False),
) -> HTMLResponse:
    try:
        run = create_local_assessment_run(
            assessment_name=assessment_name,
            output_root=_LOCAL_OUTPUT_ROOT,
        )
    except ValueError as exc:
        return _error_response(
            request=request,
            title="Invalid assessment name",
            message=str(exc),
            status_code=400,
        )

    if not workbook.filename or not workbook.filename.lower().endswith(".xlsx"):
        write_run_status(
            run,
            status="failed",
            stage="upload",
            message="Invalid upload. Expected a .xlsx Workflow Packet workbook.",
        )
        return _error_response(
            request=request,
            title="Invalid file",
            message="Please upload a completed .xlsx Workflow Packet workbook.",
            status_code=400,
        )

    write_input_workbook(
        run=run,
        workbook_bytes=await workbook.read(),
    )

    if export_client_report and not run_analysis:
        return _error_response(
            request=request,
            title="Invalid run options",
            message="Generating a client-facing report requires assessment analysis.",
            status_code=400,
        )

    if run_llm and not run_analysis:
        return _error_response(
            request=request,
            title="Invalid run options",
            message="Fresh LLM workflow analysis should be run with assessment analysis enabled.",
            status_code=400,
        )

    try:
        write_run_status(
            run,
            status="running",
            stage="assessment",
            message="Assessment pipeline started.",
            details={
                "run_analysis": run_analysis,
                "run_llm": run_llm,
                "export_client_report": export_client_report,
            },
        )

        result = run_workflow_packet_assessment(
            AssessmentOptions(
                workbook_path=run.workbook_path,
                workflow_id=run.workflow_id,
                run_id=run.run_id,
                output_dir=run.output_dir,
                overwrite=True,
                run_llm=run_llm,
                run_analysis=run_analysis,
                evaluation_profile_id=evaluation_profile_id,
                export_client_report=export_client_report,
            )
        )

        write_run_status(
            run,
            status="completed",
            stage="completed",
            message="Assessment completed successfully.",
            details={
                "assessment_status": result.get("status"),
                "analysis_status": result.get("analysis", {}).get("status"),
            },
        )

    except Exception as exc:
        write_run_status(
            run,
            status="failed",
            stage="assessment",
            message=str(exc),
        )

        return _error_response(
            request=request,
            title="Assessment failed",
            message=str(exc),
            status_code=500,
        )

    report_path_value = (
        result.get("analysis", {})
        .get("report_paths", {})
        .get("client_assessment_report")
    )

    report_path = Path(report_path_value) if report_path_value else None

    return _report_response(
        request=request,
        title="Assessment Result",
        workflow_id=run.workflow_id,
        run_id=run.run_id,
        output_dir=run.output_dir,
        report_path=report_path if report_path and report_path.is_file() else None,
        result=result,
         run_status=read_run_status(run),
    )


@router.get("/assessments/{workflow_id}/{run_id}", response_class=HTMLResponse)
async def view_assessment_run(
    request: Request,
    workflow_id: str,
    run_id: str,
) -> HTMLResponse:
    run = get_local_assessment_run(
        output_root=_LOCAL_OUTPUT_ROOT,
        workflow_id=workflow_id,
        run_id=run_id,
    )

    run_status = read_run_status(run)

    if not run.output_dir.exists():
        return _error_response(
            request=request,
            title="Assessment run not found",
            message=f"No local assessment run exists at {run.output_dir}",
            status_code=404,
        )

    result = read_manifest(run)
    report_path = client_report_path(run)

    return _report_response(
        request=request,
        title="Assessment Result",
        workflow_id=run.workflow_id,
        run_id=run.run_id,
        output_dir=run.output_dir,
        report_path=report_path if report_path.is_file() else None,
        result=result,
        run_status=run_status,
    )


@router.post("/assessments/{workflow_id}/{run_id}/run-full")
async def run_full_assessment(
    request: Request,
    background_tasks: BackgroundTasks,
    workflow_id: str,
    run_id: str,
    evaluation_profile_id: str = Form("access_request_review"),
    run_llm: bool = Form(False),
    export_client_report: bool = Form(False),
    confirm_api_cost: bool = Form(False),
):
    run = get_local_assessment_run(
        output_root=_LOCAL_OUTPUT_ROOT,
        workflow_id=workflow_id,
        run_id=run_id,
    )

    if not run.output_dir.exists():
        return _error_response(
            request=request,
            title="Assessment run not found",
            message=f"No local assessment run exists at {run.output_dir}",
            status_code=404,
        )

    if not run.workbook_path.exists():
        return _error_response(
            request=request,
            title="Uploaded workbook not found",
            message=f"Expected uploaded workbook at {run.workbook_path}",
            status_code=404,
        )

    if (run_llm or export_client_report) and not confirm_api_cost:
        return _error_response(
            request=request,
            title="API cost confirmation required",
            message=(
                "Fresh LLM workflow analysis or client report generation may incur API cost. "
                "Confirm API cost before running the full assessment."
            ),
            status_code=400,
        )

    existing_llm_artifact = run.artifacts_dir / "llm_workflow_analysis.json"

    if not run_llm and not existing_llm_artifact.exists():
        return _error_response(
            request=request,
            title="LLM workflow analysis required",
            message=(
                "This run does not have an existing LLM workflow analysis artifact. "
                "Enable fresh LLM workflow analysis to run the full assessment."
            ),
            status_code=400,
        )

    write_run_status(
        run,
        status="queued",
        stage="full_assessment",
        message="Full assessment queued.",
        details={
            "run_analysis": True,
            "run_llm": run_llm,
            "export_client_report": export_client_report,
            "evaluation_profile_id": evaluation_profile_id,
        },
    )

    background_tasks.add_task(
        _execute_full_assessment_background,
        workflow_id=run.workflow_id,
        run_id=run.run_id,
        evaluation_profile_id=evaluation_profile_id,
        run_llm=run_llm,
        export_client_report=export_client_report,
    )

    return RedirectResponse(
        url=f"/assessments/{run.workflow_id}/{run.run_id}",
        status_code=303,
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

@router.get("/demo/access-review/report.md")
async def download_demo_report() -> FileResponse:
    if not _DEMO_REPORT_PATH.exists():
        raise FileNotFoundError(f"Demo report not found: {_DEMO_REPORT_PATH}")

    return FileResponse(
        path=_DEMO_REPORT_PATH,
        media_type="text/markdown",
        filename="access_review_packet_copilot_demo_report.md",
    )


@router.get("/assessments/{workflow_id}/{run_id}/report.md")
async def download_assessment_report(
    workflow_id: str,
    run_id: str,
) -> FileResponse:
    assessment_dir = _assessment_dir(workflow_id, run_id)
    report_path = assessment_dir / "reports" / "client_assessment_report.md"

    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")

    return FileResponse(
        path=report_path,
        media_type="text/markdown",
        filename=f"{workflow_id}_{run_id}_client_assessment_report.md",
    )


@router.get("/assessments/{workflow_id}/{run_id}/manifest.json")
async def download_assessment_manifest(
    workflow_id: str,
    run_id: str,
) -> FileResponse:
    assessment_dir = _assessment_dir(workflow_id, run_id)
    manifest_path = assessment_dir / "assessment_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    return FileResponse(
        path=manifest_path,
        media_type="application/json",
        filename=f"{workflow_id}_{run_id}_assessment_manifest.json",
    )


@router.get("/assessments/{workflow_id}/{run_id}/package.zip")
async def download_assessment_package(
    workflow_id: str,
    run_id: str,
) -> FileResponse:
    assessment_dir = _assessment_dir(workflow_id, run_id)

    if not assessment_dir.exists():
        raise FileNotFoundError(f"Assessment folder not found: {assessment_dir}")

    zip_base = assessment_dir.parent / f"{run_id}_assessment_package"
    zip_path = Path(f"{zip_base}.zip")

    if zip_path.exists():
        zip_path.unlink()

    shutil.make_archive(
        base_name=str(zip_base),
        format="zip",
        root_dir=assessment_dir,
    )

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{workflow_id}_{run_id}_assessment_package.zip",
    )

def _execute_full_assessment_background(
    *,
    workflow_id: str,
    run_id: str,
    evaluation_profile_id: str,
    run_llm: bool,
    export_client_report: bool,
) -> None:
    run = get_local_assessment_run(
        output_root=_LOCAL_OUTPUT_ROOT,
        workflow_id=workflow_id,
        run_id=run_id,
    )

    try:
        write_run_status(
            run,
            status="running",
            stage="full_assessment",
            message="Full assessment pipeline is running.",
            details={
                "run_analysis": True,
                "run_llm": run_llm,
                "export_client_report": export_client_report,
                "evaluation_profile_id": evaluation_profile_id,
            },
        )

        result = run_workflow_packet_assessment(
            AssessmentOptions(
                workbook_path=run.workbook_path,
                workflow_id=run.workflow_id,
                run_id=run.run_id,
                output_dir=run.output_dir,
                overwrite=True,
                run_llm=run_llm,
                run_analysis=True,
                evaluation_profile_id=evaluation_profile_id,
                export_client_report=export_client_report,
            )
        )

        write_run_status(
            run,
            status="completed",
            stage="completed",
            message="Full assessment completed successfully.",
            details={
                "assessment_status": result.get("status"),
                "analysis_status": result.get("analysis", {}).get("status"),
                "report_paths": result.get("analysis", {}).get("report_paths", {}),
            },
        )

    except Exception as exc:
        write_run_status(
            run,
            status="failed",
            stage="full_assessment",
            message=str(exc),
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
    run_status: dict | None = None,
) -> HTMLResponse:
    report_html = ""

    if report_path and report_path.is_file():
        report_markdown = report_path.read_text(encoding="utf-8")
        report_html = markdown_lib.markdown(
            report_markdown,
            extensions=["tables", "fenced_code"],
        )

    is_demo = workflow_id == "access_request_review_packet_demo"

    if is_demo:
        report_download_url = "/demo/access-review/report.md"
        manifest_download_url = None
        package_download_url = None
    else:
        report_download_url = f"/assessments/{workflow_id}/{run_id}/report.md"
        manifest_download_url = f"/assessments/{workflow_id}/{run_id}/manifest.json"
        package_download_url = f"/assessments/{workflow_id}/{run_id}/package.zip"

    is_run_active = bool(
        run_status
        and run_status.get("status") in {"queued", "running"}
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
            "run_status": run_status,
            "workspace_summary": _workspace_summary(result),
            "report_download_url": report_download_url if report_path else None,
            "manifest_download_url": manifest_download_url,
            "package_download_url": package_download_url,
            "is_run_active": is_run_active,
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

def _workspace_summary(result: dict | None) -> dict | None:
    if not result:
        return None

    prepare_result = result.get("prepare_result", {})
    validation = prepare_result.get("validation", {})
    generated_workflow = prepare_result.get("generated_workflow", {})
    smoke_test = prepare_result.get("smoke_test", {})
    analysis = result.get("analysis", {})

    files_written = generated_workflow.get("files_written", [])
    artifact_paths = analysis.get("artifact_paths", {})
    report_paths = analysis.get("report_paths", {})

    validation_valid = validation.get("valid")
    validation_label = "Passed" if validation_valid else "Needs review"

    return {
        "status": result.get("status", ""),
        "stage": result.get("assessment_stage", ""),
        "validation_label": validation_label,
        "error_count": validation.get("error_count", 0),
        "warning_count": validation.get("warning_count", 0),
        "normalized_packet_path": prepare_result.get("normalized_packet_path"),
        "generated_workflow_dir": generated_workflow.get("output_dir"),
        "installed_workflow_id": prepare_result.get("installed_workflow_id"),
        "generated_file_count": len(files_written),
        "registered_document_count": smoke_test.get("document_count"),
        "analysis_status": analysis.get("status", "not_started"),
        "artifact_count": len(artifact_paths),
        "report_count": len(report_paths),
        "manifest_path": result.get("assessment_manifest_path"),
        "readme_path": result.get("readme_path"),
    }

def _assessment_dir(workflow_id: str, run_id: str) -> Path:
    return get_local_assessment_run(
        output_root=_LOCAL_OUTPUT_ROOT,
        workflow_id=workflow_id,
        run_id=run_id,
    ).output_dir

