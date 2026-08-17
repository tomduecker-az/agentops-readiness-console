from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ClaimSource:
    section: str
    row_index: int | None = None
    field: str | None = None


@dataclass(frozen=True)
class PacketClaim:
    claim_id: str
    claim_type: str
    subject_id: str
    properties: dict[str, Any]
    source: ClaimSource


def build_packet_claim_graph(normalized_packet: dict[str, Any]) -> dict[str, Any]:
    claims: list[PacketClaim] = []

    claims.extend(_overview_claims(normalized_packet.get("overview", {})))
    claims.extend(_workflow_step_claims(normalized_packet.get("workflow_steps", [])))
    claims.extend(_policy_control_claims(normalized_packet.get("policy_controls", [])))
    claims.extend(_data_dictionary_claims(normalized_packet.get("data_dictionary", [])))
    claims.extend(_sample_record_claims(normalized_packet.get("sample_records", [])))
    claims.extend(_goal_metric_claims(normalized_packet.get("goals_metrics", {})))
    claims.extend(_target_system_claims(normalized_packet.get("target_systems", [])))

    claim_dicts = [asdict(claim) for claim in claims]

    return {
        "artifact_type": "packet_claim_graph",
        "schema_version": "packet_claim_graph_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "workflow_id": normalized_packet.get("workflow_id"),
        "workflow_name": normalized_packet.get("workflow_name"),
        "packet_version": normalized_packet.get("packet_version"),
        "claims": claim_dicts,
        "indexes": _build_indexes(claim_dicts),
        "metadata": {
            "claim_count": len(claim_dicts),
            "source_metadata": normalized_packet.get("metadata", {}),
        },
    }


def _overview_claims(overview: dict[str, Any]) -> list[PacketClaim]:
    claims: list[PacketClaim] = []

    overview_fields = {
        "workflow_name": "Workflow Name",
        "business_purpose": "Business Purpose",
        "workflow_trigger": "Workflow Trigger",
        "completion_criteria": "Workflow Completion Criteria",
        "primary_participants": "Primary Participants",
        "systems_involved": "Systems Involved",
        "current_pain_points": "Current Pain Points",
        "ai_goals": "AI Goals",
        "ai_no_go_areas": "AI No-Go Areas",
        "known_constraints": "Known Constraints",
    }

    for normalized_name, source_field in overview_fields.items():
        value = overview.get(source_field)

        if _is_blank(value):
            continue

        claims.append(
            PacketClaim(
                claim_id=f"OVERVIEW-{len(claims) + 1:03d}",
                claim_type="overview_claim",
                subject_id=normalized_name,
                properties={
                    "name": normalized_name,
                    "value": value,
                },
                source=ClaimSource(
                    section="overview",
                    field=source_field,
                ),
            )
        )

    participants = _split_list_like(overview.get("Primary Participants"))
    for participant in participants:
        claims.append(
            PacketClaim(
                claim_id=f"PARTICIPANT-{len([c for c in claims if c.claim_type == 'participant_claim']) + 1:03d}",
                claim_type="participant_claim",
                subject_id=_slug(participant),
                properties={
                    "role_name": participant,
                    "declared_in_overview": True,
                },
                source=ClaimSource(section="overview", field="Primary Participants"),
            )
        )

    systems = _split_list_like(overview.get("Systems Involved"))
    for system in systems:
        claims.append(
            PacketClaim(
                claim_id=f"OVERVIEW-SYSTEM-{len([c for c in claims if c.claim_type == 'overview_system_claim']) + 1:03d}",
                claim_type="overview_system_claim",
                subject_id=_slug(system),
                properties={
                    "system_name": system,
                    "declared_in_overview": True,
                },
                source=ClaimSource(section="overview", field="Systems Involved"),
            )
        )

    no_go_areas = _split_list_like(overview.get("AI No-Go Areas"))
    for no_go_area in no_go_areas:
        claims.append(
            PacketClaim(
                claim_id=f"NOGO-{len([c for c in claims if c.claim_type == 'ai_no_go_claim']) + 1:03d}",
                claim_type="ai_no_go_claim",
                subject_id=_slug(no_go_area),
                properties={
                    "no_go_text": no_go_area,
                },
                source=ClaimSource(section="overview", field="AI No-Go Areas"),
            )
        )

    return claims


