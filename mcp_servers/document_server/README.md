# Document MCP Server

## Purpose

The Document MCP Server provides controlled read-only access to registered workflow documents.

It represents the document-access boundary for agentic workflow analysis.

## Tools

### list_documents

Lists registered document metadata for a workflow.

### read_document

Reads the full content of a specific registered document.

### search_documents

Performs simple keyword search across registered workflow documents.

## Security Boundary

This server does not expose arbitrary filesystem access.

Documents must be registered through `workflow_core` before they can be listed, read, or searched.

## Enterprise 

In a production enterprise system, this server could be replaced or extended with connectors to:

- SharePoint
- Confluence
- Google Drive
- Box
- ServiceNow knowledge base
- internal SOP repositories
- policy management systems

The MCP server should remain an adapter. Registry lookup, path safety, and document access rules should remain in shared domain logic or an approved registry service.