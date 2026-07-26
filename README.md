# AgentOps Readiness Console

A governed workflow-readiness console for evaluating whether business processes are ready for safe AI or agentic automation.

## Purpose

AgentOps Readiness Console analyzes a business workflow, identifies risk and control requirements, designs human-in-the-loop approval patterns, and creates implementation backlog items for governed automation.

The system demonstrates an enterprise control pattern:

```text
Agent recommends
Human approves
Policy checks
Tool executes
Audit records
```

The goal is not to automate workflows blindly. The goal is to determine where AI can safely assist, what controls must exist first, and which actions require human approval before execution.

## What This Project Demonstrates

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

## Current MVP State

This MVP is intentionally local-first and deterministic.

Current implementation includes:

- workflow packet ingestion
- deterministic specialist agent modules
- policy-mediated tool access
- MCP server contracts and local gateway adapters
- data sensitivity classification
- risk/control analysis
- HITL design
- implementation backlog generation
- approval-gated GitHub issue creation
- audit event generation
- checked-in example outputs for multiple workflows

Current intentional limitations:

- artifacts and audit events are stored in memory
- specialist agents currently use deterministic logic rather than LLM-backed reasoning
- the API uses local gateway adapters instead of full MCP client transport
- workflow runs execute synchronously
- no production database is included yet

These deviations are documented in:

```text
docs/enterprise_deviations.md
```

## MVP Outputs

1. Workflow map
2. Data sensitivity report
3. Risk/control matrix
4. Human-in-the-loop design
5. Implementation backlog
6. Approval-gated project-management write action
7. Audit trail

## Example Outputs

Example generated outputs are available under:

```text
examples/payment_reconciliation_outputs/
examples/customer_onboarding_outputs/
```

These files show the artifacts and audit trail produced by two workflow examples:

- payment reconciliation / exception handling
- SaaS customer onboarding

A human-readable comparison of the checked-in workflow examples is available at:

```text
examples/README.md
```

To regenerate the payment reconciliation outputs locally:

```bash
source services/api/.venv/bin/activate
PYTHONPATH=services/api python -m scripts.export_example_outputs --workflow-id payment_reconciliation --output-dir examples/payment_reconciliation_outputs
```

To regenerate the customer onboarding outputs locally:

```bash
source services/api/.venv/bin/activate
PYTHONPATH=services/api python -m scripts.export_example_outputs --workflow-id customer_onboarding --output-dir examples/customer_onboarding_outputs
```

To validate the checked-in example outputs:

```bash
PYTHONPATH=services/api python -m scripts.validate_example_outputs
```

The validation checks confirm that exported artifacts include audit evidence, dry-run approval behavior, and workflow-specific output for the customer onboarding example.

## Architecture Themes

- Governed workflow analysis
- Multi-agent orchestration pattern
- MCP-oriented tool boundaries
- Scoped agent permissions
- Human approval before write actions
- Policy checks before tool execution
- Audit event generation
- Data sensitivity classification
- Enterprise workflow transformation

## Demo Workflows

### Payment Reconciliation

The initial workflow is an anonymized payment reconciliation / exception-handling process.

It demonstrates risk/control analysis for finance and operations workflows involving source-system checks, approval requirements, status updates, and audit needs.

### Customer Onboarding

The second workflow is a SaaS customer onboarding process.

It demonstrates generalization beyond the original finance workflow and includes onboarding-specific risks such as:

- customer-facing commitments
- implementation scope changes
- sensitive integrations
- missing intake / handoff information
- compressed launch timelines

No real confidential, customer, account, payment, agency, employer, or production data is included.

## Repository Structure

```text
apps/
  web/                         Frontend placeholder

services/
  api/                         FastAPI backend and agent orchestration

mcp_servers/
  document_server/             Read-only workflow document access
  policy_server/               Read-only policy and governance checks
  audit_server/                Append-only audit tool boundary
  project_mgmt_server/         Approval-gated GitHub issue creation

packages/
  workflow_core/               Workflow registry and document logic
  policy_core/                 Data classification, controls, and tool permissions
  audit_core/                  Audit event models and store
  project_mgmt_core/           GitHub issue creation logic

data/
  workflows/                   Workflow packets used for analysis
  workflow_packet_template/    Template for adding new workflow packets

examples/
  payment_reconciliation_outputs/
  customer_onboarding_outputs/
  README.md                    Human-readable comparison of example outputs

docs/
  Architecture, security, MCP contracts, workflow packet, and enterprise design notes

scripts/
  Smoke tests, export scripts, and validation utilities
```

## Key Documentation

```text
docs/project_charter.md
docs/architecture.md
docs/agent_design.md
docs/security_model.md
docs/mcp_contracts.md
docs/enterprise_deviations.md
docs/workflow_packet_format.md
docs/local_test_plan.md
docs/governed_execution_flow.md
docs/github_write_action_test.md
```

## Local Setup

From the repository root:

```bash
cd ~/projects/agentops-readiness-console
source services/api/.venv/bin/activate
```

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

## API Flow

Use the Swagger UI or API client to run:

```text
GET /workflows
POST /runs
GET /runs/{run_id}/artifacts
GET /runs/{run_id}/audit
POST /runs/{run_id}/backlog/{backlog_id}/approve
```

## End-to-End Smoke Test

From the repository root:

```bash
source services/api/.venv/bin/activate
PYTHONPATH=services/api python -m scripts.smoke_test_full_governed_flow
```

Expected result:

```text
PASS: Full governed workflow flow completed successfully.
```

## Example Output Validation

From the repository root:

```bash
source services/api/.venv/bin/activate
PYTHONPATH=services/api python -m scripts.validate_example_outputs
```

Expected result:

```text
PASS: Example outputs validated successfully.
```

## Try It With Your Own Workflow

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

For detailed packet instructions, see:

```text
docs/workflow_packet_format.md
docs/local_test_plan.md
```

## Real GitHub Write-Action Test

The project includes an approval-gated GitHub issue creation flow.

The first real write-action test created GitHub issue #1 after:

```text
backlog item generated
human approval recorded
policy check completed
GitHub issue created
audit event recorded
artifact updated
```

Details are documented in:

```text
docs/github_write_action_test.md
```

## Enterprise Interpretation

This MVP is not a production enterprise system. It is a portfolio implementation of the core control pattern required for safe AI workflow automation:

```text
separate analysis from execution
classify sensitive data before model use
scope agent permissions
require human approval for write actions
check policy before tool execution
record audit evidence
make implementation recommendations traceable
```

A production version would add:

- durable database storage
- persistent run history
- production-grade audit logging
- RBAC / SSO
- LLM-backed reasoning behind schema validation
- prompt injection and tool misuse testing
- background job execution
- full MCP client transport
- enterprise policy-as-code integration
- deployment, monitoring, and incident response controls