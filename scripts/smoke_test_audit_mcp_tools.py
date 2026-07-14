from audit_core import clear_audit_events
from mcp_servers.audit_server.app.tools import (
    get_run_audit_events,
    log_agent_step,
    log_approval,
    log_policy_check,
    log_policy_violation,
    log_tool_call,
    log_write_action,
)


def main() -> None:
    clear_audit_events()

    run_id = "run_test_audit_mcp"

    log_agent_step(
        run_id=run_id,
        agent_name="workflow_mapper",
        step_name="map_workflow",
        status="started",
        details={"workflow_id": "payment_reconciliation"},
    )

    log_tool_call(
        run_id=run_id,
        agent_name="workflow_mapper",
        tool_name="document_server.read_document",
        details={"document_id": "process_narrative"},
    )

    log_policy_check(
        run_id=run_id,
        actor="tool_policy_guardian",
        policy_name="document_read_access",
        decision="allow",
        details={"tool_name": "document_server.read_document"},
    )

    log_approval(
        run_id=run_id,
        actor="human_reviewer",
        approval_type="implementation_backlog_write",
        approved=True,
        details={"approved_items": 3},
    )

    log_write_action(
        run_id=run_id,
        actor="implementation_planner",
        action_name="project_mgmt_server.create_issue",
        success=True,
        details={"created_issue_count": 3},
    )

    log_policy_violation(
        run_id=run_id,
        actor="workflow_mapper",
        violation_type="unauthorized_write_attempt",
        details={"tool_name": "project_mgmt_server.create_issue"},
    )

    events = get_run_audit_events(run_id)

    print(f"Audit events for {run_id}: {len(events)}")

    for event in events:
        print(
            f"- {event['event_type']} actor={event['actor']} "
            f"details={event['details']}"
        )


if __name__ == "__main__":
    main()