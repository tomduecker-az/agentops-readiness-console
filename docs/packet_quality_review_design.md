# Packet Quality Review Design

## Purpose

The Packet Quality Review layer evaluates whether a completed Workflow Packet is internally consistent and reliable enough to support an AI readiness assessment.

The packet is not treated as ground truth. It is treated as a set of claims that must be tested.

## Design Principle

Do not rely on hardcoded workflow-specific keywords.

The deterministic layer should test:
- Structured workbook fields
- Cross-sheet references
- Controlled classification values
- Required ownership and approval relationships
- Declared systems and data elements
- Explicit AI no-go, control, and human-review boundaries

The LLM layer should test:
- Semantic omissions
- Misleading governance claims
- Incomplete no-go boundaries
- Implied process branches
- AI-readiness consequences

## Processing Flow

Workflow Packet
→ Normalized Packet JSON
→ Packet Claim Graph
→ Deterministic Consistency Rules
→ LLM Adversarial Packet Reviewer
→ Reconciled Packet Quality Review
→ Client Assessment Report

## Artifacts

### packet_claim_graph.json

Normalized claims extracted from the packet:
- workflow overview claims
- participant claims
- workflow step claims
- data handling claims
- system claims
- control claims
- sample record claims
- no-go claims

### packet_quality_review.json

Combined review artifact:
- deterministic findings
- advisory findings
- reconciled critical findings
- quality score dimensions
- recommended remediation before AI build

## Deterministic Finding Types

### Missing Reference

A workflow step references a data element, system, role, or control that is not declared elsewhere in the packet.

### Unresolved Accountability

A workflow step, approval, exception path, or control cannot be tied to a listed accountable participant/role.

### Control Enforceability Gap

A control requires approval or human review but does not define who enforces it, where it is enforced, or before which workflow action.

### Data Governance Contradiction

A data element has a sensitive/protected classification but is allowed into model context without redaction, transformation, or explicit safe-use rationale.

### Data Handling Inconsistency

Fields with the same classification or same declared business object have materially different model-context/redaction handling without explanation.

### No-Go Coverage Gap

The workflow contains a high-consequence action, but the AI no-go / human-review boundaries do not explicitly cover that action.

## LLM Adversarial Reviewer Questions

The reviewer should answer:

1. Which packet claims appear unsupported or contradictory?
2. Which fields may be misclassified or mishandled based on their description and usage?
3. Which high-consequence workflow actions are not clearly covered by no-go, control, or human-review boundaries?
4. Which process branches are implied by statuses, controls, or sample records but missing from workflow steps?
5. Which deterministic findings materially affect AI readiness?
6. What must be fixed before the recommended first AI product can be considered safe?

## Reporting Rule

The client assessment report must explicitly address all critical packet-quality findings.

The final report may not claim a workflow is model-safe, release-ready, or automation-ready unless the Packet Quality Review supports that claim.
