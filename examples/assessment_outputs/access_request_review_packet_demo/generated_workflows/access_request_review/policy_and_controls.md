# Policy and Controls

| Control ID | Control Name | Type | Applies To Steps | Approval Required | Write Action Allowed |
|---|---|---|---|---|---|
| CTRL-001 | Minimum intake requirements | policy | STEP-001; STEP-004 | false | false |
| CTRL-002 | Employee and manager verification | policy | STEP-002 | false | false |
| CTRL-003 | Application owner approval | approval | STEP-005; STEP-007 | true | true |
| CTRL-004 | Security review for privileged or sensitive access | approval | STEP-003; STEP-006; STEP-007 | true | true |
| CTRL-005 | No restricted data in model context | data | STEP-001; STEP-002; STEP-003; STEP-006 | false | false |
| CTRL-006 | Provisioning requires recorded approvals | approval | STEP-007 | true | true |
| CTRL-007 | System-of-record updates must be audited | audit | STEP-008 | true | true |
| CTRL-008 | Report review and evidence retention | retention | STEP-010 | true | true |

## CTRL-001: Minimum intake requirements

**Control Type:** policy

**Applies To Steps:** STEP-001; STEP-004

**Requirement:** Access requests must contain required intake fields before review can proceed.

**Approval Required:** false

**Approval Role:** Not specified

**Evidence Required:** Completed request form

**Write Action Allowed:** false

**Retention Requirement:** Retain with request ticket

**Source Reference:** Access intake procedure

## CTRL-002: Employee and manager verification

**Control Type:** policy

**Applies To Steps:** STEP-002

**Requirement:** Employee status and manager relationship must be verified before approval routing.

**Approval Required:** false

**Approval Role:** Not specified

**Evidence Required:** Verification result

**Write Action Allowed:** false

**Retention Requirement:** Retain with request ticket

**Source Reference:** Identity operations procedure

## CTRL-003: Application owner approval

**Control Type:** approval

**Applies To Steps:** STEP-005; STEP-007

**Requirement:** Application owner approval is required before access can be provisioned.

**Approval Required:** true

**Approval Role:** Application Owner

**Evidence Required:** Recorded approval

**Write Action Allowed:** true

**Retention Requirement:** Retain according to audit policy

**Source Reference:** Access approval policy

## CTRL-004: Security review for privileged or sensitive access

**Control Type:** approval

**Applies To Steps:** STEP-003; STEP-006; STEP-007

**Requirement:** Privileged, sensitive, custom, API, SSO, or security-impacting access requires security review before provisioning.

**Approval Required:** true

**Approval Role:** Security Reviewer

**Evidence Required:** Security review outcome

**Write Action Allowed:** true

**Retention Requirement:** Retain according to audit policy

**Source Reference:** Privileged access policy

## CTRL-005: No restricted data in model context

**Control Type:** data

**Applies To Steps:** STEP-001; STEP-002; STEP-003; STEP-006

**Requirement:** PII and sensitive access details must be excluded or transformed before model use.

**Approval Required:** false

**Approval Role:** Not specified

**Evidence Required:** Model-context filtering log

**Write Action Allowed:** false

**Retention Requirement:** Retain model input audit log

**Source Reference:** AI data handling policy

## CTRL-006: Provisioning requires recorded approvals

**Control Type:** approval

**Applies To Steps:** STEP-007

**Requirement:** Provisioning cannot occur until required approval evidence is present.

**Approval Required:** true

**Approval Role:** IT Provisioning Lead

**Evidence Required:** Approval and provisioning evidence

**Write Action Allowed:** true

**Retention Requirement:** Retain according to audit policy

**Source Reference:** Provisioning control procedure

## CTRL-007: System-of-record updates must be audited

**Control Type:** audit

**Applies To Steps:** STEP-008

**Requirement:** Ticket updates must record actor, timestamp, action, and evidence reference.

**Approval Required:** true

**Approval Role:** Identity Operations Lead

**Evidence Required:** Audit event

**Write Action Allowed:** true

**Retention Requirement:** Retain according to audit policy

**Source Reference:** Audit policy

## CTRL-008: Report review and evidence retention

**Control Type:** retention

**Applies To Steps:** STEP-010

**Requirement:** Weekly reports and supporting evidence must be retained and reviewed before distribution if sensitive information is included.

**Approval Required:** true

**Approval Role:** Identity Operations Lead

**Evidence Required:** Reviewed report and evidence package

**Write Action Allowed:** true

**Retention Requirement:** Retain according to audit policy

**Source Reference:** Reporting and evidence retention policy
