from audit_core import AuditEventType
from policy_core import (
    PolicyDecision,
    check_tool_permission as core_check_tool_permission,
    classify_data as core_classify_data,
)
from policy_core.models import DataClassificationResult

from app.services.audit_service import log_audit_event


class PolicyToolAccessDeniedError(Exception):
    """Raised when a policy tool access check blocks execution."""


def _check_tool_access(
    run_id: str,
    agent_name: str,
    tool_name: str,
    approval_granted: bool = False,
) -> None:
    decision = core_check_tool_permission(
        tool_name=tool_name,
        agent_name=agent_name,
        approval_granted=approval_granted,
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.policy_checked,
        actor="tool_policy_guardian",
        details={
            "tool_name": tool_name,
            "agent_name": agent_name,
            "decision": decision.decision.value,
            "requires_human_approval": decision.requires_human_approval,
            "rationale": decision.rationale,
        },
    )

    if decision.decision != PolicyDecision.allow:
        log_audit_event(
            run_id=run_id,
            event_type=AuditEventType.policy_violation,
            actor=agent_name,
            details={
                "tool_name": tool_name,
                "decision": decision.decision.value,
                "rationale": decision.rationale,
            },
        )

        raise PolicyToolAccessDeniedError(decision.rationale)


def classify_data(
    run_id: str,
    agent_name: str,
    data_element: str,
) -> DataClassificationResult:
    tool_name = "policy_server.classify_data"

    _check_tool_access(
        run_id=run_id,
        agent_name=agent_name,
        tool_name=tool_name,
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.tool_called,
        actor=agent_name,
        details={
            "tool_name": tool_name,
            "data_element": data_element,
        },
    )

    return core_classify_data(data_element)