# Local Test Plan

This guide verifies that the AgentOps Readiness Console can run a governed workflow analysis locally.

## 1. Start the API

From repo root:

```bash
cd services/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000/docs
```

## 2. List registered workflows

Call:

```text
GET /workflows
```

Expected:

```text
payment_reconciliation
```

## 3. Start a workflow run

Call:

```text
POST /runs
```

Body:

```json
{
  "workflow_id": "payment_reconciliation"
}
```

Expected:

```json
{
  "run_id": "run_...",
  "workflow_id": "payment_reconciliation",
  "status": "created"
}
```

Copy the returned `run_id`.

## 4. Review generated artifacts

Call:

```text
GET /runs/{run_id}/artifacts
```

Expected artifacts:

```text
workflow_map
data_sensitivity_report
risk_control_matrix
hitl_design
```

If the Implementation Planner Agent has been added, the response should also include:

```text
implementation_backlog
```

## 5. Review audit history

Call:

```text
GET /runs/{run_id}/audit
```

Expected event types include:

```text
run_started
agent_started
policy_checked
tool_called
agent_completed
run_completed
```

Expected actors include:

```text
coordinator
workflow_mapper
data_sensitivity_classifier
risk_control_designer
hitl_designer
tool_policy_guardian
system
```

## 6. Test with a custom workflow

Copy the template:

```bash
cp -r data/workflow_packet_template data/workflows/my_test_workflow
mv data/workflows/my_test_workflow/workflow_manifest.example.json data/workflows/my_test_workflow/workflow_manifest.json
```

Edit:

```text
data/workflows/my_test_workflow/workflow_manifest.json
data/workflows/my_test_workflow/process_narrative.md
data/workflows/my_test_workflow/current_workflow_steps.md
data/workflows/my_test_workflow/policy_and_controls.md
data/workflows/my_test_workflow/sample_records.csv
```

In the manifest, update:

```json
{
  "workflow_id": "my_test_workflow",
  "display_name": "My Test Workflow",
  "packet_path": "data/workflows/my_test_workflow"
}
```

Restart the API and call:

```text
GET /workflows
```

Expected:

```text
my_test_workflow
```

Then run:

```json
{
  "workflow_id": "my_test_workflow"
}
```

## Notes

Current MVP limitations:

- artifact storage is in-memory
- audit storage is in-memory
- workflow runs are synchronous
- agents are deterministic skeleton agents
- gateway adapters call shared core logic locally rather than using full MCP client transport