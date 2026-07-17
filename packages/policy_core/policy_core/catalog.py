from policy_core.models import (
    DataSensitivity,
    RequiredControl,
    ToolAccessLevel,
)


DATA_CLASSIFICATION_CATALOG: dict[str, dict[str, object]] = {
    "record_id": {
        "sensitivity": DataSensitivity.internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Synthetic/internal record identifiers are allowed in the demo context.",
    },
        "payment_date": {
        "sensitivity": DataSensitivity.financial_internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Payment dates are financial transaction metadata and should be handled as internal financial data.",
    },
    "exception_type": {
        "sensitivity": DataSensitivity.internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Exception type is internal operational metadata.",
    },
    "status": {
        "sensitivity": DataSensitivity.internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Workflow status is internal operational metadata.",
    },
    "assigned_role": {
        "sensitivity": DataSensitivity.internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Assigned role is internal process metadata and does not identify an individual in the demo workflow.",
    },
    "days_open": {
        "sensitivity": DataSensitivity.internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Days open is internal process-aging metadata.",
    },
    "requires_supervisor_review": {
        "sensitivity": DataSensitivity.internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Supervisor review requirement is internal control metadata.",
    },
    "payment_amount": {
        "sensitivity": DataSensitivity.financial_internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Payment amounts are financial data and require care, but synthetic demo values may be used.",
    },
    "source_system": {
        "sensitivity": DataSensitivity.internal,
        "allowed_in_model_context": True,
        "requires_redaction": False,
        "rationale": "Source-system labels are internal operational metadata.",
    },
    "customer_identifier": {
        "sensitivity": DataSensitivity.pii,
        "allowed_in_model_context": False,
        "requires_redaction": True,
        "rationale": "Customer-identifying data should not be sent to the model context.",
    },
    "notes": {
        "sensitivity": DataSensitivity.internal,
        "allowed_in_model_context": True,
        "requires_redaction": True,
        "rationale": "Free-text notes may contain sensitive data and should be reviewed or redacted.",
    },
}


TOOL_PERMISSION_CATALOG: dict[str, dict[str, object]] = {
    "document_server.list_documents": {
        "access_level": ToolAccessLevel.read,
        "allowed_agents": [
            "workflow_mapper",
            "data_sensitivity_classifier",
            "risk_control_designer",
            "coordinator",
        ],
        "requires_human_approval": False,
        "rationale": "Listing registered document metadata is read-only.",
    },
    "document_server.read_document": {
        "access_level": ToolAccessLevel.read,
        "allowed_agents": [
            "workflow_mapper",
            "data_sensitivity_classifier",
            "risk_control_designer",
            "coordinator",
        ],
        "requires_human_approval": False,
        "rationale": "Reading registered workflow documents is allowed for analysis agents.",
    },
        "policy_server.classify_data": {
        "access_level": ToolAccessLevel.read,
        "allowed_agents": [
            "data_sensitivity_classifier",
            "risk_control_designer",
            "coordinator",
            "tool_policy_guardian",
        ],
        "requires_human_approval": False,
        "rationale": "Data classification policy checks are read-only governance operations.",
    },
    "policy_server.get_required_controls": {
        "access_level": ToolAccessLevel.read,
        "allowed_agents": [
            "risk_control_designer",
            "hitl_designer",
            "coordinator",
            "tool_policy_guardian",
        ],
        "requires_human_approval": False,
        "rationale": "Control lookup is a read-only governance operation.",
    },
    "policy_server.check_tool_permission": {
        "access_level": ToolAccessLevel.read,
        "allowed_agents": [
            "coordinator",
            "tool_policy_guardian",
        ],
        "requires_human_approval": False,
        "rationale": "Tool permission checks are read-only governance operations.",
    },
    "document_server.search_documents": {
        "access_level": ToolAccessLevel.read,
        "allowed_agents": [
            "workflow_mapper",
            "data_sensitivity_classifier",
            "risk_control_designer",
            "coordinator",
        ],
        "requires_human_approval": False,
        "rationale": "Searching registered workflow documents is read-only.",
    },
    "audit_server.log_event": {
        "access_level": ToolAccessLevel.append,
        "allowed_agents": [
            "coordinator",
            "workflow_mapper",
            "data_sensitivity_classifier",
            "risk_control_designer",
            "hitl_designer",
            "implementation_planner",
            "tool_policy_guardian",
        ],
        "requires_human_approval": False,
        "rationale": "Append-only audit logging is allowed and required for traceability.",
    },
    "project_mgmt_server.create_issue": {
        "access_level": ToolAccessLevel.write,
        "allowed_agents": [
            "implementation_planner",
        ],
        "requires_human_approval": True,
        "rationale": "Creating project-management issues is a write action and requires human approval.",
    },
}