def _workflow_step_claims(rows: list[dict[str, Any]]) -> list[PacketClaim]:
    claims: list[PacketClaim] = []

    for idx, row in enumerate(rows, start=1):
        step_id = _text(row.get("step_id")) or f"step_row_{idx}"

        claims.append(
            PacketClaim(
                claim_id=f"STEP-{idx:03d}",
                claim_type="workflow_step_claim",
                subject_id=step_id,
                properties={
                    "step_id": step_id,
                    "step_name": row.get("step_name"),
                    "sequence": row.get("sequence"),
                    "owner_role": row.get("owner_role"),
                    "trigger_or_input": row.get("trigger_or_input"),
                    "activity": row.get("activity"),
                    "decision_or_rule": row.get("decision_or_rule"),
                    "systems_used": row.get("systems_used") or [],
                    "data_used": row.get("data_used") or [],
                    "output": row.get("output"),
                    "exceptions_or_escalations": row.get("exceptions_or_escalations"),
                    "current_pain_points": row.get("current_pain_points"),
                },
                source=ClaimSource(section="workflow_steps", row_index=idx),
            )
        )

        owner_role = _text(row.get("owner_role"))
        if owner_role:
            claims.append(
                PacketClaim(
                    claim_id=f"STEP-OWNER-{idx:03d}",
                    claim_type="step_owner_claim",
                    subject_id=f"{step_id}:{_slug(owner_role)}",
                    properties={
                        "step_id": step_id,
                        "owner_role": owner_role,
                    },
                    source=ClaimSource(section="workflow_steps", row_index=idx, field="owner_role"),
                )
            )

        for system in row.get("systems_used") or []:
            claims.append(
                PacketClaim(
                    claim_id=f"STEP-SYSTEM-{idx:03d}-{len([c for c in claims if c.claim_type == 'step_system_usage_claim']) + 1:03d}",
                    claim_type="step_system_usage_claim",
                    subject_id=f"{step_id}:{_slug(system)}",
                    properties={
                        "step_id": step_id,
                        "system_name": system,
                    },
                    source=ClaimSource(section="workflow_steps", row_index=idx, field="systems_used"),
                )
            )

        for field_name in row.get("data_used") or []:
            claims.append(
                PacketClaim(
                    claim_id=f"STEP-DATA-{idx:03d}-{len([c for c in claims if c.claim_type == 'step_data_usage_claim']) + 1:03d}",
                    claim_type="step_data_usage_claim",
                    subject_id=f"{step_id}:{_slug(field_name)}",
                    properties={
                        "step_id": step_id,
                        "field_name": field_name,
                    },
                    source=ClaimSource(section="workflow_steps", row_index=idx, field="data_used"),
                )
            )

    return claims


