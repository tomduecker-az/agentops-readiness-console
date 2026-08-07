from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from workflow_core.packet_v1_models import WorkflowPacketV1


DOCUMENTS = [
    {
        "document_id": "process_narrative",
        "title": "Process Narrative",
        "relative_path": "process_narrative.md",
        "document_type": "process_narrative",
    },
    {
        "document_id": "current_workflow_steps",
        "title": "Current Workflow Steps",
        "relative_path": "current_workflow_steps.md",
        "document_type": "current_workflow_steps",
    },
    {
        "document_id": "policy_and_controls",
        "title": "Policy and Controls",
        "relative_path": "policy_and_controls.md",
        "document_type": "policy_and_controls",
    },
    {
        "document_id": "sample_records",
        "title": "Sample Records",
        "relative_path": "sample_records.csv",
        "document_type": "sample_records",
    },
    {
        "document_id": "data_dictionary",
        "title": "Data Dictionary",
        "relative_path": "data_dictionary.md",
        "document_type": "supporting_documentation",
    },
    {
        "document_id": "goals_and_metrics",
        "title": "Goals and Metrics",
        "relative_path": "goals_and_metrics.md",
        "document_type": "supporting_documentation",
    },
    {
        "document_id": "target_systems",
        "title": "Target Systems",
        "relative_path": "target_systems.md",
        "document_type": "supporting_documentation",
    },
]


def export_workflow_packet_v1_documents(
    *,
    packet: WorkflowPacketV1,
    output_dir: str | Path,
    overwrite: bool = False,
) -> dict[str, Any]:
    output_path = Path(output_dir)

    if output_path.exists() and any(output_path.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory already exists and is not empty: {output_path}. "
            "Use overwrite=True or choose another output directory."
        )

    output_path.mkdir(parents=True, exist_ok=True)

    files_written: list[str] = []

    _write_text(
        output_path / "process_narrative.md",
        _render_process_narrative(packet),
        files_written,
    )
    _write_text(
        output_path / "current_workflow_steps.md",
        _render_current_workflow_steps(packet),
        files_written,
    )
    _write_text(
        output_path / "policy_and_controls.md",
        _render_policy_and_controls(packet),
        files_written,
    )
    _write_text(
        output_path / "data_dictionary.md",
        _render_data_dictionary(packet),
        files_written,
    )
    _write_text(
        output_path / "goals_and_metrics.md",
        _render_goals_and_metrics(packet),
        files_written,
    )
    _write_text(
        output_path / "target_systems.md",
        _render_target_systems(packet),
        files_written,
    )
    _write_sample_records_csv(
        output_path / "sample_records.csv",
        packet.sample_records,
        files_written,
    )

    normalized_packet_path = output_path / "normalized_packet.json"
    normalized_packet_path.write_text(
        json.dumps(asdict(packet), indent=2),
        encoding="utf-8",
    )
    files_written.append(str(normalized_packet_path))

    manifest = _build_manifest(packet, files_written)
    manifest_path = output_path / "workflow_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    files_written.append(str(manifest_path))

    return {
        "workflow_id": packet.workflow_id,
        "workflow_name": packet.workflow_name,
        "output_dir": str(output_path),
        "files_written": files_written,
        "manifest_path": str(manifest_path),
    }


