# AgentOps Readiness Console

A governed multi-agent MCP application for enterprise workflow analysis.

## Purpose

AgentOps Readiness Console analyzes an enterprise workflow, identifies risk and control requirements, designs human-in-the-loop approval patterns, and creates implementation backlog issues only after explicit human approval.

## MVP Outputs

1. Workflow map
2. Risk/control matrix
3. Human-in-the-loop design
4. Implementation backlog with approval-gated GitHub issue creation

## Architecture Themes

- Multi-agent orchestration
- MCP-based tool access
- Scoped agent permissions
- Human approval before write actions
- Durable audit logging
- Data governance
- Enterprise workflow transformation

## Initial Demo Workflow

The initial workflow is an anonymized payment reconciliation / exception-handling process.

No real confidential, customer, account, payment, agency, or employer data is included.

## Repository Structure

```text
apps/
  web/                    Next.js frontend

services/
  api/                    FastAPI backend and agent orchestration

mcp_servers/
  document_server/        Read-only workflow document access
  policy_server/          Read-only policy and governance checks
  audit_server/           Append-only audit logging
  project_mgmt_server/    Approval-gated GitHub issue creation

data/
  sample_workflow_packet/ Anonymized workflow data

docs/
  Architecture, security, MCP contracts, and enterprise design notes