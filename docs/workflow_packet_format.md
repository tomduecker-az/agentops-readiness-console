# Workflow Packet Format

A workflow packet is a small folder of files that describes a business process for governed agentic analysis.

The system discovers workflows from:

```text
data/workflows/<workflow_id>/workflow_manifest.json
```

## Required Files

Each workflow packet should include:

```text
workflow_manifest.json
process_narrative.md
current_workflow_steps.md
policy_and_controls.md
sample_records.csv
```

## workflow_manifest.json

The manifest registers the workflow with the system.

Example:

```json
{
  "workflow_id": "invoice_exception_review",
  "display_name": "Invoice Exception Review",
  "description": "A workflow for reviewing and resolving invoice exceptions.",
  "packet_path": "data/workflows/invoice_exception_review",
  "documents": [
    {
      "document_id": "process_narrative",
      "title": "Process Narrative",
      "relative_path": "process_narrative.md",
      "document_type": "narrative",
      "required": true
    },
    {
      "document_id": "current_workflow_steps",
      "title": "Current Workflow Steps",
      "relative_path": "current_workflow_steps.md",
      "document_type": "workflow_steps",
      "required": true
    },
    {
      "document_id": "policy_and_controls",
      "title": "Policy and Controls",
      "relative_path": "policy_and_controls.md",
      "document_type": "policy",
      "required": true
    },
    {
      "document_id": "sample_records",
      "title": "Sample Records",
      "relative_path": "sample_records.csv",
      "document_type": "sample_records",
      "required": true
    }
  ]
}
```

## process_narrative.md

Describe the workflow in plain language.

Include the process trigger, participants, systems, decisions, exceptions, escalations, and completion criteria.

## current_workflow_steps.md

List the current process steps as a numbered list.

Example:

```markdown
# Current Workflow Steps

1. Analyst receives an unmatched invoice.
2. Analyst checks the source system for matching details.
3. Analyst determines the exception type.
4. Supervisor reviews exceptions above the approval threshold.
5. Analyst updates the exception status.
```

The current deterministic workflow mapper expects numbered steps.

## policy_and_controls.md

List known policies, approval requirements, controls, and constraints.

Example:

```markdown
# Policy and Controls

- Exceptions above approval threshold require supervisor approval.
- Records missing source-system identifiers cannot be auto-closed.
- Customer-identifying data must not be included in LLM prompts.
- Write actions require explicit human approval.
```

## sample_records.csv

Provide representative, anonymized sample records.

The first row must contain field names. These field names are used by the Data Sensitivity Agent.

Example:

```csv
record_id,invoice_amount,status,assigned_role,notes
REC-001,5000,Open,Analyst,Missing source-system reference
REC-002,750,Pending Review,Supervisor,Requires review
```

## Sensitive Data Guidance

Do not include real customer-identifying data, secrets, credentials, production financial records, or regulated personal data in demo workflow packets.

Use anonymized or synthetic values.

The policy layer uses conservative fallback classification for unknown fields.