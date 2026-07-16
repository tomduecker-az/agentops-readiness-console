from uuid import uuid4

from app.schemas.artifacts import AnalysisArtifact, ArtifactStatus, ArtifactType


_ARTIFACTS: list[AnalysisArtifact] = []


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

    _ARTIFACTS.append(artifact)

    return artifact


def get_artifacts_for_run(run_id: str) -> list[AnalysisArtifact]:
    return [artifact for artifact in _ARTIFACTS if artifact.run_id == run_id]


def get_artifact_for_run_by_type(
    run_id: str,
    artifact_type: ArtifactType,
) -> AnalysisArtifact | None:
    for artifact in _ARTIFACTS:
        if artifact.run_id == run_id and artifact.artifact_type == artifact_type:
            return artifact

    return None


def update_artifact_content(
    artifact_id: str,
    content: dict,
    status: ArtifactStatus | None = None,
) -> AnalysisArtifact:
    for artifact in _ARTIFACTS:
        if artifact.artifact_id == artifact_id:
            artifact.content = content

            if status is not None:
                artifact.status = status

            return artifact

    raise ValueError(f"Artifact '{artifact_id}' was not found.")


def clear_artifacts() -> None:
    _ARTIFACTS.clear()