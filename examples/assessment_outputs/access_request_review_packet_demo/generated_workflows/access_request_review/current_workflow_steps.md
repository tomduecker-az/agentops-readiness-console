# Current Workflow Steps

| Sequence | Step ID | Step Name | Owner Role | Output |
|---:|---|---|---|---|
| 1 | STEP-001 | Submit access request | Manager | Submitted access request ticket |
| 2 | STEP-002 | Verify employee and manager | Identity Analyst | Employee and manager verification result |
| 3 | STEP-003 | Review access characteristics | Identity Analyst | Review classification |
| 4 | STEP-004 | Clarify missing or conflicting intake | Identity Analyst | Clarification request |
| 5 | STEP-005 | Application owner decision | Application Owner | Application owner approval outcome |
| 6 | STEP-006 | Security review | Security Reviewer | Security review outcome |
| 7 | STEP-007 | Provision approved access | IT Provisioning Specialist | Provisioned access |
| 8 | STEP-008 | Update ticket and evidence | Identity Analyst | Updated ticket and retained evidence |
| 9 | STEP-009 | Escalate near-SLA requests | Identity Analyst | Escalation notice |
| 10 | STEP-010 | Prepare weekly report and retain evidence | Identity Analyst | Weekly report and retained evidence |

## STEP-001: Submit access request

**Owner Role:** Manager

**Trigger/Input:** Employee needs application access

**Activity:** Submit access request with employee, application, role, access scope, and business justification.

**Decision or Rule:** Request must contain required intake fields before review can begin.

**Systems Used:** Ticketing System

**Data Used:** request_type; request_reason; system_requested; access_scope

**Output:** Submitted access request ticket

**Exceptions or Escalations:** Incomplete requests returned for clarification.

**Current Pain Points:** Missing or vague intake data causes rework.

## STEP-002: Verify employee and manager

**Owner Role:** Identity Analyst

**Trigger/Input:** Submitted access request

**Activity:** Verify employee status, manager relationship, role, and employment status against HR source.

**Decision or Rule:** Employee must be active and manager relationship must be valid.

**Systems Used:** Ticketing System; HRIS

**Data Used:** employee_status; manager_verified; verification_status

**Output:** Employee and manager verification result

**Exceptions or Escalations:** Conflicting HR data is escalated.

**Current Pain Points:** Manual verification takes analyst time.

## STEP-003: Review access characteristics

**Owner Role:** Identity Analyst

**Trigger/Input:** Verified request

**Activity:** Review whether access is privileged, sensitive, custom, API-based, SSO-related, or security-impacting.

**Decision or Rule:** Requests with privileged or sensitive characteristics require additional review.

**Systems Used:** Ticketing System; Application Administration Console

**Data Used:** request_type; contains_privileged_access; access_scope; system_requested

**Output:** Review classification

**Exceptions or Escalations:** Unclear access scope returned for clarification.

**Current Pain Points:** Routing criteria may be inconsistently applied.

## STEP-004: Clarify missing or conflicting intake

**Owner Role:** Identity Analyst

**Trigger/Input:** Missing, unclear, or conflicting information

**Activity:** Return request to manager or requester for clarification.

**Decision or Rule:** Clarification is required before approval routing if required data is missing.

**Systems Used:** Ticketing System

**Data Used:** verification_status; role_mapping_status; notes

**Output:** Clarification request

**Exceptions or Escalations:** Repeated clarification loops may occur.

**Current Pain Points:** Clarification loops increase cycle time.

## STEP-005: Application owner decision

**Owner Role:** Application Owner

**Trigger/Input:** Review-ready request

**Activity:** Approve or reject access request based on application ownership criteria.

**Decision or Rule:** Only authorized application owners can approve access.

**Systems Used:** Ticketing System

**Data Used:** application_owner_approval; access_scope; request_reason

**Output:** Application owner approval outcome

**Exceptions or Escalations:** Unauthorized or unclear approvals escalated.

**Current Pain Points:** Approval evidence may be incomplete or inconsistent.

## STEP-006: Security review

**Owner Role:** Security Reviewer

**Trigger/Input:** Privileged, sensitive, custom, API, SSO, or security-impacting request

**Activity:** Review additional risk and approve, reject, or request more information.

**Decision or Rule:** Security review is required for privileged or sensitive access.

**Systems Used:** Ticketing System; Identity Provider

**Data Used:** security_review_required; security_review_status; contains_privileged_access

**Output:** Security review outcome

**Exceptions or Escalations:** Incomplete risk context returned for clarification.

**Current Pain Points:** Security review routing depends on accurate classification.

## STEP-007: Provision approved access

**Owner Role:** IT Provisioning Specialist

**Trigger/Input:** Required approvals recorded

**Activity:** Provision approved access in identity provider or application administration system.

**Decision or Rule:** Provisioning cannot occur until required approvals are recorded.

**Systems Used:** Identity Provider; Application Administration Console

**Data Used:** application_owner_approval; security_review_status; action_details

**Output:** Provisioned access

**Exceptions or Escalations:** Provisioning failures escalated.

**Current Pain Points:** Manual provisioning creates delay and risk of inconsistency.

## STEP-008: Update ticket and evidence

**Owner Role:** Identity Analyst

**Trigger/Input:** Provisioning complete or request rejected

**Activity:** Update ticket status and attach required approval, provisioning, and review evidence.

**Decision or Rule:** System-of-record updates must include evidence references.

**Systems Used:** Ticketing System

**Data Used:** current_status; approval_status; notes

**Output:** Updated ticket and retained evidence

**Exceptions or Escalations:** Missing evidence routed back to responsible reviewer or provisioner.

**Current Pain Points:** Evidence collection creates audit effort.

## STEP-009: Escalate near-SLA requests

**Owner Role:** Identity Analyst

**Trigger/Input:** Request approaches SLA threshold

**Activity:** Escalate requests near SLA breach to appropriate owner.

**Decision or Rule:** Near-SLA requests require escalation according to operational policy.

**Systems Used:** Ticketing System; Reporting System

**Data Used:** current_status; sla_risk

**Output:** Escalation notice

**Exceptions or Escalations:** Unclear SLA threshold may delay escalation.

**Current Pain Points:** SLA management is manual.

## STEP-010: Prepare weekly report and retain evidence

**Owner Role:** Identity Analyst

**Trigger/Input:** Weekly reporting cycle

**Activity:** Prepare weekly access request report and retain required evidence.

**Decision or Rule:** Reports must be reviewed before distribution if they contain sensitive workflow information.

**Systems Used:** Reporting System; Ticketing System

**Data Used:** current_status; request_type; approval_status; security_review_status

**Output:** Weekly report and retained evidence

**Exceptions or Escalations:** Report discrepancies require follow-up.

**Current Pain Points:** Reporting preparation consumes analyst time.
