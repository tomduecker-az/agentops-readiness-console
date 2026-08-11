from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_local_artifacts(artifacts_dir: str | Path) -> list[dict[str, Any]]:
    directory = Path(artifacts_dir)

    if not directory.exists():
        raise FileNotFoundError(f"Artifacts directory does not exist: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Artifacts path is not a directory: {directory}")

    artifacts: list[dict[str, Any]] = []

    for path in sorted(directory.glob("*.json")):
        artifact_type = path.stem
        payload = json.loads(path.read_text(encoding="utf-8"))

        if _looks_like_artifact_wrapper(payload):
            artifacts.append(payload)
        else:
            artifacts.append(
                {
                    "artifact_id": f"local_{artifact_type}",
                    "artifact_type": artifact_type,
                    "status": "local",
                    "content": payload,
                    "metadata": {
                        "source": "local_artifacts_dir",
                        "path": str(path),
                    },
                }
            )

    return artifacts


def get_local_artifact_by_type(
    *,
    artifacts: list[dict[str, Any]],
    artifact_type: str,
) -> dict[str, Any] | None:
    for artifact in artifacts:
        if artifact.get("artifact_type") == artifact_type:
            return artifact

    return None


def get_local_artifact_content_by_type(
    *,
    artifacts: list[dict[str, Any]],
    artifact_type: str,
) -> dict[str, Any] | None:
    artifact = get_local_artifact_by_type(
        artifacts=artifacts,
        artifact_type=artifact_type,
    )

    if not artifact:
        return None

    content = artifact.get("content")

    return content if isinstance(content, dict) else None


def write_local_artifact(
    *,
    artifacts_dir: str | Path,
    artifact_type: str,
    content: dict[str, Any],
    wrap: bool = False,
) -> Path:
    directory = Path(artifacts_dir)
    directory.mkdir(parents=True, exist_ok=True)

    output_path = directory / f"{artifact_type}.json"

    payload: dict[str, Any]

    if wrap:
        payload = {
            "artifact_id": f"local_{artifact_type}",
            "artifact_type": artifact_type,
            "status": "local",
            "content": content,
            "metadata": {
                "source": "local_artifacts_dir",
            },
        }
    else:
        payload = content

    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return output_path


def _looks_like_artifact_wrapper(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("artifact_type"), str)
        and "content" in payload
    )