from __future__ import annotations

import itertools
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class PacketQualityFinding:
    finding_id: str
    rule_id: str
    rule_type: str
    category: str
    severity: str
    title: str
    evidence: dict[str, Any]
    implication: str
    recommendation: str
    confidence: str


SENSITIVE_DATA_CATEGORIES = {
    "pii",
    "phi",
    "confidential",
    "restricted",
    "regulated",
    "privileged",
    "sensitive",
}

NON_OPERATIONAL_SOURCE_SYSTEM_KEYS = {
    "",
    "sample_data",
    "sample_records",
    "example_data",
    "test_data",
    "seed_data",
    "derived",
    "calculated",
    "not_specified",
    "not_applicable",
    "n_a",
    "na",
    "none",
    "null",
}


def _is_non_operational_source_system(source_system: Any) -> bool:
    return _slug(source_system) in NON_OPERATIONAL_SOURCE_SYSTEM_KEYS

def run_packet_quality_rules(packet_claim_graph: dict[str, Any]) -> dict[str, Any]:
    claims = packet_claim_graph.get("claims", [])
    indexes = packet_claim_graph.get("indexes", {})

    findings: list[PacketQualityFinding] = []

    findings.extend(_rule_step_data_references_declared(claims, indexes))
    findings.extend(_rule_data_dictionary_step_references_declared(claims, indexes))
    findings.extend(_rule_data_dictionary_usage_reflected_in_step_data_used(claims, indexes))
    findings.extend(_rule_step_systems_declared(claims, indexes))
    findings.extend(_rule_data_source_systems_declared(claims, indexes))
    findings.extend(_rule_controls_apply_to_existing_steps(claims, indexes))
    findings.extend(_rule_step_owners_resolve_to_participants(claims, indexes))
    findings.extend(_rule_control_approvers_resolve_to_participants(claims, indexes))
    findings.extend(_rule_target_system_owners_resolve_to_participants(claims, indexes))
    findings.extend(_rule_declared_participants_have_operational_use(claims))
    findings.extend(_rule_declared_target_systems_have_operational_use(claims))
    findings.extend(_rule_approval_required_has_role(claims))
    findings.extend(_rule_sensitive_data_not_allowed_without_redaction(claims))
    findings.extend(_rule_similar_fields_have_consistent_handling(claims))
    findings.extend(_rule_sample_record_fields_declared(claims, indexes))
    findings.extend(_rule_sample_record_segregation_of_duties(claims))

    return {
        "artifact_type": "packet_quality_deterministic_review",
        "schema_version": "packet_quality_deterministic_review_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "workflow_id": packet_claim_graph.get("workflow_id"),
        "workflow_name": packet_claim_graph.get("workflow_name"),
        "summary": _summarize_findings(findings),
        "findings": [asdict(finding) for finding in findings],
        "metadata": {
            "finding_count": len(findings),
            "input_claim_count": packet_claim_graph.get("metadata", {}).get("claim_count"),
            "rule_count": 16,
        },
    }


