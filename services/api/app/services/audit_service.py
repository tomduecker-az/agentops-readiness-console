from audit_core.models import AuditEvent, AuditEventType

from app.storage.supabase_store import (
    get_audit_events_for_run_from_db,
    log_audit_event_to_db,
)


def log_audit_event(
    run_id: str,
    event_type: AuditEventType | str,
    actor: str,
    details: dict | None = None,
) -> AuditEvent:
    return log_audit_event_to_db(
        run_id=run_id,
        event_type=event_type,
        actor=actor,
        details=details,
    )


def get_audit_events_for_run(run_id: str) -> list[AuditEvent]:
    return get_audit_events_for_run_from_db(run_id)


def clear_audit_events() -> None:
    """
    Kept for backwards compatibility with older scripts.

    Supabase-backed storage is persistent, so this intentionally does not delete
    shared database rows.
    """
    return None