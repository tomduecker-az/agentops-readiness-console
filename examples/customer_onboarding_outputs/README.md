# customer_onboarding Example Outputs

This folder contains example output from the AgentOps Readiness Console.

## Workflow

```text
customer_onboarding
```

## Run

```text
run_6a91439e1c75426b830c1422589db38a
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
130 audit events
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
