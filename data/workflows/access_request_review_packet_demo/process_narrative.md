# Process Narrative

**Workflow ID:** `access_request_review`
**Workflow Name:** Access Request Review
**Packet Version:** workflow_packet_v1

## Workflow Overview

### Business Purpose

Ensure employees receive appropriate application access while preserving security, approval accountability, and audit evidence.

### Workflow Trigger

A manager submits an access request for an employee who needs access to an application, role, or system capability.

### Workflow Completion Criteria

The request is approved or rejected, approved access is provisioned when applicable, the ticket is updated, and required approval/evidence records are retained.

### Primary Participants

Manager; Identity Analyst; Application Owner; Security Reviewer; IT Provisioning Specialist

### Systems Involved

Ticketing System; HRIS; Identity Provider; Application Administration Console; Reporting System

### Current Pain Points

Manual verification, incomplete requests, inconsistent evidence packets, unclear routing for privileged access, SLA pressure, and audit preparation effort.

### AI Goals

Identify missing information earlier, prepare reviewer packets, summarize model-safe validation results, flag requests needing additional review, improve SLA visibility, and improve audit readiness.

### AI No-Go Areas

AI must not approve or reject access, provision access, update systems of record, send external communications, or bypass required human review.

### Known Constraints

PII and sensitive access details must be restricted from model context unless transformed into approved derived signals. Privileged access requires human review. Write actions require approval and audit logging.
