# Target Systems

| System Name | Type | Read Access Possible | Write Access Possible | Owner Role | Authentication Method |
|---|---|---|---|---|---|
| Ticketing System | workflow_system | true | true | Identity Operations | SSO or OAuth |
| HRIS | source_system | true | false | HR Operations | SSO |
| Identity Provider | identity_system | true | true | IT Security | Approved service account |
| Application Administration Console | execution_system | true | true | Application Owner | SSO or approved integration |
| Reporting System | reporting_system | true | true | Identity Operations | SSO |

## Ticketing System

**System Type:** workflow_system

**Read Access Possible:** true

**Write Access Possible:** true

**Owner Role:** Identity Operations

**Authentication Method:** SSO or OAuth

**Notes:** Ticket updates require approval/audit controls.

## HRIS

**System Type:** source_system

**Read Access Possible:** true

**Write Access Possible:** false

**Owner Role:** HR Operations

**Authentication Method:** SSO

**Notes:** Read-only verification source.

## Identity Provider

**System Type:** identity_system

**Read Access Possible:** true

**Write Access Possible:** true

**Owner Role:** IT Security

**Authentication Method:** Approved service account

**Notes:** Provisioning requires recorded approval evidence.

## Application Administration Console

**System Type:** execution_system

**Read Access Possible:** true

**Write Access Possible:** true

**Owner Role:** Application Owner

**Authentication Method:** SSO or approved integration

**Notes:** Application-specific access execution system.

## Reporting System

**System Type:** reporting_system

**Read Access Possible:** true

**Write Access Possible:** true

**Owner Role:** Identity Operations

**Authentication Method:** SSO

**Notes:** Report distribution requires review when sensitive information is included.
