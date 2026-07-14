# Policy MCP Server

## Purpose

The Policy MCP Server exposes enterprise governance decisions to agents through controlled read-only MCP tools.

It represents the policy decision boundary for agentic workflow analysis.

## Tools

### classify_data

Classifies a data element by sensitivity level and model-context handling rules.

### check_tool_permission

Determines whether an agent may use a specific tool and whether human approval is required.

### get_required_controls

Returns required controls for a workflow step or governed action.

## Security Boundary

Agents do not decide their own permissions.

The Policy MCP Server exposes policy decisions from `policy_core`. The agent may request a policy check, but it cannot override the result.

## Enterprise Interpretation

In a production enterprise system, this policy layer could be backed by:

- policy-as-code
- centralized governance catalog
- security-approved data classification rules
- RBAC / ABAC rules
- compliance controls
- approval workflow state

The MCP server should remain an adapter. Policy logic should remain in reusable policy-domain code or an approved policy service.