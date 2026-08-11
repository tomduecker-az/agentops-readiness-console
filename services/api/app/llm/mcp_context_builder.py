from __future__ import annotations
from typing import Any
from audit_core import AuditEventType
from app.mcp_clients.stdio_runtime import call_mcp_tool
from app.services.audit_service import log_audit_event
from app.llm.evidence_catalog import build_evidence_catalog


_AGENT_NAME = "mcp_llm_shadow_analyzer"


SEARCH_QUERIES = [
    "approval requirements security review provisioning human approval write actions",
    "SLA deadline escalation identity team lead weekly access review report",
    "audit evidence retention approvals provisioning rejected requests reviewer information",
    "missing unclear incomplete conflicting information clarification",
    "HR source verification employee identifier manager email role employment status",
]


DATA_ELEMENTS = [
    "employee_identifier",
    "employee_email",
    "manager_email",
    "employee_role",
    "employment_status",
    "requested_system",
    "access_level",
    "privileged_access_indicator",
    "business_justification",
    "approval_status",
    "ticket_status",
    "sla_due_date",
    "free_text_notes",
    "approval_evidence",
    "provisioning_records",
]


CONTROL_ACTIONS = [
    "AI-assisted intake review using access request and HR verification data",
    "application owner approval or rejection of requested access",
    "security review for privileged sensitive custom or security-related access",
    "provisioning approved access in identity provider and target systems",
    "updating ticket status approval evidence and provisioning evidence",
    "routing clarification requests or communications to the manager",
    "escalating requests approaching the SLA deadline",
    "preparing and distributing weekly access review reports",
    "creating or modifying workflow records or project issues",
    "model-context handling for employee access request data",
]


def build_mcp_retrieved_context(
    run_id: str,
    workflow_id: str,
    *,
    audit_enabled: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tool_trace: list[dict[str, Any]] = []

    documents = _call_governed_tool(
        run_id=run_id,
        policy_tool_name="document_server.list_documents",
        server="document",
        mcp_tool_name="list_documents",
        arguments={"workflow_id": workflow_id},
        tool_trace=tool_trace,
        audit_enabled=audit_enabled,
    )

    document_contents = []

    for document in documents:
        document_id = document["document_id"]

        document_contents.append(
            _call_governed_tool(
                run_id=run_id,
                policy_tool_name="document_server.read_document",
                server="document",
                mcp_tool_name="read_document",
                arguments={
                    "workflow_id": workflow_id,
                    "document_id": document_id,
                },
                tool_trace=tool_trace,
                audit_enabled=audit_enabled,
            )
        )

    search_results = []

    for query in SEARCH_QUERIES:
        search_results.append(
            {
                "query": query,
                "results": _call_governed_tool(
                    run_id=run_id,
                    policy_tool_name="document_server.search_documents",
                    server="document",
                    mcp_tool_name="search_documents",
                    arguments={
                        "workflow_id": workflow_id,
                        "query": query,
                    },
                    tool_trace=tool_trace,
                    audit_enabled=audit_enabled,
                ),
            }
        )

    data_classifications = _call_governed_tool(
        run_id=run_id,
        policy_tool_name="policy_server.classify_data_elements",
        server="policy",
        mcp_tool_name="classify_data_elements",
        arguments={"data_elements": DATA_ELEMENTS},
        tool_trace=tool_trace,
        audit_enabled=audit_enabled,
    )

    required_controls = _call_governed_tool(
        run_id=run_id,
        policy_tool_name="policy_server.get_required_controls_for_actions",
        server="policy",
        mcp_tool_name="get_required_controls_for_actions",
        arguments={"workflow_steps": CONTROL_ACTIONS},
        tool_trace=tool_trace,
        audit_enabled=audit_enabled,
    )
    evidence_catalog = build_evidence_catalog(
        workflow_id=workflow_id,
        document_contents=document_contents,
        search_results=search_results,
        data_classifications=data_classifications,
        required_controls=required_controls,
    )

    context = {
        "workflow_id": workflow_id,
        "retrieval_mode": "bounded_mcp_context",
        "documents": documents,
        "document_contents": document_contents,
        "targeted_search_results": search_results,
        "data_classifications": data_classifications,
        "required_controls": required_controls,
        "evidence_catalog": evidence_catalog,
        "retrieval_limits": {
            "document_list_calls": 1,
            "document_read_calls": len(document_contents),
            "search_calls": len(SEARCH_QUERIES),
            "batch_classification_calls": 1,
            "batch_required_control_calls": 1,
            "total_governed_tool_calls": len(tool_trace),
        },
    }

    return context, tool_trace


def _call_governed_tool(
    run_id: str,
    policy_tool_name: str,
    server: str,
    mcp_tool_name: str,
    arguments: dict[str, Any],
    tool_trace: list[dict[str, Any]],
    *,
    audit_enabled: bool = True,
) -> Any:
    permission = call_mcp_tool(
        server="policy",
        tool_name="check_tool_permission",
        arguments={
            "tool_name": policy_tool_name,
            "agent_name": _AGENT_NAME,
            "approval_granted": False,
        },
    )

    if audit_enabled:
        log_audit_event(
            run_id=run_id,
            event_type=AuditEventType.policy_checked,
            actor="tool_policy_guardian",
            details={
                "tool_name": policy_tool_name,
                "agent_name": _AGENT_NAME,
                "decision": permission.get("decision"),
                "requires_human_approval": permission.get("requires_human_approval"),
                "rationale": permission.get("rationale"),
                "analysis_mode": "mcp_llm_shadow_bounded",
            },
        )

    if not _is_allowed(permission):
        raise PermissionError(
            f"Policy denied {policy_tool_name} for {_AGENT_NAME}: {permission}"
        )

    result = call_mcp_tool(
        server=server,
        tool_name=mcp_tool_name,
        arguments=arguments,
    )

    safe_arguments = _safe_arguments(arguments)

    if audit_enabled:
        log_audit_event(
            run_id=run_id,
            event_type=AuditEventType.tool_called,
            actor=_AGENT_NAME,
            details={
                "tool_name": policy_tool_name,
                "mcp_tool_name": mcp_tool_name,
                "arguments": safe_arguments,
                "analysis_mode": "mcp_llm_shadow_bounded",
            },
        )

    tool_trace.append(
        {
            "tool_name": policy_tool_name,
            "mcp_tool_name": mcp_tool_name,
            "server": server,
            "status": "executed",
            "arguments": safe_arguments,
        }
    )

    return result


def _is_allowed(permission: dict[str, Any]) -> bool:
    decision = str(permission.get("decision", "")).lower()
    return decision == "allow" or decision.endswith(".allow")


def _safe_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    safe = dict(arguments)

    for key in ["content", "document_content", "text"]:
        if key in safe:
            safe[key] = "[redacted]"

    return safe