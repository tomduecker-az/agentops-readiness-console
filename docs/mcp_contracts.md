# MCP Server Contracts

## Purpose

This document defines the planned MCP server boundaries and tool contracts.

MCP servers expose controlled tools and resources to agents. Each server has a clear responsibility and access level.

## Document MCP Server

### Access Level

Read-only.

### Purpose

Provides controlled access to workflow documents, SOPs, sample records, and policy notes.

### Planned Tools

- list_documents
- read_document
- search_documents

### Enterprise Boundary

This server should not expose write actions. It is a source of context, not an execution system.

## Policy MCP Server

### Access Level

Read-only.

### Purpose

Centralizes governance rules, data classification rules, tool permission rules, and approval requirements.

### Planned Tools

- classify_data
- check_policy
- check_tool_permission
- get_required_controls

### Enterprise Boundary

Policy checks must be treated as enforcement inputs. Agents can request a policy check, but they cannot override the result.

## Audit MCP Server

### Access Level

Append-only.

### Purpose

Creates a durable audit trail of agent behavior and system decisions.

### Planned Tools

- log_agent_step
- log_tool_call
- log_approval
- log_policy_violation
- log_write_action

### Enterprise Boundary

Audit records should not be editable by agents. The MVP may use a simplified local implementation, but the architecture treats audit logging as append-only.

## Project Management MCP Server

### Access Level

Write-gated.

### Purpose

Creates real GitHub issues from approved backlog items.

### Planned Tools

- propose_issue
- create_issue_after_approval

### Enterprise Boundary

The project-management MCP server is the only MVP server with a write-capable action.

Write access requires:

- approved backlog item
- approval record
- policy check
- scoped GitHub token
- audit log entry

## Tool Access Summary

| MCP Server | Access Level | Write Capable | Approval Required |
|---|---:|---:|---:|
| Document MCP Server | Read-only | No | No |
| Policy MCP Server | Read-only | No | No |
| Audit MCP Server | Append-only | Yes, append only | No |
| Project Management MCP Server | Write-gated | Yes | Yes |

## Enterprise Principle

MCP tools are integration boundaries.

Each tool should have an explicit purpose, permission level, expected input, expected output, and audit requirement.