import csv
from io import StringIO
from typing import Any

from audit_core import AuditEventType
from policy_core.exceptions import UnknownDataElementError

from app.mcp_clients.document_gateway import read_document
from app.mcp_clients.policy_gateway import classify_data
from app.schemas.artifacts import ArtifactType
from app.services.artifact_service import create_artifact
from app.services.audit_service import log_audit_event


_AGENT_NAME = "data_sensitivity_classifier"


def generate_data_sensitivity_report(run_id: str, workflow_id: str) -> dict[str, Any]:
    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_started,
        actor=_AGENT_NAME,
        details={"workflow_id": workflow_id},
    )

    sample_records_document = read_document(
        run_id=run_id,
        agent_name=_AGENT_NAME,
        workflow_id=workflow_id,
        document_id="sample_records",
    )

    field_names, sample_rows = _parse_csv_metadata(sample_records_document.content)

    classified_fields = []
    unknown_fields = []

    for field_name in field_names:
        try:
            classification = classify_data(
                run_id=run_id,
                agent_name=_AGENT_NAME,
                data_element=field_name,
            )

            classified_fields.append(
                {
                    "field_name": field_name,
                    "sensitivity": classification.sensitivity.value,
                    "allowed_in_model_context": classification.allowed_in_model_context,
                    "requires_redaction": classification.requires_redaction,
                    "rationale": classification.rationale,
                    "sample_values": _sample_values_for_field(
                        sample_rows=sample_rows,
                        field_name=field_name,
                    ),
                }
            )

        except UnknownDataElementError as exc:
            unknown_fields.append(
                {
                    "field_name": field_name,
                    "issue": str(exc),
                    "recommended_action": "Add this field to the data classification catalog before using it in model context.",
                }
            )

    content = {
        "workflow_id": workflow_id,
        "title": "Data Sensitivity Report",
        "source_document": sample_records_document.document_id,
        "field_count": len(field_names),
        "classified_fields": classified_fields,
        "unknown_fields": unknown_fields,
        "summary": _build_summary(classified_fields, unknown_fields),
        "generation_mode": "deterministic_skeleton",
    }

    artifact = create_artifact(
        run_id=run_id,
        artifact_type=ArtifactType.data_sensitivity_report,
        content=content,
    )

    log_audit_event(
        run_id=run_id,
        event_type=AuditEventType.agent_completed,
        actor=_AGENT_NAME,
        details={
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type.value,
            "field_count": len(field_names),
            "unknown_field_count": len(unknown_fields),
        },
    )

    return artifact.model_dump(mode="json")


def _parse_csv_metadata(content: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(StringIO(content))
    rows = list(reader)

    field_names = reader.fieldnames or []

    return field_names, rows


def _sample_values_for_field(
    sample_rows: list[dict[str, str]],
    field_name: str,
    limit: int = 3,
) -> list[str]:
    values: list[str] = []

    for row in sample_rows:
        value = row.get(field_name)

        if value is None or value == "":
            continue

        if value not in values:
            values.append(value)

        if len(values) >= limit:
            break

    return values


def _build_summary(
    classified_fields: list[dict[str, Any]],
    unknown_fields: list[dict[str, Any]],
) -> dict[str, Any]:
    blocked_from_model_context = [
        field["field_name"]
        for field in classified_fields
        if not field["allowed_in_model_context"]
    ]

    requires_redaction = [
        field["field_name"]
        for field in classified_fields
        if field["requires_redaction"]
    ]

    financial_fields = [
        field["field_name"]
        for field in classified_fields
        if field["sensitivity"] == "financial_internal"
    ]

    return {
        "classified_field_count": len(classified_fields),
        "unknown_field_count": len(unknown_fields),
        "blocked_from_model_context": blocked_from_model_context,
        "requires_redaction": requires_redaction,
        "financial_fields": financial_fields,
    }