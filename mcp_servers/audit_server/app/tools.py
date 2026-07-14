from typing import Any

from audit_core import AuditEventType, get_audit_events_for_run, log_audit_event


def log_agent_step(
    run_id: str,
    agent_name: str,
    step_name: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Log a high-level agent step such as agent_started or agent_completed.
    """

    event_type = (
        AuditEventType.agent_completed
        if status == "completed"
        else AuditEventType.agent_started
    )

    event = log_audit_event(
        run_id=run_id,
        event_type=event_type,
        actor=agent_name,
        details={
            "step_name": step_name,
            "status": status,
            **(details or {}),
        },
    )

    return event.model_dump(mode="json")


def log_tool_call(
    run_id: str,
    agent_name: str,
    tool_name: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Log that an agent called or requested a tool.
    """

    event = log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.tool_called,
        actor=agent_name,
        details={
            "tool_name": tool_name,
            **(details or {}),
        },
    )

    return event.model_dump(mode="json")


def log_policy_check(
    run_id: str,
    actor: str,
    policy_name: str,
    decision: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Log a policy check and its decision.
    """

    event = log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.policy_checked,
        actor=actor,
        details={
            "policy_name": policy_name,
            "decision": decision,
            **(details or {}),
        },
    )

    return event.model_dump(mode="json")


def log_approval(
    run_id: str,
    actor: str,
    approval_type: str,
    approved: bool,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Log a human approval or rejection decision.
    """

    event = log_audit_event(
        run_id=run_id,
        event_type=(
            AuditEventType.approval_granted
            if approved
            else AuditEventType.approval_rejected
        ),
        actor=actor,
        details={
            "approval_type": approval_type,
            "approved": approved,
            **(details or {}),
        },
    )

    return event.model_dump(mode="json")


def log_policy_violation(
    run_id: str,
    actor: str,
    violation_type: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Log a blocked or violating policy event.
    """

    event = log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.policy_violation,
        actor=actor,
        details={
            "violation_type": violation_type,
            **(details or {}),
        },
    )

    return event.model_dump(mode="json")


def log_write_action(
    run_id: str,
    actor: str,
    action_name: str,
    success: bool,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Log a write action attempt or result.
    """

    event = log_audit_event(
        run_id=run_id,
        event_type=(
            AuditEventType.write_action_executed
            if success
            else AuditEventType.write_action_failed
        ),
        actor=actor,
        details={
            "action_name": action_name,
            "success": success,
            **(details or {}),
        },
    )

    return event.model_dump(mode="json")


def get_run_audit_events(run_id: str) -> list[dict[str, Any]]:
    """
    Return audit events for a workflow run.
    """

    events = get_audit_events_for_run(run_id)
    return [event.model_dump(mode="json") for event in events]


def register_audit_tools(mcp: Any) -> None:
    """
    Register audit tools with a FastMCP server instance.
    """

    mcp.tool()(log_agent_step)
    mcp.tool()(log_tool_call)
    mcp.tool()(log_policy_check)
    mcp.tool()(log_approval)
    mcp.tool()(log_policy_violation)
    mcp.tool()(log_write_action)
    mcp.tool()(get_run_audit_events)