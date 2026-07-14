from typing import Any

from policy_core import (
    check_tool_permission as core_check_tool_permission,
    classify_data as core_classify_data,
    get_required_controls as core_get_required_controls,
)


def classify_data(data_element: str) -> dict[str, Any]:
    """
    Classify a data element according to the enterprise policy catalog.

    Returns sensitivity level, model-context allowance, redaction requirement,
    and rationale.
    """

    result = core_classify_data(data_element)
    return result.model_dump(mode="json")


def check_tool_permission(
    tool_name: str,
    agent_name: str,
    approval_granted: bool = False,
) -> dict[str, Any]:
    """
    Check whether an agent is allowed to use a specific tool.

    Write-capable tools may return require_approval unless approval has already
    been granted.
    """

    result = core_check_tool_permission(
        tool_name=tool_name,
        agent_name=agent_name,
        approval_granted=approval_granted,
    )

    return result.model_dump(mode="json")


def get_required_controls(workflow_step: str) -> dict[str, Any]:
    """
    Return required controls for a workflow step or governed action.
    """

    result = core_get_required_controls(workflow_step)
    return result.model_dump(mode="json")


def register_policy_tools(mcp: Any) -> None:
    """
    Register policy tools with a FastMCP server instance.

    Keeping registration separate from implementation lets us test the tool
    functions directly without starting an MCP server.
    """

    mcp.tool()(classify_data)
    mcp.tool()(check_tool_permission)
    mcp.tool()(get_required_controls)