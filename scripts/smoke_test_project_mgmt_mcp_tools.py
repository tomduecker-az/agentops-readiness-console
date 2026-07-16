from project_mgmt_core.exceptions import ApprovalRequiredError
from mcp_servers.project_mgmt_server.app.tools import create_issue


def main() -> None:
    print("\nBlocked write test:")
    try:
        create_issue(
            title="Blocked issue test",
            body="This should not be created because approval is missing.",
            labels=["agentops", "blocked"],
            approval_granted=False,
            approval_reference=None,
            dry_run=True,
        )
    except ApprovalRequiredError as exc:
        print(f"- blocked as expected: {exc}")

    print("\nApproved dry-run test:")
    result = create_issue(
        title="Dry-run issue test",
        body="This simulates a GitHub issue after approval.",
        labels=["agentops", "dry-run"],
        approval_granted=True,
        approval_reference="approval_test_001",
        dry_run=True,
    )

    print(f"- status: {result['status']}")
    print(f"- dry_run: {result['dry_run']}")
    print(f"- message: {result['message']}")


if __name__ == "__main__":
    main()