# Agent Design

## Purpose

This document defines the agent responsibilities, boundaries, and allowed tool access for AgentOps Readiness Console.

The system is intentionally multi-agent. Each agent has a focused role, structured output contract, and scoped MCP access.

## Coordinator Agent

### Responsibility

The Coordinator Agent manages sequencing and routing. It does not perform deep analysis itself and does not execute write actions.

### Duties

- start a workflow analysis run
- route work to specialist agents
- pass structured context between agents
- verify required outputs are present
- request human approval before write actions
- assemble the final response for the UI

### Tool Access

- no direct project-management write access
- may read run state
- may write audit events through approved backend services

## Workflow Mapper Agent

### Responsibility

Creates a structured workflow map from the workflow packet.

### Duties

- identify process steps
- identify actors
- identify systems
- identify handoffs
- identify decision points
- identify bottlenecks
- identify candidate automation points

### Allowed MCP Access

- Document MCP Server: read-only
- Audit MCP Server: append-only

### Output

- workflow steps
- actors
- systems
- inputs and outputs
- decision points
- risks or failure points

## Data Sensitivity Agent

### Responsibility

Classifies the types of data used in the workflow and identifies data governance concerns.

### Duties

- identify sensitive data by workflow step
- classify data sensitivity
- identify PII, financial, customer, operational, or confidential data
- recommend redaction requirements
- flag data that should not be sent to an LLM

### Allowed MCP Access

- Document MCP Server: read-only
- Policy MCP Server: read-only
- Audit MCP Server: append-only

### Output

- data classes by workflow step
- sensitivity warnings
- recommended handling controls

## Risk / Control Agent

### Responsibility

Creates the risk/control matrix.

### Duties

- identify workflow risks
- assess likelihood and impact
- define required controls
- identify approval requirements
- map controls to workflow steps
- identify tool restrictions

### Allowed MCP Access

- Policy MCP Server: read-only
- Audit MCP Server: append-only

### Output

- risk/control matrix
- required control owner
- approval requirement
- tool restriction

## HITL Designer Agent

### Responsibility

Designs the human-in-the-loop model.

### Duties

- define autonomy levels
- identify which actions can be autonomous
- identify which actions require approval
- define escalation rules
- define fallback behavior
- define rejection handling

### Allowed MCP Access

- Policy MCP Server: read-only
- Audit MCP Server: append-only

### Output

- HITL design
- autonomy level by workflow step
- approval points
- fallback path

## Implementation Planner Agent

### Responsibility

Creates proposed implementation backlog items and executes approved issue creation.

### Duties

- generate backlog items
- define user stories
- define acceptance criteria
- map backlog items to workflow steps and controls
- prepare GitHub issue payloads
- wait for human approval
- create GitHub issues only after approval

### Allowed MCP Access Before Approval

- Audit MCP Server: append-only

### Allowed MCP Access After Approval

- Project Management MCP Server: write-gated issue creation

### Output

- proposed backlog items
- approved issue creation results
- GitHub issue references

## Tool / Policy Guardian

### Responsibility

The Tool / Policy Guardian is the internal governance layer that validates proposed tool use.

### Duties

- check agent permissions
- check tool permissions
- check whether a tool is read-only, append-only, or write-capable
- confirm approval state before write actions
- block unauthorized write actions
- log policy violations

### Allowed MCP Access

- Policy MCP Server: read-only
- Audit MCP Server: append-only

## Enterprise Principle

Agent boundaries are security boundaries.

Each agent should only receive the tools, context, and authority required for its specific job.