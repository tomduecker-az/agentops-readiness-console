# audit_core

Reusable audit event logic for AgentOps Readiness Console.

## Purpose

This package owns shared audit-domain logic used by API services, MCP servers, and future agent orchestration.

## Responsibilities

- audit event models
- audit event type definitions
- audit event creation
- in-memory audit store for MVP
- future storage abstraction for durable audit logging

## Enterprise Boundary

This package is intentionally independent from FastAPI and MCP.

FastAPI routes and MCP tools should act as adapters over this package instead of duplicating audit event definitions or logging behavior.

## Enterprise Deviation

The MVP uses an in-memory audit store. A production enterprise system would persist audit records to an append-only durable store such as Postgres/Supabase.