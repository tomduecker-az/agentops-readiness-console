from fastapi import FastAPI

from app.core.config import get_settings
from app.routes.health import router as health_router
from app.routes.runs import router as runs_router
from app.routes.workflows import router as workflows_router
from app.routes.artifacts import router as artifacts_router
from app.routes.backlog import router as backlog_router
from fastapi.staticfiles import StaticFiles
from app.routes.assessment_ui import router as assessment_ui_router

settings = get_settings()

app = FastAPI(
    title="AgentOps Readiness Console API",
    version="0.1.0",
    description="Governed multi-agent MCP workflow analysis backend.",
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
app.include_router(runs_router, prefix="/runs", tags=["runs"])
app.include_router(artifacts_router, prefix="/runs", tags=["artifacts"])
app.include_router(backlog_router, prefix="/runs", tags=["backlog"])
app.mount("/static", StaticFiles(directory="services/api/app/static"), name="static")
app.include_router(assessment_ui_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "environment": settings.app_env,
        "status": "ok",
    }