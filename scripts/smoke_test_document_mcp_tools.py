from mcp_servers.document_server.app.tools import (
    list_documents,
    read_document,
    search_documents,
)


def main() -> None:
    workflow_id = "payment_reconciliation"

    print("\nDocuments:")
    documents = list_documents(workflow_id)
    for document in documents:
        print(f"- {document['document_id']}: {document['title']}")

    print("\nRead process_narrative:")
    process_narrative = read_document(workflow_id, "process_narrative")
    print(process_narrative["content"][:500])

    print("\nSearch for approval:")
    results = search_documents(workflow_id, "approval")
    for result in results:
        print(
            f"- {result['document_id']} line {result['line_number']}: "
            f"{result['snippet']}"
        )


if __name__ == "__main__":
    main()