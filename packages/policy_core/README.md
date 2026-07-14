# policy_core

Reusable policy and governance logic for AgentOps Readiness Console.

## Purpose

This package owns shared policy-domain logic used by API services, MCP servers, and future agent orchestration.

## Responsibilities

- data classification
- tool permission checks
- approval requirement evaluation
- required control lookup
- autonomy-level guidance
- shared policy exceptions

## Enterprise Boundary

This package is intentionally independent from FastAPI and MCP.

FastAPI routes and MCP tools should act as adapters over this package instead of duplicating policy logic.