from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def build_packet_quality_review(
    *,
    packet_claim_graph: dict[str, Any],
    deterministic_review: dict[str, Any],
    adversarial_review: dict[str, Any],
) -> dict[str, Any]:
    deterministic_findings = deterministic_review.get("findings", [])
    advisory_findings = adversarial_review.get("advisory_findings", [])

    reconciled_findings = _build_reconciled_findings(
        deterministic_findings=deterministic_findings,
        advisory_findings=advisory_findings,
    )

    return {
        "artifact_type": "packet_quality_review",
        "schema_version": "packet_quality_review_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "workflow_id": packet_claim_graph.get("workflow_id"),
        "workflow_name": packet_claim_graph.get("workflow_name"),
        "review_verdict": adversarial_review.get("review_verdict", {}),
        "summary": _build_summary(
            deterministic_findings=deterministic_findings,
            advisory_findings=advisory_findings,
            reconciled_findings=reconciled_findings,
        ),
        "reconciled_critical_findings": reconciled_findings,
        "deterministic_findings": deterministic_findings,
        "advisory_findings": advisory_findings,
        "client_report_guidance": adversarial_review.get("client_report_guidance", {}),
        "metadata": {
            "input_claim_count": packet_claim_graph.get("metadata", {}).get("claim_count"),
            "deterministic_finding_count": len(deterministic_findings),
            "advisory_finding_count": len(advisory_findings),
            "reconciled_finding_count": len(reconciled_findings),
            "deterministic_review_schema_version": deterministic_review.get("schema_version"),
            "adversarial_review_schema_version": "packet_adversarial_review_v1",
        },
    }


def _build_reconciled_findings(
    *,
    deterministic_findings: list[dict[str, Any]],
    advisory_findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reconciled: list[dict[str, Any]] = []

    for finding in advisory_findings:
        severity = _normalized_severity(finding.get("severity"))

        if severity not in {"critical", "high"}:
            continue

        reconciled.append(
            {
                "finding_id": finding.get("finding_id"),
                "source": "adversarial_review",
                "severity": severity,
                "finding_type": finding.get("finding_type"),
                "category": finding.get("category"),
                "title": finding.get("title"),
                "evidence": finding.get("evidence", []),
                "packet_claim_challenged": finding.get("packet_claim_challenged"),
                "implication": finding.get("ai_readiness_implication"),
                "recommendation": finding.get("recommended_remediation"),
                "confidence": finding.get("confidence"),
                "supporting_deterministic_finding_ids": finding.get(
                    "deterministic_supporting_finding_ids", []
                ),
            }
        )

    supported_deterministic_ids = {
        item
        for finding in advisory_findings
        for item in finding.get("deterministic_supporting_finding_ids", [])
    }

    for finding in deterministic_findings:
        severity = _normalized_severity(finding.get("severity"))
        finding_id = finding.get("finding_id")

        if severity not in {"critical", "high"}:
            continue

        if finding_id in supported_deterministic_ids:
            continue

        reconciled.append(
            {
                "finding_id": finding_id,
                "source": "deterministic_review",
                "severity": severity,
                "finding_type": "proven_consistency_issue",
                "category": finding.get("category"),
                "title": finding.get("title"),
                "evidence": finding.get("evidence", {}),
                "packet_claim_challenged": "Structured packet claims are internally inconsistent or unresolved.",
                "implication": finding.get("implication"),
                "recommendation": finding.get("recommendation"),
                "confidence": finding.get("confidence"),
                "supporting_deterministic_finding_ids": [finding_id],
            }
        )

    reconciled.sort(
        key=lambda item: (
            -SEVERITY_RANK.get(_normalized_severity(item.get("severity")), 0),
            str(item.get("finding_id") or ""),
        )
    )

    return reconciled


def _build_summary(
    *,
    deterministic_findings: list[dict[str, Any]],
    advisory_findings: list[dict[str, Any]],
    reconciled_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    all_findings = deterministic_findings + advisory_findings

    by_severity: dict[str, int] = {}
    by_source = {
        "deterministic_review": len(deterministic_findings),
        "adversarial_review": len(advisory_findings),
    }

    for finding in all_findings:
        severity = _normalized_severity(finding.get("severity"))
        by_severity[severity] = by_severity.get(severity, 0) + 1

    return {
        "total_findings": len(all_findings),
        "by_source": by_source,
        "by_severity": by_severity,
        "reconciled_critical_or_high_count": len(reconciled_findings),
        "top_reconciled_findings": [
            {
                "finding_id": finding.get("finding_id"),
                "source": finding.get("source"),
                "severity": finding.get("severity"),
                "finding_type": finding.get("finding_type"),
                "title": finding.get("title"),
            }
            for finding in reconciled_findings[:10]
        ],
    }


def _normalized_severity(value: Any) -> str:
    text = str(value or "").strip().lower()

    if text in SEVERITY_RANK:
        return text

    return "low"
