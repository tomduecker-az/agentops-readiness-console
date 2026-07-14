# workflow_core

Reusable workflow registry and document access logic for AgentOps Readiness Console.

## Purpose

This package owns shared workflow-domain logic used by the FastAPI backend and MCP servers.

## Responsibilities

- registered workflow lookup
- workflow packet validation
- workflow document metadata
- safe document path resolution
- read-only document access
- keyword document search
- shared workflow exceptions

## Enterprise Boundary

This package is intentionally independent from FastAPI and MCP.

FastAPI routes and MCP tools should act as adapters over this package instead of duplicating workflow registry or document access logic.