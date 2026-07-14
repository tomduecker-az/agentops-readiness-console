# Audit MCP Server

## Purpose

The Audit MCP Server exposes controlled audit logging tools for agentic workflow analysis.

It represents the traceability boundary for the system.

## Tools

### log_agent_step

Logs high-level agent lifecycle events.

### log_tool_call

Logs agent tool calls or tool requests.

### log_policy_check

Logs policy checks and decisions.

### log_approval

Logs human approval or rejection decisions.

### log_policy_violation

Logs blocked or violating policy events.

### log_write_action

Logs write action success or failure.

### get_run_audit_events

Returns audit events for a workflow run.

## Security Boundary

Audit tools are append-oriented. Agents may add audit events, but they should not modify or delete prior audit records.

## Enterprise Interpretation

In a production enterprise system, audit records would be persisted to an append-only durable store such as Postgres/Supabase with identity, timestamps, retention rules, and tamper-resistance controls.

The MCP server should remain an adapter. Audit event definitions and logging behavior should remain in reusable audit-domain logic or an approved audit service.