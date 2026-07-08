from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.runs import router as runs_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title="AgentOps Readiness Console API",
    version="0.1.0",
    description="Governed multi-agent MCP workflow analysis backend.",
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(runs_router, prefix="/runs", tags=["runs"])


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "environment": settings.app_env,
        "status": "ok",
    }