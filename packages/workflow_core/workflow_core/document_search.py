from workflow_core.document_store import list_documents, read_document
from workflow_core.models import DocumentSearchResult


def search_documents(workflow_id: str, query: str) -> list[DocumentSearchResult]:
    normalized_query = query.lower().strip()

    if not normalized_query:
        return []

    results: list[DocumentSearchResult] = []

    for document in list_documents(workflow_id):
        document_content = read_document(workflow_id, document.document_id)

        for line_number, line in enumerate(document_content.content.splitlines(), start=1):
            if normalized_query in line.lower():
                results.append(
                    DocumentSearchResult(
                        workflow_id=workflow_id,
                        document_id=document.document_id,
                        title=document.title,
                        line_number=line_number,
                        snippet=line.strip(),
                    )
                )

    return results