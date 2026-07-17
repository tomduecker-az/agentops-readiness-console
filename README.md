# AgentOps Readiness Console

A governed multi-agent MCP application for enterprise workflow analysis.

## Purpose

AgentOps Readiness Console analyzes an enterprise workflow, identifies risk and control requirements, designs human-in-the-loop approval patterns, and creates implementation backlog issues only after explicit human approval.

## What This Project Demonstrates

AgentOps Readiness Console demonstrates a governed approach to evaluating business workflows before applying AI or agentic automation.

The system takes a workflow packet and produces:

```text
workflow_map
data_sensitivity_report
risk_control_matrix
hitl_design
implementation_backlog
```

It then supports an approval-gated write action:

```text
implementation backlog item
  ↓
human approval
  ↓
policy check
  ↓
project-management issue creation
  ↓
audit trail
```

The first successful real write-action test created GitHub issue #1 from an approved backlog item.

See:

```text
docs/governed_execution_flow.md
docs/github_write_action_test.md
docs/workflow_packet_format.md
docs/local_test_plan.md
```

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

  ## Try It With Your Own Workflow

  ## End-to-End Smoke Test

  To verify the full governed workflow locally:

  ```bash
  source services/api/.venv/bin/activate
  PYTHONPATH=services/api python -m scripts.smoke_test_full_governed_flow

This project supports custom workflow packets for local testing.

A workflow packet lives under:

```text
data/workflows/<workflow_id>/
```

Each packet includes:

```text
workflow_manifest.json
process_narrative.md
current_workflow_steps.md
policy_and_controls.md
sample_records.csv
```

To create a new workflow packet:

```bash
cp -r data/workflow_packet_template data/workflows/my_test_workflow
mv data/workflows/my_test_workflow/workflow_manifest.example.json data/workflows/my_test_workflow/workflow_manifest.json
```

Edit the manifest:

```json
{
  "workflow_id": "my_test_workflow",
  "display_name": "My Test Workflow",
  "packet_path": "data/workflows/my_test_workflow"
}
```

Then edit the narrative, workflow steps, policy notes, and sample records.

Start the API:

```bash
cd services/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000/docs
```

Run:

```text
GET /workflows
POST /runs
GET /runs/{run_id}/artifacts
GET /runs/{run_id}/audit
```

For detailed packet instructions, see:

```text
docs/workflow_packet_format.md
docs/local_test_plan.md
```