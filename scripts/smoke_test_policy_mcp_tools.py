from mcp_servers.policy_server.app.tools import (
    check_tool_permission,
    classify_data,
    get_required_controls,
)


def main() -> None:
    print("\nClassify data:")
    for data_element in ["payment_amount", "customer_identifier", "notes"]:
        result = classify_data(data_element)
        print(
            f"- {result['data_element']}: {result['sensitivity']} "
            f"allowed={result['allowed_in_model_context']} "
            f"redact={result['requires_redaction']}"
        )

    print("\nCheck tool permissions:")
    checks = [
        ("document_server.read_document", "workflow_mapper", False),
        ("project_mgmt_server.create_issue", "implementation_planner", False),
        ("project_mgmt_server.create_issue", "implementation_planner", True),
        ("project_mgmt_server.create_issue", "workflow_mapper", True),
    ]

    for tool_name, agent_name, approval_granted in checks:
        result = check_tool_permission(
            tool_name=tool_name,
            agent_name=agent_name,
            approval_granted=approval_granted,
        )
        print(
            f"- {agent_name} -> {tool_name}: {result['decision']} "
            f"approval_required={result['requires_human_approval']}"
        )

    print("\nRequired controls:")
    result = get_required_controls("implementation_backlog_write")
    for control in result["controls"]:
        print(f"- {control['control_id']}: {control['name']}")


if __name__ == "__main__":
    main()