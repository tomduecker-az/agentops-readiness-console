from typing import Any

from audit_core import AuditEventType
from policy_core import PolicyDecision, check_tool_permission
from workflow_core import (
    list_documents as core_list_documents,
    read_document as core_read_document,
    search_documents as core_search_documents,
)
from workflow_core.models import DocumentContent, DocumentSearchResult, WorkflowDocument

from app.services.audit_service import log_audit_event


class ToolAccessDeniedError(Exception):
    """Raised when a policy check blocks tool access."""


def _check_tool_access(
    run_id: str,
    agent_name: str,
    tool_name: str,
    approval_granted: bool = False,
) -> None:
    decision = check_tool_permission(
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

        raise ToolAccessDeniedError(decision.rationale)


def _log_tool_call(
    run_id: str,
    agent_name: str,
    tool_name: str,
    details: dict[str, Any] | None = None,
) -> None:
    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.tool_called,
        actor=agent_name,
        details={
            "tool_name": tool_name,
            **(details or {}),
        },
    )


def list_documents(
    run_id: str,
    agent_name: str,
    workflow_id: str,
) -> list[WorkflowDocument]:
    tool_name = "document_server.list_documents"

    _check_tool_access(run_id, agent_name, tool_name)
    _log_tool_call(
        run_id,
        agent_name,
        tool_name,
        {"workflow_id": workflow_id},
    )

    return core_list_documents(workflow_id)


def read_document(
    run_id: str,
    agent_name: str,
    workflow_id: str,
    document_id: str,
) -> DocumentContent:
    tool_name = "document_server.read_document"

    _check_tool_access(run_id, agent_name, tool_name)
    _log_tool_call(
        run_id,
        agent_name,
        tool_name,
        {
            "workflow_id": workflow_id,
            "document_id": document_id,
        },
    )

    return core_read_document(workflow_id, document_id)


def search_documents(
    run_id: str,
    agent_name: str,
    workflow_id: str,
    query: str,
) -> list[DocumentSearchResult]:
    tool_name = "document_server.search_documents"

    _check_tool_access(run_id, agent_name, tool_name)
    _log_tool_call(
        run_id,
        agent_name,
        tool_name,
        {
            "workflow_id": workflow_id,
            "query": query,
        },
    )

    return core_search_documents(workflow_id, query)