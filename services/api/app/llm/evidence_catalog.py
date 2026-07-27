from __future__ import annotations

from typing import Any


def build_evidence_catalog(
    workflow_id: str,
    document_contents: list[dict[str, Any]],
    search_results: list[dict[str, Any]],
    data_classifications: dict[str, Any],
    required_controls: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence_items: list[dict[str, Any]] = []

    for index, document in enumerate(document_contents, start=1):
        document_id = document.get("document_id", f"document_{index}")
        title = document.get("title") or document.get("document_title") or document_id
        content = document.get("content", "")

        evidence_items.append(
            {
                "evidence_id": f"DOC-{index:03d}",
                "evidence_type": "workflow_document",
                "workflow_id": workflow_id,
                "source_id": document_id,
                "source_title": title,
                "summary": _summarize_text(content),
                "content": content,
            }
        )

    search_index = 1

    for search_group in search_results:
        query = search_group.get("query", "")
        results = search_group.get("results", [])

        for result in results[:5]:
            evidence_items.append(
                {
                    "evidence_id": f"SEARCH-{search_index:03d}",
                    "evidence_type": "document_search_result",
                    "workflow_id": workflow_id,
                    "source_id": result.get("document_id", "unknown"),
                    "source_title": result.get("document_title")
                    or result.get("title")
                    or result.get("document_id", "unknown"),
                    "query": query,
                    "summary": result.get("snippet")
                    or result.get("content")
                    or result.get("text")
                    or "",
                    "content": result,
                }
            )
            search_index += 1

    evidence_items.append(
        {
            "evidence_id": "POLICY-001",
            "evidence_type": "data_classification_batch",
            "workflow_id": workflow_id,
            "source_id": "policy_server.classify_data_elements",
            "source_title": "Batch data classification results",
            "summary": "Policy-server classifications for workflow data elements.",
            "content": data_classifications,
        }
    )

    evidence_items.append(
        {
            "evidence_id": "POLICY-002",
            "evidence_type": "required_controls_batch",
            "workflow_id": workflow_id,
            "source_id": "policy_server.get_required_controls_for_actions",
            "source_title": "Batch required-control lookup results",
            "summary": "Policy-server required-control lookup results for governed workflow actions.",
            "content": required_controls,
        }
    )

    return evidence_items


def _summarize_text(value: str, max_chars: int = 500) -> str:
    normalized = " ".join(str(value).split())

    if len(normalized) <= max_chars:
        return normalized

    return normalized[: max_chars - 3] + "..."