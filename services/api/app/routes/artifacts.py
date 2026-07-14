from fastapi import APIRouter

from app.schemas.artifacts import AnalysisArtifact
from app.services.artifact_service import get_artifacts_for_run

router = APIRouter()


@router.get("/{run_id}/artifacts", response_model=list[AnalysisArtifact])
async def get_run_artifacts(run_id: str) -> list[AnalysisArtifact]:
    return get_artifacts_for_run(run_id)