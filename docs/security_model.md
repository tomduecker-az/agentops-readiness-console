# Security and Governance Model

## Purpose

This document defines the security and governance principles for AgentOps Readiness Console.

The application is designed to demonstrate how agentic AI can be introduced into enterprise workflows with controlled authority, auditable behavior, and human approval for privileged actions.

## Guiding Principles

1. Least privilege
2. Human approval before write actions
3. No secrets in source control
4. Scoped tool access by agent role
5. Durable audit logging
6. Explicit data classification
7. No live sensitive data in the demo corpus
8. Separation of reasoning authority from execution authority

## Read vs. Write Boundary

Read-only tools may be used autonomously by approved agents.

Write actions require:

- proposed action payload
- policy check
- human approval
- audit log entry
- execution by a scoped MCP server

## Human Approval Requirement

The MVP has one privileged write action:

- create GitHub issues from the proposed implementation backlog

This action must not execute until a human approves the proposed backlog.

## GitHub Issue Creation

The GitHub token must be:

- fine-grained
- scoped to one repository
- limited to Issues write permission
- stored only as an environment variable
- unavailable to the frontend

The browser must never receive the GitHub token.

## Secrets Management

Local development uses `.env` files.

Rules:

- `.env` must not be committed
- `.env.example` may be committed
- secrets must not appear in screenshots
- secrets must not be pasted into ChatGPT
- service tokens must stay backend-only

## Audit Requirements

The system should log:

- agent run started
- agent run completed
- MCP tool called
- policy check performed
- approval requested
- approval granted
- approval rejected
- write action executed
- write action failed
- policy violation detected

## Data Handling

The MVP uses anonymized and synthetic workflow data.

Rules:

- no real customer names
- no real account numbers
- no real payment IDs
- no confidential employer data
- no private agency data
- no live production system access

## Enterprise Principle

The model may produce recommendations, but the application owns enforcement.

Agentic AI should not be treated as a trusted actor with unrestricted system access.