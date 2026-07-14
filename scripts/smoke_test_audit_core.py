from audit_core import (
    AuditEventType,
    clear_audit_events,
    get_audit_events_for_run,
    log_audit_event,
)


def main() -> None:
    clear_audit_events()

    run_id = "run_test_001"

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.run_started,
        actor="system",
        details={"workflow_id": "payment_reconciliation"},
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.tool_called,
        actor="workflow_mapper",
        details={
            "tool_name": "document_server.read_document",
            "document_id": "process_narrative",
        },
    )

    events = get_audit_events_for_run(run_id)

    print(f"Events for {run_id}: {len(events)}")

    for event in events:
        print(
            f"- {event.event_type.value} actor={event.actor} "
            f"details={event.details}"
        )


if __name__ == "__main__":
    main()