def _policy_control_claims(rows: list[dict[str, Any]]) -> list[PacketClaim]:
    claims: list[PacketClaim] = []

    for idx, row in enumerate(rows, start=1):
        control_id = _text(row.get("control_id")) or f"control_row_{idx}"

        claims.append(
            PacketClaim(
                claim_id=f"CONTROL-{idx:03d}",
                claim_type="policy_control_claim",
                subject_id=control_id,
                properties={
                    "control_id": control_id,
                    "control_name": row.get("control_name"),
                    "control_type": row.get("control_type"),
                    "applies_to_steps": row.get("applies_to_steps") or [],
                    "requirement": row.get("requirement"),
                    "approval_required": _to_bool(row.get("approval_required")),
                    "approval_role": row.get("approval_role"),
                    "evidence_required": row.get("evidence_required"),
                    "write_action_allowed": _to_bool(row.get("write_action_allowed")),
                    "retention_requirement": row.get("retention_requirement"),
                    "source_reference": row.get("source_reference"),
                },
                source=ClaimSource(section="policy_controls", row_index=idx),
            )
        )

        approval_role = _text(row.get("approval_role"))
        if approval_role:
            claims.append(
                PacketClaim(
                    claim_id=f"CONTROL-APPROVER-{idx:03d}",
                    claim_type="control_approval_role_claim",
                    subject_id=f"{control_id}:{_slug(approval_role)}",
                    properties={
                        "control_id": control_id,
                        "approval_required": _to_bool(row.get("approval_required")),
                        "approval_role": approval_role,
                    },
                    source=ClaimSource(section="policy_controls", row_index=idx, field="approval_role"),
                )
            )

        for step_id in row.get("applies_to_steps") or []:
            claims.append(
                PacketClaim(
                    claim_id=f"CONTROL-STEP-{idx:03d}-{len([c for c in claims if c.claim_type == 'control_step_application_claim']) + 1:03d}",
                    claim_type="control_step_application_claim",
                    subject_id=f"{control_id}:{step_id}",
                    properties={
                        "control_id": control_id,
                        "step_id": step_id,
                    },
                    source=ClaimSource(section="policy_controls", row_index=idx, field="applies_to_steps"),
                )
            )

    return claims


def _data_dictionary_claims(rows: list[dict[str, Any]]) -> list[PacketClaim]:
    claims: list[PacketClaim] = []

    for idx, row in enumerate(rows, start=1):
        field_name = _text(row.get("field_name")) or f"field_row_{idx}"

        claims.append(
            PacketClaim(
                claim_id=f"DATA-{idx:03d}",
                claim_type="data_handling_claim",
                subject_id=field_name,
                properties={
                    "field_name": field_name,
                    "business_meaning": row.get("business_meaning"),
                    "source_system": row.get("source_system"),
                    "data_category": row.get("data_category"),
                    "required_for_workflow": _to_bool(row.get("required_for_workflow")),
                    "model_context_allowed": _to_bool(row.get("model_context_allowed")),
                    "redaction_required": _to_bool(row.get("redaction_required")),
                    "allowed_values": row.get("allowed_values") or [],
                    "used_in_steps": row.get("used_in_steps") or [],
                    "notes": row.get("notes"),
                },
                source=ClaimSource(section="data_dictionary", row_index=idx),
            )
        )

        source_system = _text(row.get("source_system"))
        if source_system:
            claims.append(
                PacketClaim(
                    claim_id=f"DATA-SYSTEM-{idx:03d}",
                    claim_type="data_source_system_claim",
                    subject_id=f"{field_name}:{_slug(source_system)}",
                    properties={
                        "field_name": field_name,
                        "source_system": source_system,
                    },
                    source=ClaimSource(section="data_dictionary", row_index=idx, field="source_system"),
                )
            )

        for step_id in row.get("used_in_steps") or []:
            claims.append(
                PacketClaim(
                    claim_id=f"DATA-STEP-{idx:03d}-{len([c for c in claims if c.claim_type == 'data_step_usage_claim']) + 1:03d}",
                    claim_type="data_step_usage_claim",
                    subject_id=f"{field_name}:{step_id}",
                    properties={
                        "field_name": field_name,
                        "step_id": step_id,
                    },
                    source=ClaimSource(section="data_dictionary", row_index=idx, field="used_in_steps"),
                )
            )

    return claims


def _sample_record_claims(rows: list[dict[str, Any]]) -> list[PacketClaim]:
    claims: list[PacketClaim] = []

    for idx, row in enumerate(rows, start=1):
        record_id = _text(row.get("record_id")) or f"sample_record_row_{idx}"

        claims.append(
            PacketClaim(
                claim_id=f"RECORD-{idx:03d}",
                claim_type="sample_record_claim",
                subject_id=record_id,
                properties=dict(row),
                source=ClaimSource(section="sample_records", row_index=idx),
            )
        )

    return claims


