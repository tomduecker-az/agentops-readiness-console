from typing import Any

from workflow_core import (
    list_documents as core_list_documents,
    read_document as core_read_document,
    search_documents as core_search_documents,
)


def list_documents(workflow_id: str) -> list[dict[str, Any]]:
    """
    List registered documents available for a workflow.

    This tool only returns document metadata. It does not read full document content.
    """

    documents = core_list_documents(workflow_id)

    return [document.model_dump() for document in documents]


def read_document(workflow_id: str, document_id: str) -> dict[str, Any]:
    """
    Read the full content of a registered workflow document.

    The document must belong to the registered workflow packet.
    Arbitrary filesystem reads are not allowed.
    """

    document_content = core_read_document(
        workflow_id=workflow_id,
        document_id=document_id,
    )

    return document_content.model_dump()


def search_documents(workflow_id: str, query: str) -> list[dict[str, Any]]:
    """
    Search registered workflow documents using simple keyword search.

    This is intentionally not semantic search yet. The first goal is to prove
    controlled document access through an MCP boundary.
    """

    results = core_search_documents(
        workflow_id=workflow_id,
        query=query,
    )

    return [result.model_dump() for result in results]


def register_document_tools(mcp: Any) -> None:
    """
    Register document tools with a FastMCP server instance.

    Keeping registration separate from implementation lets us test the tool
    functions directly without starting an MCP server.
    """

    mcp.tool()(list_documents)
    mcp.tool()(read_document)
    mcp.tool()(search_documents)