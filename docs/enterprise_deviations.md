# Enterprise Deviations

## Purpose

This project is built as an enterprise learning and portfolio system. Some production concerns are intentionally simplified.

Each deviation is documented so the portfolio can explain what was simplified and how an enterprise implementation would differ.

## Deviation 1: Single User

The MVP assumes one user/operator.

### Enterprise Version

A production enterprise system would include:

- SSO
- RBAC
- tenant isolation
- approval roles
- admin policy management
- identity-based audit logging

## Deviation 2: Sanitized Local Workflow Data

The MVP uses anonymized sample workflow data.

### Enterprise Version

A production enterprise system would require:

- approved data ingestion process
- data retention rules
- data loss prevention review
- privacy/security signoff
- access logging
- data classification before model use

## Deviation 3: Single Write Integration

The MVP writes only to GitHub Issues.

### Enterprise Version

A production enterprise system might integrate with:

- ServiceNow
- Jira
- Linear
- Asana
- Azure DevOps
- internal project-management systems

Those integrations would require formal approval, scoped OAuth, change-management review, and service ownership.

## Deviation 4: Simplified Policy Engine

The MVP starts with application-level policy checks.

### Enterprise Version

A production enterprise system would likely use:

- centralized policy engine
- policy-as-code
- formal approval workflow
- compliance reporting
- security review
- change-controlled policy updates

## Deviation 5: Local-First Development

The MVP runs locally first.

### Enterprise Version

A production enterprise system would include:

- dev, staging, and production environments
- CI/CD
- container scanning
- dependency scanning
- secret manager
- infrastructure-as-code
- logging and monitoring
- incident response procedures

## Deviation 6: Simplified Agent Evaluation

The MVP focuses on deterministic structured outputs and approval-gated write actions.

### Enterprise Version

A production enterprise system would include:

- regression evaluation suites
- red-team tests
- prompt injection testing
- tool misuse testing
- output quality scoring
- human review workflows
- monitoring for drift and degraded performance

## Enterprise Principle

A portfolio MVP can be smaller than a production system, but it should not hide where production hardening would be required.

## Current MVP Deviations

### Deterministic Agents

The current agents use deterministic logic to generate workflow artifacts.

Enterprise interpretation: the orchestration, policy, audit, and artifact boundaries are being validated before adding LLM reasoning. LLM-backed reasoning can be introduced behind the same controls.

### In-Memory Artifact and Audit Stores

The MVP stores artifacts and audit events in memory.

Enterprise interpretation: production systems should persist artifacts and audit events to durable storage such as Postgres/Supabase, with retention and access controls.

### Local Gateway Adapters Instead of Full MCP Transport

The API currently uses gateway modules that enforce policy and audit behavior while calling shared core packages directly.

Enterprise interpretation: production orchestration would call MCP servers through MCP client transport. The local gateway approach keeps the MVP testable while preserving the policy and audit control pattern.

### Synchronous Run Execution

The MVP executes the workflow analysis synchronously during `POST /runs`.

Enterprise interpretation: production systems should move longer-running analysis into background jobs or workflow orchestration infrastructure.

### Static Policy Catalog with Conservative Fallback

The MVP uses a policy catalog plus heuristic fallback classification.

Enterprise interpretation: production systems should integrate with enterprise data catalogs, policy-as-code, RBAC/ABAC, and security-reviewed classification rules.