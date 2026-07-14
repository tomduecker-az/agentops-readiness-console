from policy_core.catalog import TOOL_PERMISSION_CATALOG
from policy_core.exceptions import UnknownToolError
from policy_core.models import PolicyDecision, ToolPermissionResult


def check_tool_permission(
    tool_name: str,
    agent_name: str,
    approval_granted: bool = False,
) -> ToolPermissionResult:
    normalized_tool = tool_name.strip()
    normalized_agent = agent_name.strip()

    policy = TOOL_PERMISSION_CATALOG.get(normalized_tool)

    if policy is None:
        raise UnknownToolError(f"Tool '{tool_name}' is not defined in the tool catalog.")

    allowed_agents = policy["allowed_agents"]
    requires_human_approval = bool(policy["requires_human_approval"])

    if normalized_agent not in allowed_agents:
        return ToolPermissionResult(
            tool_name=normalized_tool,
            agent_name=normalized_agent,
            access_level=policy["access_level"],
            decision=PolicyDecision.block,
            requires_human_approval=requires_human_approval,
            rationale=(
                f"Agent '{normalized_agent}' is not allowed to use tool "
                f"'{normalized_tool}'."
            ),
        )

    if requires_human_approval and not approval_granted:
        return ToolPermissionResult(
            tool_name=normalized_tool,
            agent_name=normalized_agent,
            access_level=policy["access_level"],
            decision=PolicyDecision.require_approval,
            requires_human_approval=True,
            rationale=(
                f"Tool '{normalized_tool}' is write-capable and requires human approval."
            ),
        )

    return ToolPermissionResult(
        tool_name=normalized_tool,
        agent_name=normalized_agent,
        access_level=policy["access_level"],
        decision=PolicyDecision.allow,
        requires_human_approval=requires_human_approval,
        rationale=str(policy["rationale"]),
    )