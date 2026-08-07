# Data Dictionary

| Field Name | Category | Source System | Model Context Allowed | Redaction Required | Used In Steps |
|---|---|---|---|---|---|
| record_id | Internal | Sample Data | true | false | STEP-001 |
| request_type | Internal | Ticketing System | true | false | STEP-001; STEP-003; STEP-010 |
| request_reason | Confidential | Ticketing System | false | true | STEP-001; STEP-005 |
| employee_status | PII | HRIS | false | true | STEP-002 |
| manager_verified | Derived Metadata | HRIS | true | false | STEP-002 |
| role_mapping_status | Derived Metadata | Ticketing System | true | false | STEP-003; STEP-004 |
| contains_privileged_access | Sensitive Access | Ticketing System | false | true | STEP-003; STEP-006 |
| access_scope | Sensitive Access | Ticketing System | false | true | STEP-001; STEP-003; STEP-005 |
| system_requested | Internal | Ticketing System | true | false | STEP-001; STEP-003 |
| verification_status | Derived Metadata | HRIS | true | false | STEP-002; STEP-004 |
| application_owner_approval | Internal | Ticketing System | true | false | STEP-005; STEP-007; STEP-010 |
| security_review_required | Derived Metadata | Ticketing System | true | false | STEP-003; STEP-006 |
| security_review_status | Internal | Ticketing System | true | false | STEP-006; STEP-007; STEP-010 |
| approval_status | Internal | Ticketing System | true | false | STEP-005; STEP-007; STEP-008; STEP-010 |
| action_details | Confidential | Identity Provider | false | true | STEP-007 |
| current_status | Internal | Ticketing System | true | false | STEP-008; STEP-009; STEP-010 |
| sla_risk | Derived Metadata | Reporting System | true | false | STEP-009 |
| notes | Confidential | Ticketing System | false | true | STEP-004; STEP-008 |

## record_id

**Business Meaning:** Unique anonymized sample record identifier

**Source System:** Sample Data

**Data Category:** Internal

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** Not specified

**Used In Steps:** STEP-001

**Notes:** Use anonymized record IDs only

## request_type

**Business Meaning:** Type of access request

**Source System:** Ticketing System

**Data Category:** Internal

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** standard; privileged; emergency

**Used In Steps:** STEP-001; STEP-003; STEP-010

**Notes:** Allowed if normalized

## request_reason

**Business Meaning:** Business justification for requested access

**Source System:** Ticketing System

**Data Category:** Confidential

**Required For Workflow:** true

**Model Context Allowed:** false

**Redaction Required:** true

**Allowed Values:** Not specified

**Used In Steps:** STEP-001; STEP-005

**Notes:** Free text should be summarized or excluded unless approved

## employee_status

**Business Meaning:** Employment status from HR source

**Source System:** HRIS

**Data Category:** PII

**Required For Workflow:** true

**Model Context Allowed:** false

**Redaction Required:** true

**Allowed Values:** active; inactive; terminated; unknown

**Used In Steps:** STEP-002

**Notes:** Use derived verification status in model context

## manager_verified

**Business Meaning:** Whether manager relationship was verified

**Source System:** HRIS

**Data Category:** Derived Metadata

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** true; false

**Used In Steps:** STEP-002

**Notes:** Model-safe derived signal

## role_mapping_status

**Business Meaning:** Whether requested access maps cleanly to an approved role

**Source System:** Ticketing System

**Data Category:** Derived Metadata

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** matched; missing; conflicting

**Used In Steps:** STEP-003; STEP-004

**Notes:** Useful for clarification routing

## contains_privileged_access

**Business Meaning:** Whether requested access includes privileged access

**Source System:** Ticketing System

**Data Category:** Sensitive Access

**Required For Workflow:** true

**Model Context Allowed:** false

**Redaction Required:** true

**Allowed Values:** true; false

**Used In Steps:** STEP-003; STEP-006

**Notes:** Use only approved derived handling

## access_scope

**Business Meaning:** Scope of requested access

**Source System:** Ticketing System

**Data Category:** Sensitive Access

**Required For Workflow:** true

**Model Context Allowed:** false

**Redaction Required:** true

**Allowed Values:** standard; privileged; admin; custom

**Used In Steps:** STEP-001; STEP-003; STEP-005

**Notes:** Do not send raw sensitive scope unless approved

## system_requested

**Business Meaning:** Application or system for which access is requested

**Source System:** Ticketing System

**Data Category:** Internal

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** Not specified

**Used In Steps:** STEP-001; STEP-003

**Notes:** Allowed if not itself sensitive

## verification_status

**Business Meaning:** Overall verification result

**Source System:** HRIS

**Data Category:** Derived Metadata

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** verified; failed; missing; conflicting

**Used In Steps:** STEP-002; STEP-004

**Notes:** Preferred model-safe verification signal

## application_owner_approval

**Business Meaning:** Application owner approval state

**Source System:** Ticketing System

**Data Category:** Internal

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** pending; approved; rejected; needs_clarification

**Used In Steps:** STEP-005; STEP-007; STEP-010

**Notes:** Approval alone does not authorize provisioning without all required reviews

## security_review_required

**Business Meaning:** Whether security review is required

**Source System:** Ticketing System

**Data Category:** Derived Metadata

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** true; false

**Used In Steps:** STEP-003; STEP-006

**Notes:** Derived routing signal

## security_review_status

**Business Meaning:** Security review state

**Source System:** Ticketing System

**Data Category:** Internal

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** not_required; pending; approved; rejected; needs_clarification

**Used In Steps:** STEP-006; STEP-007; STEP-010

**Notes:** Required before provisioning for privileged or sensitive requests

## approval_status

**Business Meaning:** Overall approval state

**Source System:** Ticketing System

**Data Category:** Internal

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** pending; approved; rejected; needs_clarification

**Used In Steps:** STEP-005; STEP-007; STEP-008; STEP-010

**Notes:** Must be validated against required approvals before execution

## action_details

**Business Meaning:** Provisioning action to execute

**Source System:** Identity Provider

**Data Category:** Confidential

**Required For Workflow:** true

**Model Context Allowed:** false

**Redaction Required:** true

**Allowed Values:** Not specified

**Used In Steps:** STEP-007

**Notes:** Do not expose raw provisioning details to model unless approved

## current_status

**Business Meaning:** Current workflow status

**Source System:** Ticketing System

**Data Category:** Internal

**Required For Workflow:** true

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** submitted; in_review; pending_security_review; ready_to_provision; completed; returned; escalated

**Used In Steps:** STEP-008; STEP-009; STEP-010

**Notes:** Controlled workflow state

## sla_risk

**Business Meaning:** Whether request is approaching SLA threshold

**Source System:** Reporting System

**Data Category:** Derived Metadata

**Required For Workflow:** false

**Model Context Allowed:** true

**Redaction Required:** false

**Allowed Values:** low; medium; high

**Used In Steps:** STEP-009

**Notes:** Useful for prioritization

## notes

**Business Meaning:** Free-text workflow notes

**Source System:** Ticketing System

**Data Category:** Confidential

**Required For Workflow:** false

**Model Context Allowed:** false

**Redaction Required:** true

**Allowed Values:** Not specified

**Used In Steps:** STEP-004; STEP-008

**Notes:** Free text requires careful handling
