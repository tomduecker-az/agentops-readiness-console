# MCP-Enabled LLM Agent

## Purpose

The MCP-enabled LLM agent moves workflow analysis from a direct-prompt model call to a governed tool-mediated architecture.

The direct LLM shadow mode proved that a high-reasoning model can produce useful workflow analysis. The MCP-enabled agent tests whether that quality can be preserved while forcing workflow context access through controlled tools.

## Design Goal

The model should not receive unrestricted filesystem access or a blind full-document prompt.

Instead, the model receives a task and must retrieve workflow context through registered MCP tools.

## Current Tool Scope

The first MCP-enabled agent exposes only read-only and governance tools:

- document_server.list_documents
- document_server.read_document
- document_server.search_documents
- policy_server.classify_data
- policy_server.get_required_controls

The project-management write tool is not exposed to the MCP-enabled LLM agent.

## Execution Boundary

The model may:

- discover registered workflow documents
- read registered workflow packet documents
- search registered workflow packet documents
- request data classification
- request required controls
- produce advisory workflow analysis

The model may not:

- approve backlog items
- create GitHub issues
- execute write actions
- directly update Supabase
- bypass policy checks
- read arbitrary filesystem paths
- override human approval

## Runtime Pattern

```text
MCP-enabled LLM agent
  -> tool request
  -> application allowlist validation
  -> policy_server.check_tool_permission
  -> MCP server tool execution
  -> audit event persisted
  -> tool result returned to model
  -> structured advisory artifact persisted