def _rule_step_data_references_declared(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    declared_fields = set(indexes.get("data_fields", {}).keys())
    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "step_data_usage_claim"):
        field_name = claim["properties"].get("field_name")
        step_id = claim["properties"].get("step_id")
        field_key = _slug(field_name)

        if field_key and field_key not in declared_fields:
            findings.append(
                _finding(
                    rule_id="GRAPH-DATA-001",
                    rule_type="cross_sheet_reference",
                    category="missing_data_dictionary_reference",
                    severity="high",
                    title="Workflow step uses data field missing from Data Dictionary",
                    evidence={
                        "step_id": step_id,
                        "field_name": field_name,
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The workflow relies on a data field that has no declared classification, "
                        "redaction rule, model-context rule, owner, or allowed values."
                    ),
                    recommendation=(
                        "Add this field to the Data Dictionary before using it for assessment, "
                        "model context, or automation design."
                    ),
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_data_dictionary_step_references_declared(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    declared_steps = set(indexes.get("workflow_steps", {}).keys())
    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "data_step_usage_claim"):
        field_name = claim["properties"].get("field_name")
        step_id = claim["properties"].get("step_id")
        step_key = _slug(step_id)

        if step_key and step_key not in declared_steps:
            findings.append(
                _finding(
                    rule_id="GRAPH-DATA-002",
                    rule_type="cross_sheet_reference",
                    category="invalid_data_step_mapping",
                    severity="medium",
                    title="Data Dictionary references a workflow step that does not exist",
                    evidence={
                        "field_name": field_name,
                        "step_id": step_id,
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The packet claims this field is used in a workflow step that is not present "
                        "in the Workflow Steps sheet."
                    ),
                    recommendation="Correct the step reference or add the missing workflow step.",
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_data_dictionary_usage_reflected_in_step_data_used(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    declared_steps = set(indexes.get("workflow_steps", {}).keys())

    step_data_pairs = {
        (
            _slug(claim["properties"].get("step_id")),
            _slug(claim["properties"].get("field_name")),
        )
        for claim in _claims_by_type(claims, "step_data_usage_claim")
    }

    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "data_step_usage_claim"):
        field_name = claim["properties"].get("field_name")
        step_id = claim["properties"].get("step_id")

        field_key = _slug(field_name)
        step_key = _slug(step_id)

        if not field_key or not step_key:
            continue

        # Avoid duplicating the existing "Data Dictionary references a workflow step
        # that does not exist" finding.
        if step_key not in declared_steps:
            continue

        if (step_key, field_key) in step_data_pairs:
            continue

        severity = _data_usage_mismatch_severity(field_name)

        findings.append(
            _finding(
                rule_id="GRAPH-DATA-004",
                rule_type="cross_sheet_reference",
                category="data_dictionary_usage_not_reflected_in_step",
                severity=severity,
                title="Data Dictionary field is mapped to a workflow step that does not list it as used data",
                evidence={
                    "field_name": field_name,
                    "step_id": step_id,
                    "source_claim_id": claim["claim_id"],
                    "source": claim["source"],
                },
                implication=(
                    "The Data Dictionary says this field is used by a workflow step, "
                    "but the Workflow Steps sheet does not list the field in that step's data_used values. "
                    "This weakens traceability and may indicate that a control input, flag, threshold, "
                    "or decision signal has no actual workflow consumer."
                ),
                recommendation=(
                    "Either add the field to the workflow step's data_used list, correct the Data Dictionary "
                    "used_in_steps mapping, or document why the field is retained but not consumed by the step."
                ),
                confidence="high",
                sequence=len(findings) + 1,
            )
        )

    return findings

def _rule_step_systems_declared(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    declared_systems = set(indexes.get("target_systems", {}).keys())
    declared_systems.update(indexes.get("overview_systems", {}).keys())

    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "step_system_usage_claim"):
        system_name = claim["properties"].get("system_name")
        step_id = claim["properties"].get("step_id")
        system_key = _slug(system_name)

        if system_key and system_key not in declared_systems:
            findings.append(
                _finding(
                    rule_id="GRAPH-SYS-001",
                    rule_type="cross_sheet_reference",
                    category="undeclared_system",
                    severity="medium",
                    title="Workflow step uses a system that is not declared",
                    evidence={
                        "step_id": step_id,
                        "system_name": system_name,
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The workflow depends on a system with no declared owner, access method, "
                        "read/write posture, or integration boundary."
                    ),
                    recommendation=(
                        "Add this system to Target Systems or Systems Involved before designing AI "
                        "support around it."
                    ),
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_data_source_systems_declared(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    declared_systems = set(indexes.get("target_systems", {}).keys())
    declared_systems.update(indexes.get("overview_systems", {}).keys())

    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "data_source_system_claim"):
        source_system = claim["properties"].get("source_system")
        field_name = claim["properties"].get("field_name")
        system_key = _slug(source_system)
        if _is_non_operational_source_system(source_system):
            continue

        if system_key and system_key not in declared_systems:
            findings.append(
                _finding(
                    rule_id="GRAPH-SYS-002",
                    rule_type="cross_sheet_reference",
                    category="undeclared_data_source_system",
                    severity="medium",
                    title="Data field references a source system that is not declared",
                    evidence={
                        "field_name": field_name,
                        "source_system": source_system,
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "A data field is sourced from a system that lacks declared ownership, access, "
                        "and integration constraints in the packet."
                    ),
                    recommendation="Declare the source system in Target Systems or Systems Involved.",
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_controls_apply_to_existing_steps(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    declared_steps = set(indexes.get("workflow_steps", {}).keys())
    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "control_step_application_claim"):
        control_id = claim["properties"].get("control_id")
        step_id = claim["properties"].get("step_id")
        step_key = _slug(step_id)

        if step_key and step_key not in declared_steps:
            findings.append(
                _finding(
                    rule_id="GRAPH-CTRL-001",
                    rule_type="cross_sheet_reference",
                    category="invalid_control_step_reference",
                    severity="high",
                    title="Policy control applies to a workflow step that does not exist",
                    evidence={
                        "control_id": control_id,
                        "step_id": step_id,
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The packet claims a control applies to a missing step, so the control may not "
                        "be enforceable where the workflow actually operates."
                    ),
                    recommendation="Correct the control's step mapping or add the missing workflow step.",
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_step_owners_resolve_to_participants(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    participants = set(indexes.get("participants", {}).keys())
    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "step_owner_claim"):
        owner_role = claim["properties"].get("owner_role")
        step_id = claim["properties"].get("step_id")

        if owner_role and not _resolves_to_known_role_strict(owner_role, participants):
            findings.append(
                _finding(
                    rule_id="GRAPH-ROLE-001",
                    rule_type="role_resolution",
                    category="unresolved_step_owner",
                    severity="medium",
                    title="Workflow step owner does not resolve to a declared participant",
                    evidence={
                        "step_id": step_id,
                        "owner_role": owner_role,
                        "declared_participant_keys": sorted(participants),
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The step may not have a clearly accountable human owner. This weakens "
                        "human-in-the-loop design, escalation, and auditability."
                    ),
                    recommendation=(
                        "Use a role that appears in Primary Participants, or add the missing role to "
                        "Primary Participants."
                    ),
                    confidence="medium",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_control_approvers_resolve_to_participants(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    participants = set(indexes.get("participants", {}).keys())
    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "control_approval_role_claim"):
        approval_required = claim["properties"].get("approval_required")
        approval_role = claim["properties"].get("approval_role")
        control_id = claim["properties"].get("control_id")

        if approval_required is True and approval_role and not _resolves_to_known_role_strict(approval_role, participants):
            findings.append(
                _finding(
                    rule_id="GRAPH-ROLE-002",
                    rule_type="role_resolution",
                    category="unresolved_control_approver",
                    severity="high",
                    title="Approval-required control uses an approver role not declared as a participant",
                    evidence={
                        "control_id": control_id,
                        "approval_role": approval_role,
                        "declared_participant_keys": sorted(participants),
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "An approval control cannot be automated, audited, or enforced reliably if "
                        "the approver role is not a declared participant in the workflow."
                    ),
                    recommendation=(
                        "Replace the approval role with a declared accountable role or add the role "
                        "to Primary Participants."
                    ),
                    confidence="medium",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_approval_required_has_role(
    claims: list[dict[str, Any]],
) -> list[PacketQualityFinding]:
    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "policy_control_claim"):
        props = claim["properties"]
        approval_required = props.get("approval_required")
        approval_role = props.get("approval_role")

        if approval_required is True and not _text(approval_role):
            findings.append(
                _finding(
                    rule_id="GRAPH-CTRL-002",
                    rule_type="control_completeness",
                    category="missing_approval_role",
                    severity="high",
                    title="Control requires approval but no approver role is provided",
                    evidence={
                        "control_id": props.get("control_id"),
                        "control_name": props.get("control_name"),
                        "approval_required": approval_required,
                        "approval_role": approval_role,
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The packet defines a human approval requirement but does not identify who "
                        "can satisfy it."
                    ),
                    recommendation="Name the accountable approval role before treating this as a control.",
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_sensitive_data_not_allowed_without_redaction(
    claims: list[dict[str, Any]],
) -> list[PacketQualityFinding]:
    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "data_handling_claim"):
        props = claim["properties"]
        data_category = _text(props.get("data_category"))
        model_context_allowed = props.get("model_context_allowed")
        redaction_required = props.get("redaction_required")

        if (
            _slug(data_category) in SENSITIVE_DATA_CATEGORIES
            and model_context_allowed is True
            and redaction_required is False
        ):
            findings.append(
                _finding(
                    rule_id="GRAPH-DATA-003",
                    rule_type="data_governance_consistency",
                    category="sensitive_data_allowed_without_redaction",
                    severity="critical",
                    title="Sensitive data is allowed into model context without redaction",
                    evidence={
                        "field_name": props.get("field_name"),
                        "business_meaning": props.get("business_meaning"),
                        "data_category": data_category,
                        "model_context_allowed": model_context_allowed,
                        "redaction_required": redaction_required,
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The packet's own structured classification conflicts with its model-context "
                        "handling. This field should not be treated as model-safe without explicit "
                        "data-owner review."
                    ),
                    recommendation=(
                        "Block the field from model context, require redaction, or define a safe "
                        "transformation before using it in an LLM workflow."
                    ),
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings


def _rule_similar_fields_have_consistent_handling(
    claims: list[dict[str, Any]],
) -> list[PacketQualityFinding]:
    data_claims = _claims_by_type(claims, "data_handling_claim")
    findings: list[PacketQualityFinding] = []

    for left, right in itertools.combinations(data_claims, 2):
        left_props = left["properties"]
        right_props = right["properties"]

        left_category = _slug(left_props.get("data_category"))
        right_category = _slug(right_props.get("data_category"))

        if not left_category or left_category != right_category:
            continue

        if not _same_source_or_business_family(left_props, right_props):
            continue

        left_handling = (
            left_props.get("model_context_allowed"),
            left_props.get("redaction_required"),
        )
        right_handling = (
            right_props.get("model_context_allowed"),
            right_props.get("redaction_required"),
        )

        if left_handling == right_handling:
            continue

        similarity = _token_similarity(
            left_props.get("field_name"),
            right_props.get("field_name"),
        )

        if similarity < 0.34:
            continue

        findings.append(
            _finding(
                rule_id="GRAPH-DATA-004",
                rule_type="data_governance_consistency",
                category="inconsistent_similar_field_handling",
                severity="high",
                title="Similar fields with the same classification have inconsistent model/redaction handling",
                evidence={
                    "left_field": {
                        "field_name": left_props.get("field_name"),
                        "business_meaning": left_props.get("business_meaning"),
                        "source_system": left_props.get("source_system"),
                        "data_category": left_props.get("data_category"),
                        "model_context_allowed": left_props.get("model_context_allowed"),
                        "redaction_required": left_props.get("redaction_required"),
                        "source_claim_id": left["claim_id"],
                        "source": left["source"],
                    },
                    "right_field": {
                        "field_name": right_props.get("field_name"),
                        "business_meaning": right_props.get("business_meaning"),
                        "source_system": right_props.get("source_system"),
                        "data_category": right_props.get("data_category"),
                        "model_context_allowed": right_props.get("model_context_allowed"),
                        "redaction_required": right_props.get("redaction_required"),
                        "source_claim_id": right["claim_id"],
                        "source": right["source"],
                    },
                    "field_name_similarity": similarity,
                },
                implication=(
                    "The packet may contain guessed or inconsistent handling rules. Similar fields "
                    "with the same classification should not have materially different model-context "
                    "or redaction treatment without a stated rationale."
                ),
                recommendation=(
                    "Require a data owner to reconcile these handling rules before relying on the "
                    "allowlist."
                ),
                confidence="medium",
                sequence=len(findings) + 1,
            )
        )

    return findings


def _rule_sample_record_fields_declared(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    declared_fields = set(indexes.get("data_fields", {}).keys())
    findings: list[PacketQualityFinding] = []

    ignored_sample_fields = {
        "record_id",
    }

    for claim in _claims_by_type(claims, "sample_record_claim"):
        record_id = claim["subject_id"]
        properties = claim["properties"]

        for field_name, value in properties.items():
            if _slug(field_name) in ignored_sample_fields:
                continue

            if _is_blank(value):
                continue

            if _slug(field_name) not in declared_fields:
                findings.append(
                    _finding(
                        rule_id="GRAPH-RECORD-001",
                        rule_type="sample_record_consistency",
                        category="sample_record_field_missing_from_data_dictionary",
                        severity="medium",
                        title="Sample record contains populated field missing from Data Dictionary",
                        evidence={
                            "record_id": record_id,
                            "field_name": field_name,
                            "value_present": True,
                            "source_claim_id": claim["claim_id"],
                            "source": claim["source"],
                        },
                        implication=(
                            "The sample data contains a field that lacks declared classification, "
                            "redaction, and model-context handling."
                        ),
                        recommendation="Add this field to the Data Dictionary or remove it from sample records.",
                        confidence="high",
                        sequence=len(findings) + 1,
                    )
                )

    return findings

def _rule_target_system_owners_resolve_to_participants(
    claims: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> list[PacketQualityFinding]:
    participants = set(indexes.get("participants", {}).keys())
    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "target_system_claim"):
        props = claim.get("properties", {})
        system_name = props.get("system_name") or claim.get("subject_id")
        owner_role = props.get("owner_role")

        if owner_role and not _resolves_to_known_role_strict(owner_role, participants):
            findings.append(
                _finding(
                    rule_id="GRAPH-ROLE-003",
                    rule_type="cross_sheet_reference",
                    category="unresolved_target_system_owner",
                    severity="medium",
                    title="Target system owner does not resolve to a declared participant",
                    evidence={
                        "system_name": system_name,
                        "owner_role": owner_role,
                        "declared_participant_keys": sorted(participants),
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The packet declares a system owner that is not part of the declared participant model. "
                        "This weakens accountability for source access, integration boundaries, data quality, "
                        "and operational ownership."
                    ),
                    recommendation=(
                        "Use a role that appears in Primary Participants, or add the missing system-owner role "
                        "to Primary Participants with its responsibilities clearly defined."
                    ),
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings

def _rule_declared_participants_have_operational_use(
    claims: list[dict[str, Any]],
) -> list[PacketQualityFinding]:
    used_role_keys: set[str] = set()

    operational_claim_types = {
        "step_owner_role_claim",
        "control_approval_role_claim",
        "target_system_claim",
        "sample_record_claim",
    }

    for claim in claims:
        if claim.get("claim_type") not in operational_claim_types:
            continue

        props = claim.get("properties", {})

        for _field_name, role_value in _role_reference_values_from_properties(props):
            used_role_keys.add(_slug(role_value))

    used_role_keys.discard("")

    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "participant_claim"):
        props = claim.get("properties", {})
        role_name = props.get("role_name")
        role_key = _slug(role_name or claim.get("subject_id"))

        if not role_key:
            continue

        if role_key in used_role_keys:
            continue

        findings.append(
            _finding(
                rule_id="GRAPH-ROLE-004",
                rule_type="reverse_reference",
                category="declared_participant_without_operational_use",
                severity="low",
                title="Declared participant has no explicit operational responsibility in the packet",
                evidence={
                    "role_name": role_name,
                    "participant_key": role_key,
                    "used_role_keys": sorted(used_role_keys),
                    "source_claim_id": claim["claim_id"],
                    "source": claim["source"],
                },
                implication=(
                    "The role is listed as a primary participant, but the packet does not show it owning a step, "
                    "approving a control, owning a system, or appearing as a sample-record actor. This may mean "
                    "the workflow documentation is incomplete, the role is contextual only, or the participant "
                    "list overstates the operating model."
                ),
                recommendation=(
                    "Either assign the participant explicit workflow responsibilities, document its review or "
                    "notification role, or remove it from Primary Participants if it is not part of the operating workflow."
                ),
                confidence="high",
                sequence=len(findings) + 1,
            )
        )

    return findings

def _rule_declared_target_systems_have_operational_use(
    claims: list[dict[str, Any]],
) -> list[PacketQualityFinding]:
    used_system_keys: set[str] = set()

    for claim in _claims_by_type(claims, "step_system_usage_claim"):
        used_system_keys.add(_slug(claim.get("properties", {}).get("system_name")))

    for claim in _claims_by_type(claims, "data_source_system_claim"):
        source_system = claim.get("properties", {}).get("source_system")
        if _is_non_operational_source_system(source_system):
            continue
        used_system_keys.add(_slug(source_system))

    used_system_keys.discard("")

    findings: list[PacketQualityFinding] = []

    for claim in _claims_by_type(claims, "target_system_claim"):
        props = claim.get("properties", {})
        system_name = props.get("system_name")
        system_key = _slug(system_name or claim.get("subject_id"))

        if not system_key:
            continue

        if system_key in used_system_keys:
            continue

        findings.append(
            _finding(
                rule_id="GRAPH-SYS-003",
                rule_type="reverse_reference",
                category="declared_target_system_without_operational_use",
                severity="medium",
                title="Declared target system has no explicit workflow or data-source use",
                evidence={
                    "system_name": system_name,
                    "system_key": system_key,
                    "used_system_keys": sorted(used_system_keys),
                    "source_claim_id": claim["claim_id"],
                    "source": claim["source"],
                },
                implication=(
                    "The system is declared in the target-system inventory, but the packet does not show it being "
                    "used by a workflow step or as a data source. This may indicate an incomplete workflow map, "
                    "an out-of-scope system, or a missing integration/data-lineage dependency."
                ),
                recommendation=(
                    "Either reference the system in the relevant workflow steps or data fields, document why it is "
                    "contextual or future-state only, or remove it from the target-system inventory for this assessment."
                ),
                confidence="high",
                sequence=len(findings) + 1,
            )
        )

    return findings

def _rule_sample_record_segregation_of_duties(
    claims: list[dict[str, Any]],
) -> list[PacketQualityFinding]:
    findings: list[PacketQualityFinding] = []

    sod_field_pairs = [
        ("preparer_role", "approver_role"),
        ("preparer_user", "approver_user"),
        ("prepared_by", "approved_by"),
        ("posted_by", "approved_by"),
        ("submitter_role", "approver_role"),
        ("requester_role", "approver_role"),
    ]

    for claim in _claims_by_type(claims, "sample_record_claim"):
        props = claim.get("properties", {})
        record_id = props.get("record_id") or claim.get("subject_id")

        for left_field, right_field in sod_field_pairs:
            left_value = _text(props.get(left_field))
            right_value = _text(props.get(right_field))

            if not left_value or not right_value:
                continue

            if _slug(left_value) != _slug(right_value):
                continue

            findings.append(
                _finding(
                    rule_id="GRAPH-SAMPLE-002",
                    rule_type="sample_record_consistency",
                    category="sample_segregation_of_duties_conflict",
                    severity="high",
                    title="Sample record uses the same role or person for preparation and approval",
                    evidence={
                        "record_id": record_id,
                        "left_field": left_field,
                        "left_value": left_value,
                        "right_field": right_field,
                        "right_value": right_value,
                        "source_claim_id": claim["claim_id"],
                        "source": claim["source"],
                    },
                    implication=(
                        "The sample record does not demonstrate segregation between preparation "
                        "and approval. In a controlled workflow, this may indicate that the packet "
                        "cannot prove independent review or that historical data contains a control failure."
                    ),
                    recommendation=(
                        "Clarify whether the values represent roles or specific individuals. Capture "
                        "identity-level preparer and approver evidence, enforce independence where required, "
                        "and correct or explain the sample record before using it as ground truth."
                    ),
                    confidence="high",
                    sequence=len(findings) + 1,
                )
            )

    return findings

def _finding(
    *,
    rule_id: str,
    rule_type: str,
    category: str,
    severity: str,
    title: str,
    evidence: dict[str, Any],
    implication: str,
    recommendation: str,
    confidence: str,
    sequence: int,
) -> PacketQualityFinding:
    return PacketQualityFinding(
        finding_id=f"{rule_id}-{sequence:03d}",
        rule_id=rule_id,
        rule_type=rule_type,
        category=category,
        severity=severity,
        title=title,
        evidence=evidence,
        implication=implication,
        recommendation=recommendation,
        confidence=confidence,
    )


def _role_reference_values_from_properties(
    properties: dict[str, Any],
) -> list[tuple[str, str]]:
    role_references: list[tuple[str, str]] = []

    for field_name, value in properties.items():
        field_key = _slug(field_name)

        if field_key != "role" and not field_key.endswith("_role"):
            continue

        role_value = _text(value)
        if not role_value:
            continue

        role_references.append((field_name, role_value))

    return role_references

def _claims_by_type(claims: list[dict[str, Any]], claim_type: str) -> list[dict[str, Any]]:
    return [claim for claim in claims if claim.get("claim_type") == claim_type]

def _resolves_to_known_role_strict(role: str, participant_keys: set[str]) -> bool:
    role_key = _slug(role)
    if not role_key:
        return False

    return role_key in participant_keys

def _resolves_to_known_role(role: str, participant_keys: set[str]) -> bool:
    role_key = _slug(role)

    if not role_key:
        return False

    if role_key in participant_keys:
        return True

    role_tokens = set(role_key.split("_"))

    for participant_key in participant_keys:
        participant_tokens = set(participant_key.split("_"))

        if role_tokens and role_tokens.issubset(participant_tokens):
            return True

        if participant_tokens and participant_tokens.issubset(role_tokens):
            return True

        if _token_jaccard(role_tokens, participant_tokens) >= 0.67:
            return True

    return False

def _data_usage_mismatch_severity(field_name: Any) -> str:
    return "medium"

def _same_source_or_business_family(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_source = _slug(left.get("source_system"))
    right_source = _slug(right.get("source_system"))

    if left_source and right_source and left_source == right_source:
        return True

    left_name = _slug(left.get("field_name"))
    right_name = _slug(right.get("field_name"))

    left_prefix = "_".join(left_name.split("_")[:2])
    right_prefix = "_".join(right_name.split("_")[:2])

    return bool(left_prefix and right_prefix and left_prefix == right_prefix)


def _token_similarity(left: Any, right: Any) -> float:
    left_tokens = set(_slug(left).split("_")) - {""}
    right_tokens = set(_slug(right).split("_")) - {""}

    return _token_jaccard(left_tokens, right_tokens)


def _token_jaccard(left_tokens: set[str], right_tokens: set[str]) -> float:
    if not left_tokens or not right_tokens:
        return 0.0

    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _summarize_findings(findings: list[PacketQualityFinding]) -> dict[str, Any]:
    by_severity: dict[str, int] = {}
    by_rule_id: dict[str, int] = {}

    for finding in findings:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_rule_id[finding.rule_id] = by_rule_id.get(finding.rule_id, 0) + 1

    critical_high = [
        finding for finding in findings if finding.severity in {"critical", "high"}
    ]

    return {
        "finding_count": len(findings),
        "by_severity": by_severity,
        "by_rule_id": by_rule_id,
        "critical_or_high_count": len(critical_high),
        "top_findings": [
            {
                "finding_id": finding.finding_id,
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "title": finding.title,
            }
            for finding in critical_high[:8]
        ],
    }


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
