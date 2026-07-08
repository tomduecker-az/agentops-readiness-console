# Architecture Overview

## System Summary

AgentOps Readiness Console uses a multi-agent architecture coordinated by a central orchestrator. Specialist agents perform focused analysis using scoped MCP server access.

The system separates:

- reasoning
- tool access
- policy enforcement
- human approval
- write execution
- audit logging

## High-Level Architecture

```text
Next.js Web UI
    |
    v
FastAPI Backend
    |
    v
Agent Orchestrator
    |
    +--> Coordinator Agent
            |
            +--> Workflow Mapper Agent
            +--> Data Sensitivity Agent
            +--> Risk / Control Agent
            +--> HITL Designer Agent
            +--> Implementation Planner Agent
            +--> Tool / Policy Guardian
                    |
                    v
              Scoped MCP Servers
                    |
                    +--> Document MCP Server      read-only
                    +--> Policy MCP Server        read-only
                    +--> Audit MCP Server         append-only
                    +--> Project Mgmt MCP Server  write-gated
```

## Core Design Principle

The model may recommend actions, but the application controls execution authority.

Read-only analysis can run autonomously. Write actions require explicit human approval.

## Enterprise Interpretation

This architecture separates decision support from execution authority.

Specialist agents are responsible for focused analysis. MCP servers expose controlled tools and resources. The policy layer determines whether a proposed action is allowed. Human approval is required before any privileged write action is executed.

This prevents the system from becoming an uncontrolled autonomous agent with broad access to enterprise systems.