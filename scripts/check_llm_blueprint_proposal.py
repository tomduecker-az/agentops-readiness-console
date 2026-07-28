from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


_ALLOWED_TOOL_CAPABILITIES = {
    "workflow_document_search",
    "policy_lookup",
    "data_classification",
    "intake_validation",
    "approval_request",
    "workflow_record_update",
    "system_access_provisioning",
    "controlled_notification",
    "report_generation",
    "audit_event_write",
}

_WRITE_OPERATION_TYPES = {
    "write",
    "mixed",
    "external_communication",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate an exported LLM Blueprint Advisor proposal."
    )
    parser.add_argument("--path", required=True)

    args = parser.parse_args()

    path = Path(args.path)
    proposal = json.loads(path.read_text(encoding="utf-8"))

    issues = _validate_proposal(proposal)

    print(f"file: {path}")
    print(f"issue_count: {len(issues)}")

    for issue in issues:
        print(f"- {issue['severity']} {issue['code']} {issue['location']}: {issue['message']}")

    errors = [issue for issue in issues if issue["severity"] == "error"]

    if errors:
        raise AssertionError(f"{len(errors)} proposal validation errors found.")

    print("PASS")


def _validate_proposal(proposal: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    evidence_catalog = proposal.get("metadata", {}).get("evidence_catalog", [])
    valid_evidence_ids = {
        item.get("evidence_id")
        for item in evidence_catalog
        if isinstance(item, dict) and item.get("evidence_id")
    }

    if not valid_evidence_ids:
        issues.append(
            _issue(
                "error",
                "missing_evidence_catalog",
                "metadata.evidence_catalog",
                "LLM proposal must include an evidence catalog in metadata.",
            )
        )
        return issues

    issues.extend(_validate_section_refs(proposal, valid_evidence_ids))
    issues.extend(_validate_tools(proposal))
    issues.extend(_validate_steps(proposal))
    issues.extend(_validate_approval_gates(proposal))

    return issues


def _validate_section_refs(
    proposal: dict[str, Any],
    valid_evidence_ids: set[str],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    sections = [
        "step_level_autonomy_matrix",
        "tooling_blueprint",
        "human_approval_gates",
        "risk_control_summary",
        "implementation_roadmap",
    ]

    executive_refs = proposal.get("executive_summary", {}).get("evidence_references", [])
    issues.extend(
        _validate_refs(
            refs=executive_refs,
            valid_evidence_ids=valid_evidence_ids,
            location="executive_summary",
        )
    )

    for section in sections:
        for index, item in enumerate(proposal.get(section, [])):
            refs = item.get("evidence_references", [])
            issues.extend(
                _validate_refs(
                    refs=refs,
                    valid_evidence_ids=valid_evidence_ids,
                    location=f"{section}[{index}]",
                )
            )

    return issues


def _validate_refs(
    *,
    refs: Any,
    valid_evidence_ids: set[str],
    location: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if not isinstance(refs, list) or not refs:
        issues.append(
            _issue(
                "error",
                "missing_evidence_references",
                location,
                "Item must include at least one evidence reference.",
            )
        )
        return issues

    invalid_refs = sorted(str(ref) for ref in refs if ref not in valid_evidence_ids)

    if invalid_refs:
        issues.append(
            _issue(
                "error",
                "invalid_evidence_reference",
                location,
                f"Invalid evidence references: {invalid_refs}",
            )
        )

    return issues


def _validate_tools(proposal: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    for index, tool in enumerate(proposal.get("tooling_blueprint", [])):
        location = f"tooling_blueprint[{index}]"

        capability_name = tool.get("capability_name")
        operation_type = tool.get("operation_type")
        approval_required = tool.get("approval_required")
        audit_required = tool.get("audit_required")

        if capability_name not in _ALLOWED_TOOL_CAPABILITIES:
            issues.append(
                _issue(
                    "error",
                    "unsupported_tool_capability",
                    location,
                    f"Unsupported tool capability: {capability_name}",
                )
            )

        if operation_type in _WRITE_OPERATION_TYPES:
            if audit_required is not True:
                issues.append(
                    _issue(
                        "error",
                        "governed_tool_missing_audit",
                        location,
                        "Write, mixed, and external-communication tools must require audit.",
                    )
                )

            if capability_name != "audit_event_write" and approval_required is not True:
                issues.append(
                    _issue(
                        "error",
                        "governed_tool_missing_approval",
                        location,
                        "Write, mixed, and external-communication tools must require approval unless explicitly exempted.",
                    )
                )

    return issues


def _validate_steps(proposal: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    for index, step in enumerate(proposal.get("step_level_autonomy_matrix", [])):
        location = f"step_level_autonomy_matrix[{index}]"

        posture = step.get("recommended_posture")
        approval_required = step.get("approval_required")
        audit_required = step.get("audit_required")
        reviewer = str(step.get("required_human_reviewer") or "").strip()

        if posture == "approval_gated_action":
            if approval_required is not True:
                issues.append(
                    _issue(
                        "error",
                        "approval_gated_step_missing_approval",
                        location,
                        "Approval-gated steps must require approval.",
                    )
                )

            if audit_required is not True:
                issues.append(
                    _issue(
                        "error",
                        "approval_gated_step_missing_audit",
                        location,
                        "Approval-gated steps must require audit.",
                    )
                )

            if not reviewer:
                issues.append(
                    _issue(
                        "error",
                        "approval_gated_step_missing_reviewer",
                        location,
                        "Approval-gated steps must identify a human reviewer.",
                    )
                )

        if posture == "limited_automation_candidate":
            issues.append(
                _issue(
                    "warning",
                    "limited_automation_requires_review",
                    location,
                    "Limited automation candidates require additional production review.",
                )
            )

    return issues


def _validate_approval_gates(proposal: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if not proposal.get("human_approval_gates"):
        issues.append(
            _issue(
                "warning",
                "missing_approval_gates",
                "human_approval_gates",
                "No approval gates were proposed.",
            )
        )

    for index, gate in enumerate(proposal.get("human_approval_gates", [])):
        location = f"human_approval_gates[{index}]"

        if not str(gate.get("required_reviewer") or "").strip():
            issues.append(
                _issue(
                    "error",
                    "approval_gate_missing_reviewer",
                    location,
                    "Approval gate must identify a required reviewer.",
                )
            )

        if not gate.get("blocked_without_approval"):
            issues.append(
                _issue(
                    "warning",
                    "approval_gate_missing_blocked_actions",
                    location,
                    "Approval gate should identify blocked actions.",
                )
            )

    return issues


def _issue(
    severity: str,
    code: str,
    location: str,
    message: str,
) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "location": location,
        "message": message,
    }


if __name__ == "__main__":
    main()