def _render_process_narrative(packet: WorkflowPacketV1) -> str:
    lines = [
        "# Process Narrative",
        "",
        f"**Workflow ID:** `{packet.workflow_id}`",
        f"**Workflow Name:** {packet.workflow_name}",
        f"**Packet Version:** {packet.packet_version}",
        "",
        "## Workflow Overview",
        "",
    ]

    ordered_sections = [
        "Business Purpose",
        "Workflow Trigger",
        "Workflow Completion Criteria",
        "Primary Participants",
        "Systems Involved",
        "Current Pain Points",
        "AI Goals",
        "AI No-Go Areas",
        "Known Constraints",
    ]

    for section in ordered_sections:
        value = packet.overview.get(section, "")
        if value:
            lines.append(f"### {section}")
            lines.append("")
            lines.append(value)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_current_workflow_steps(packet: WorkflowPacketV1) -> str:
    lines = [
        "# Current Workflow Steps",
        "",
        "| Sequence | Step ID | Step Name | Owner Role | Output |",
        "|---:|---|---|---|---|",
    ]

    for step in packet.workflow_steps:
        lines.append(
            "| "
            f"{step.sequence} | "
            f"{_md(step.step_id)} | "
            f"{_md(step.step_name)} | "
            f"{_md(step.owner_role)} | "
            f"{_md(step.output)} |"
        )

    lines.append("")

    for step in packet.workflow_steps:
        lines.extend(
            [
                f"## {step.step_id}: {step.step_name}",
                "",
                f"**Owner Role:** {step.owner_role}",
                "",
                f"**Trigger/Input:** {step.trigger_or_input}",
                "",
                f"**Activity:** {step.activity}",
                "",
                f"**Decision or Rule:** {step.decision_or_rule}",
                "",
                f"**Systems Used:** {_join(step.systems_used)}",
                "",
                f"**Data Used:** {_join(step.data_used)}",
                "",
                f"**Output:** {step.output}",
                "",
                f"**Exceptions or Escalations:** {step.exceptions_or_escalations}",
                "",
                f"**Current Pain Points:** {step.current_pain_points}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _render_policy_and_controls(packet: WorkflowPacketV1) -> str:
    lines = [
        "# Policy and Controls",
        "",
        "| Control ID | Control Name | Type | Applies To Steps | Approval Required | Write Action Allowed |",
        "|---|---|---|---|---|---|",
    ]

    for control in packet.policy_controls:
        lines.append(
            "| "
            f"{_md(control.control_id)} | "
            f"{_md(control.control_name)} | "
            f"{_md(control.control_type)} | "
            f"{_md(_join(control.applies_to_steps))} | "
            f"{str(control.approval_required).lower()} | "
            f"{str(control.write_action_allowed).lower()} |"
        )

    lines.append("")

    for control in packet.policy_controls:
        lines.extend(
            [
                f"## {control.control_id}: {control.control_name}",
                "",
                f"**Control Type:** {control.control_type}",
                "",
                f"**Applies To Steps:** {_join(control.applies_to_steps)}",
                "",
                f"**Requirement:** {control.requirement}",
                "",
                f"**Approval Required:** {str(control.approval_required).lower()}",
                "",
                f"**Approval Role:** {control.approval_role or 'Not specified'}",
                "",
                f"**Evidence Required:** {control.evidence_required}",
                "",
                f"**Write Action Allowed:** {str(control.write_action_allowed).lower()}",
                "",
                f"**Retention Requirement:** {control.retention_requirement}",
                "",
                f"**Source Reference:** {control.source_reference}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _render_data_dictionary(packet: WorkflowPacketV1) -> str:
    lines = [
        "# Data Dictionary",
        "",
        "| Field Name | Category | Source System | Model Context Allowed | Redaction Required | Used In Steps |",
        "|---|---|---|---|---|---|",
    ]

    for field in packet.data_dictionary:
        lines.append(
            "| "
            f"{_md(field.field_name)} | "
            f"{_md(field.data_category)} | "
            f"{_md(field.source_system)} | "
            f"{str(field.model_context_allowed).lower()} | "
            f"{str(field.redaction_required).lower()} | "
            f"{_md(_join(field.used_in_steps))} |"
        )

    lines.append("")

    for field in packet.data_dictionary:
        lines.extend(
            [
                f"## {field.field_name}",
                "",
                f"**Business Meaning:** {field.business_meaning}",
                "",
                f"**Source System:** {field.source_system}",
                "",
                f"**Data Category:** {field.data_category}",
                "",
                f"**Required For Workflow:** {str(field.required_for_workflow).lower()}",
                "",
                f"**Model Context Allowed:** {str(field.model_context_allowed).lower()}",
                "",
                f"**Redaction Required:** {str(field.redaction_required).lower()}",
                "",
                f"**Allowed Values:** {_join(field.allowed_values) or 'Not specified'}",
                "",
                f"**Used In Steps:** {_join(field.used_in_steps) or 'Not specified'}",
                "",
                f"**Notes:** {field.notes}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _render_goals_and_metrics(packet: WorkflowPacketV1) -> str:
    lines = [
        "# Goals and Metrics",
        "",
    ]

    if not packet.goals_metrics:
        lines.append("No goals or metrics were provided.")
        return "\n".join(lines).rstrip() + "\n"

    for section, response in packet.goals_metrics.items():
        if response:
            lines.append(f"## {section}")
            lines.append("")
            lines.append(response)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_target_systems(packet: WorkflowPacketV1) -> str:
    lines = [
        "# Target Systems",
        "",
    ]

    if not packet.target_systems:
        lines.append("No target systems were provided.")
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "| System Name | Type | Read Access Possible | Write Access Possible | Owner Role | Authentication Method |",
            "|---|---|---|---|---|---|",
        ]
    )

    for system in packet.target_systems:
        lines.append(
            "| "
            f"{_md(system.system_name)} | "
            f"{_md(system.system_type)} | "
            f"{str(system.read_access_possible).lower()} | "
            f"{str(system.write_access_possible).lower()} | "
            f"{_md(system.owner_role)} | "
            f"{_md(system.authentication_method)} |"
        )

    lines.append("")

    for system in packet.target_systems:
        lines.extend(
            [
                f"## {system.system_name}",
                "",
                f"**System Type:** {system.system_type}",
                "",
                f"**Read Access Possible:** {str(system.read_access_possible).lower()}",
                "",
                f"**Write Access Possible:** {str(system.write_access_possible).lower()}",
                "",
                f"**Owner Role:** {system.owner_role}",
                "",
                f"**Authentication Method:** {system.authentication_method}",
                "",
                f"**Notes:** {system.notes}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _write_sample_records_csv(
    path: Path,
    sample_records: list[dict[str, Any]],
    files_written: list[str],
) -> None:
    if not sample_records:
        path.write_text("", encoding="utf-8")
        files_written.append(str(path))
        return

    fieldnames = list(sample_records[0].keys())

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for record in sample_records:
            writer.writerow({field: record.get(field, "") for field in fieldnames})

    files_written.append(str(path))


def _build_manifest(
    packet: WorkflowPacketV1,
    files_written: list[str],
) -> dict[str, Any]:
    return {
        "workflow_id": packet.workflow_id,
        "display_name": packet.workflow_name,
        "description": packet.overview.get("Business Purpose", ""),
        "packet_path": ".",
        "documents": DOCUMENTS,
        "metadata": {
            "source": {
                "type": "workflow_packet_v1",
                "packet_version": packet.packet_version,
                "source_file_name": packet.metadata.get("source_file_name"),
                "source_path": packet.metadata.get("source_path"),
            },
            "workflow_step_count": len(packet.workflow_steps),
            "policy_control_count": len(packet.policy_controls),
            "data_field_count": len(packet.data_dictionary),
            "sample_record_count": len(packet.sample_records),
            "target_system_count": len(packet.target_systems),
            "has_goals_metrics": bool(packet.goals_metrics),
            "files_written": files_written,
        },
    }


def _write_text(path: Path, content: str, files_written: list[str]) -> None:
    path.write_text(content, encoding="utf-8")
    files_written.append(str(path))


def _join(values: list[str]) -> str:
    return "; ".join(values)


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()