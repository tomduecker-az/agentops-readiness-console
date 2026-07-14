from uuid import uuid4

from audit_core.models import AuditEvent, AuditEventType


_AUDIT_EVENTS: list[AuditEvent] = []


def log_audit_event(
    run_id: str,
    event_type: AuditEventType | str,
    actor: str,
    details: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_id=f"audit_{uuid4().hex}",
        run_id=run_id,
        event_type=AuditEventType(event_type),
        actor=actor,
        details=details or {},
    )

    _AUDIT_EVENTS.append(event)

    return event


def get_audit_events_for_run(run_id: str) -> list[AuditEvent]:
    return [event for event in _AUDIT_EVENTS if event.run_id == run_id]


def clear_audit_events() -> None:
    _AUDIT_EVENTS.clear()