def _goal_metric_claims(goals_metrics: dict[str, Any]) -> list[PacketClaim]:
    claims: list[PacketClaim] = []

    for idx, (key, value) in enumerate(goals_metrics.items(), start=1):
        if _is_blank(value):
            continue

        claims.append(
            PacketClaim(
                claim_id=f"GOAL-{idx:03d}",
                claim_type="goal_metric_claim",
                subject_id=_slug(key),
                properties={
                    "name": key,
                    "value": value,
                },
                source=ClaimSource(section="goals_metrics", field=key),
            )
        )

    return claims


def _target_system_claims(rows: list[dict[str, Any]]) -> list[PacketClaim]:
    claims: list[PacketClaim] = []

    for idx, row in enumerate(rows, start=1):
        system_name = _text(row.get("system_name")) or f"system_row_{idx}"

        claims.append(
            PacketClaim(
                claim_id=f"SYSTEM-{idx:03d}",
                claim_type="target_system_claim",
                subject_id=system_name,
                properties={
                    "system_name": system_name,
                    "system_type": row.get("system_type"),
                    "read_access_possible": _to_bool(row.get("read_access_possible")),
                    "write_access_possible": _to_bool(row.get("write_access_possible")),
                    "owner_role": row.get("owner_role"),
                    "authentication_method": row.get("authentication_method"),
                    "notes": row.get("notes"),
                },
                source=ClaimSource(section="target_systems", row_index=idx),
            )
        )

        owner_role = _text(row.get("owner_role"))
        if owner_role:
            claims.append(
                PacketClaim(
                    claim_id=f"SYSTEM-OWNER-{idx:03d}",
                    claim_type="system_owner_claim",
                    subject_id=f"{system_name}:{_slug(owner_role)}",
                    properties={
                        "system_name": system_name,
                        "owner_role": owner_role,
                    },
                    source=ClaimSource(section="target_systems", row_index=idx, field="owner_role"),
                )
            )

    return claims


def _build_indexes(claims: list[dict[str, Any]]) -> dict[str, Any]:
    indexes: dict[str, Any] = {
        "workflow_steps": {},
        "data_fields": {},
        "target_systems": {},
        "overview_systems": {},
        "participants": {},
        "policy_controls": {},
        "ai_no_go_claims": {},
        "sample_records": {},
        "claims_by_type": {},
    }

    for claim in claims:
        claim_type = claim["claim_type"]
        subject_id = claim["subject_id"]

        indexes["claims_by_type"].setdefault(claim_type, []).append(claim["claim_id"])

        if claim_type == "workflow_step_claim":
            indexes["workflow_steps"][_slug(subject_id)] = claim["claim_id"]
        elif claim_type == "data_handling_claim":
            indexes["data_fields"][_slug(subject_id)] = claim["claim_id"]
        elif claim_type == "target_system_claim":
            indexes["target_systems"][_slug(subject_id)] = claim["claim_id"]
        elif claim_type == "overview_system_claim":
            indexes["overview_systems"][_slug(subject_id)] = claim["claim_id"]
        elif claim_type == "participant_claim":
            indexes["participants"][_slug(subject_id)] = claim["claim_id"]
        elif claim_type == "policy_control_claim":
            indexes["policy_controls"][_slug(subject_id)] = claim["claim_id"]
        elif claim_type == "ai_no_go_claim":
            indexes["ai_no_go_claims"][_slug(subject_id)] = claim["claim_id"]
        elif claim_type == "sample_record_claim":
            indexes["sample_records"][_slug(subject_id)] = claim["claim_id"]

    return indexes


def _split_list_like(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [_text(item) for item in value if not _is_blank(item)]

    text = _text(value)
    if not text:
        return []

    parts = re.split(r"\n|;|\|", text)
    return [part.strip(" -•\t") for part in parts if part.strip(" -•\t")]


def _to_bool(value: Any) -> bool | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    if text in {"true", "yes", "y", "1"}:
        return True

    if text in {"false", "no", "n", "0"}:
        return False

    return None


def _text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _is_blank(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    if isinstance(value, list):
        return len(value) == 0

    return False


def _slug(value: Any) -> str:
    text = _text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text