CONTROL_CATALOG: dict[str, list[RequiredControl]] = {
    "financial_status_adjustment": [
        RequiredControl(
            control_id="CTRL-HITL-001",
            name="Human approval before financial write action",
            description="Any action that changes financial status requires human approval before execution.",
            applies_to=["payment_amount", "status", "adjustment"],
        ),
        RequiredControl(
            control_id="CTRL-AUDIT-001",
            name="Audit log for financial decision",
            description="Financial decisions and write actions must be logged with run ID, actor, timestamp, and rationale.",
            applies_to=["payment_amount", "status", "approval"],
        ),
    ],
    "missing_source_identifier": [
        RequiredControl(
            control_id="CTRL-VALID-001",
            name="Block automatic closure when source identifier is missing",
            description="Records missing source-system identifiers cannot be auto-closed.",
            applies_to=["source_system", "record_id"],
        ),
    ],
    "implementation_backlog_write": [
        RequiredControl(
            control_id="CTRL-HITL-002",
            name="Human approval before backlog creation",
            description="Backlog items may be proposed by the agent, but real issue creation requires approval.",
            applies_to=["project_mgmt_server.create_issue"],
        ),
        RequiredControl(
            control_id="CTRL-AUDIT-002",
            name="Audit project-management write action",
            description="Issue creation must be logged with approval reference and created issue URL.",
            applies_to=["project_mgmt_server.create_issue"],
        ),
    ],
    "governed_workflow_decision": [
        RequiredControl(
            control_id="CTRL-HITL-001",
            name="Human approval before governed decision",
            description="Policy-defined approval decisions must be reviewed before the workflow item advances.",
            applies_to=["approval", "review", "decision", "workflow_advancement"],
        ),
        RequiredControl(
            control_id="CTRL-AUDIT-001",
            name="Audit log for governed decision",
            description="Approval decisions must be logged with run ID, actor, timestamp, and rationale.",
            applies_to=["approval", "decision", "review"],
        ),
    ],
    "operational_write_action": [
        RequiredControl(
            control_id="CTRL-HITL-001",
            name="Human approval before operational write action",
            description="Workflow status, assignments, customer-facing language, or system-of-record updates require approval before execution.",
            applies_to=["status", "assignment", "external_message", "system_of_record"],
        ),
        RequiredControl(
            control_id="CTRL-AUDIT-001",
            name="Audit log for operational write action",
            description="Operational write actions must be logged with approval reference, actor, timestamp, and affected record.",
            applies_to=["write_action", "status", "assignment", "system_of_record"],
        ),
    ],
    "source_record_validation": [
        RequiredControl(
            control_id="CTRL-VALID-001",
            name="Validate source and intake records before finalization",
            description="Workflow items cannot be finalized when required source, intake, or reference information is missing or conflicting.",
            applies_to=["source_record", "intake", "record_id", "required_fields"],
        ),
    ],
    "customer_facing_commitment": [
        RequiredControl(
            control_id="CTRL-HITL-001",
            name="Human review before customer-facing commitment",
            description="Customer-facing commitments, timelines, and external language require authorized review before release.",
            applies_to=["customer_message", "commitment", "timeline", "external_communication"],
        ),
        RequiredControl(
            control_id="CTRL-AUDIT-001",
            name="Audit customer-facing commitment approval",
            description="Customer-facing approvals must be logged with reviewer, rationale, and approved version.",
            applies_to=["customer_message", "commitment", "approval"],
        ),
    ],
    "implementation_scope_change": [
        RequiredControl(
            control_id="CTRL-HITL-001",
            name="Human review before implementation scope change",
            description="Implementation scope, custom integration, or enterprise-term changes require approval before finalization.",
            applies_to=["scope", "integration", "enterprise_terms", "implementation_plan"],
        ),
        RequiredControl(
            control_id="CTRL-AUDIT-001",
            name="Audit implementation scope decision",
            description="Scope-related decisions must be traceable to reviewer, rationale, and source evidence.",
            applies_to=["scope", "integration", "approval"],
        ),
    ],
    "sensitive_integration_review": [
        RequiredControl(
            control_id="CTRL-HITL-001",
            name="Human review before sensitive integration planning",
            description="Sensitive data, security, SSO, file transfer, or custom integration requirements require technical or security review.",
            applies_to=["sensitive_data", "integration", "sso", "security", "file_transfer"],
        ),
        RequiredControl(
            control_id="CTRL-AUDIT-001",
            name="Audit sensitive integration review",
            description="Sensitive integration review decisions must be logged with reviewer, rationale, and required controls.",
            applies_to=["integration", "security_review", "approval"],
        ),
    ],
    "intake_handoff_quality": [
        RequiredControl(
            control_id="CTRL-VALID-001",
            name="Validate intake and handoff completeness",
            description="Missing or unclear intake information must be routed for clarification before planning or customer communication.",
            applies_to=["intake", "handoff", "required_fields", "clarification"],
        ),
    ],
    "accelerated_timeline_review": [
        RequiredControl(
            control_id="CTRL-HITL-001",
            name="Human review before accelerated timeline commitment",
            description="Compressed timelines require review before dates, staffing, or delivery commitments are shared externally.",
            applies_to=["timeline", "launch_date", "capacity", "commitment"],
        ),
        RequiredControl(
            control_id="CTRL-AUDIT-001",
            name="Audit accelerated timeline approval",
            description="Accelerated timeline approvals must be logged with reviewer, rationale, and accepted risk.",
            applies_to=["timeline", "approval", "commitment"],
        ),
    ],
}