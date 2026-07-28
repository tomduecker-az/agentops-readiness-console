from __future__ import annotations
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4
import httpx
from audit_core.models import AuditEvent, AuditEventType
from app.core.config import get_settings
from app.schemas.artifacts import AnalysisArtifact, ArtifactStatus, ArtifactType
import atexit

_HTTP_CLIENT: httpx.Client | None = None


def _get_http_client() -> httpx.Client:
    global _HTTP_CLIENT

    if _HTTP_CLIENT is None:
        _HTTP_CLIENT = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
            ),
        )

    return _HTTP_CLIENT


@atexit.register
def _close_http_client() -> None:
    global _HTTP_CLIENT

    if _HTTP_CLIENT is not None:
        _HTTP_CLIENT.close()
        _HTTP_CLIENT = None

class SupabaseStorageError(RuntimeError):
    pass


def create_workflow_run_record(
    run_id: str,
    workflow_id: str,
    status: str,
    message: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    now = _now_iso()

    _request(
        method="POST",
        path="/workflow_runs",
        json_body={
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": status,
            "message": message,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        },
    )


def update_workflow_run_record(
    run_id: str,
    status: str,
    message: str,
    completed: bool = False,
) -> None:
    now = _now_iso()

    payload: dict[str, Any] = {
        "status": status,
        "message": message,
        "updated_at": now,
    }

    if completed:
        payload["completed_at"] = now

    _request(
        method="PATCH",
        path="/workflow_runs",
        query={"run_id": f"eq.{run_id}"},
        json_body=payload,
    )


def get_workflow_run_record(run_id: str) -> dict[str, Any] | None:
    rows = _request(
        method="GET",
        path="/workflow_runs",
        query={
            "run_id": f"eq.{run_id}",
            "select": "*",
            "limit": "1",
        },
    )

    if not rows:
        return None

    return rows[0]


def save_artifact(artifact: AnalysisArtifact) -> AnalysisArtifact:
    now = _now_iso()

    _request(
        method="POST",
        path="/analysis_artifacts",
        json_body={
            "artifact_id": artifact.artifact_id,
            "run_id": artifact.run_id,
            "artifact_type": artifact.artifact_type.value,
            "status": artifact.status.value,
            "content": artifact.content,
            "created_at": artifact.created_at.isoformat(),
            "updated_at": now,
        },
    )

    return artifact


def get_artifacts_for_run_from_db(run_id: str) -> list[AnalysisArtifact]:
    rows = _request(
        method="GET",
        path="/analysis_artifacts",
        query={
            "run_id": f"eq.{run_id}",
            "select": "*",
            "order": "created_at.asc",
        },
    )

    return [_row_to_artifact(row) for row in rows]


def get_artifact_for_run_by_type_from_db(
    run_id: str,
    artifact_type: ArtifactType,
) -> AnalysisArtifact | None:
    rows = _request(
        method="GET",
        path="/analysis_artifacts",
        query={
            "run_id": f"eq.{run_id}",
            "artifact_type": f"eq.{artifact_type.value}",
            "select": "*",
            "order": "created_at.desc",
            "limit": "1",
        },
    )

    if not rows:
        return None

    return _row_to_artifact(rows[0])


def update_artifact_content_in_db(
    artifact_id: str,
    content: dict[str, Any],
    status: ArtifactStatus | None = None,
) -> AnalysisArtifact:
    existing = _get_artifact_by_id(artifact_id)

    if existing is None:
        raise ValueError(f"Artifact '{artifact_id}' was not found.")

    payload: dict[str, Any] = {
        "content": content,
        "updated_at": _now_iso(),
    }

    if status is not None:
        payload["status"] = status.value

    _request(
        method="PATCH",
        path="/analysis_artifacts",
        query={"artifact_id": f"eq.{artifact_id}"},
        json_body=payload,
    )

    updated = _get_artifact_by_id(artifact_id)

    if updated is None:
        raise ValueError(f"Artifact '{artifact_id}' was not found after update.")

    return updated


def log_audit_event_to_db(
    run_id: str,
    event_type: AuditEventType | str,
    actor: str,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_id=f"audit_{uuid4().hex}",
        run_id=run_id,
        event_type=AuditEventType(event_type),
        actor=actor,
        details=details or {},
    )

    _request(
        method="POST",
        path="/audit_events",
        json_body={
            "event_id": event.event_id,
            "run_id": event.run_id,
            "event_type": event.event_type.value,
            "actor": event.actor,
            "details": event.details,
            "created_at": event.created_at.isoformat(),
        },
    )

    return event


def get_audit_events_for_run_from_db(run_id: str) -> list[AuditEvent]:
    rows = _request(
        method="GET",
        path="/audit_events",
        query={
            "run_id": f"eq.{run_id}",
            "select": "*",
            "order": "created_at.asc",
        },
    )

    return [_row_to_audit_event(row) for row in rows]


def _get_artifact_by_id(artifact_id: str) -> AnalysisArtifact | None:
    rows = _request(
        method="GET",
        path="/analysis_artifacts",
        query={
            "artifact_id": f"eq.{artifact_id}",
            "select": "*",
            "limit": "1",
        },
    )

    if not rows:
        return None

    return _row_to_artifact(rows[0])


def _row_to_artifact(row: dict[str, Any]) -> AnalysisArtifact:
    return AnalysisArtifact(
        artifact_id=row["artifact_id"],
        run_id=row["run_id"],
        artifact_type=ArtifactType(row["artifact_type"]),
        status=ArtifactStatus(row["status"]),
        content=row["content"],
        created_at=_parse_datetime(row["created_at"]),
    )


def _row_to_audit_event(row: dict[str, Any]) -> AuditEvent:
    return AuditEvent(
        event_id=row["event_id"],
        run_id=row["run_id"],
        event_type=AuditEventType(row["event_type"]),
        actor=row["actor"],
        details=row["details"],
        created_at=_parse_datetime(row["created_at"]),
    )


def _request(
    method: str,
    path: str,
    query: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> Any:
    settings = get_settings()

    if not settings.supabase_url:
        raise SupabaseStorageError("SUPABASE_URL is not configured.")

    if not settings.supabase_service_role_key:
        raise SupabaseStorageError("SUPABASE_SERVICE_ROLE_KEY is not configured.")

    base_url = settings.supabase_url.rstrip("/")
    url = f"{base_url}/rest/v1{path}"
    key = settings.supabase_service_role_key

    headers = {
        "apikey": key,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    # Legacy JWT-style service_role keys can also be sent as Bearer tokens.
    # New sb_secret_ keys are sent only through the apikey header.
    if key.count(".") == 2:
        headers["Authorization"] = f"Bearer {key}"

    try:
        client = _get_http_client()

        response = client.request(
            method=method,
            url=url,
            params=query,
            json=json_body,
            headers=headers,
        )

        response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        raise SupabaseStorageError(
            f"Supabase request failed: {exc.response.status_code} {exc.response.text}"
        ) from exc

    except httpx.HTTPError as exc:
        raise SupabaseStorageError(f"Supabase request failed: {exc}") from exc

    if response.text:
        return response.json()

    return None


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()