# Project Management MCP Server

## Purpose

The Project Management MCP Server exposes controlled write actions for implementation planning.

The first supported write action is GitHub issue creation.

## Tools

### create_issue

Creates a GitHub issue after human approval.

By default, the tool runs in dry-run mode so the write path can be tested safely.

## Security Boundary

This server is write-capable.

Issue creation requires:

- human approval
- an approval reference
- policy permission for `project_mgmt_server.create_issue`
- audit logging by the calling orchestration layer

## Enterprise Interpretation

In production, this server would integrate with an enterprise project-management system such as Jira, Azure DevOps, ServiceNow, or GitHub Enterprise.

The server should remain a write-action adapter. Approval, audit, and policy enforcement should occur before execution and also be defensively validated by the write tool.