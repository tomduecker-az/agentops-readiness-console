# Payment Reconciliation Example Outputs

This folder contains example output from the AgentOps Readiness Console using the demo workflow:

```text
payment_reconciliation
```

The example run generated the full governed analysis chain and approved one backlog item in dry-run mode.

## Run

```text
run_11bb34d8f12b49479f4923ae552a9642
```

## Artifacts

The run generated:

- `workflow_map`
- `data_sensitivity_report`
- `risk_control_matrix`
- `hitl_design`
- `implementation_backlog`

## Approval-Gated Write Action

The example approved this backlog item:

```text
BACKLOG-DATA-001
```

The approval was executed in dry-run mode, so no real GitHub issue was created by this export script.

## Audit Trail

The run produced:

```text
88 audit events
```

See:

```text
audit_events.json
audit_summary.json
```

## What This Demonstrates

This example demonstrates the core governed flow:

```text
Workflow packet
  → specialist analysis artifacts
  → implementation backlog
  → human approval
  → policy-checked write action
  → audit evidence
```
