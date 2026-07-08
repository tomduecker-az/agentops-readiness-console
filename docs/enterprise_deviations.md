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