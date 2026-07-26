from uuid import uuid4

from app.schemas.artifacts import AnalysisArtifact, ArtifactStatus, ArtifactType
from app.storage.supabase_store import (
    get_artifact_for_run_by_type_from_db,
    get_artifacts_for_run_from_db,
    save_artifact,
    update_artifact_content_in_db,
)


def create_artifact(
    run_id: str,
    artifact_type: ArtifactType,
    content: dict,
    status: ArtifactStatus = ArtifactStatus.ready_for_review,
) -> AnalysisArtifact:
    artifact = AnalysisArtifact(
        artifact_id=f"artifact_{uuid4().hex}",
        run_id=run_id,
        artifact_type=artifact_type,
        status=status,
        content=content,
    )

    return save_artifact(artifact)


def get_artifacts_for_run(run_id: str) -> list[AnalysisArtifact]:
    return get_artifacts_for_run_from_db(run_id)


def get_artifact_for_run_by_type(
    run_id: str,
    artifact_type: ArtifactType,
) -> AnalysisArtifact | None:
    return get_artifact_for_run_by_type_from_db(
        run_id=run_id,
        artifact_type=artifact_type,
    )


def update_artifact_content(
    artifact_id: str,
    content: dict,
    status: ArtifactStatus | None = None,
) -> AnalysisArtifact:
    return update_artifact_content_in_db(
        artifact_id=artifact_id,
        content=content,
        status=status,
    )


def clear_artifacts() -> None:
    """
    Kept for backwards compatibility with older scripts.

    Supabase-backed storage is persistent, so this intentionally does not delete
    shared database rows.
    """
    return None