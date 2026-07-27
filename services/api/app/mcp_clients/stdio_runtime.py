from __future__ import annotations
from contextlib import ExitStack
from typing import Any
import ast
import asyncio
import json
import os
import sys


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


MCP_SERVER_MODULES = {
    "document": "mcp_servers.document_server.app.server",
    "policy": "mcp_servers.policy_server.app.server",
}


class MCPRuntimeError(RuntimeError):
    pass


def call_mcp_tool(
    server: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    return asyncio.run(
        call_mcp_tool_async(
            server=server,
            tool_name=tool_name,
            arguments=arguments or {},
        )
    )


async def call_mcp_tool_async(
    server: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    if server not in MCP_SERVER_MODULES:
        raise MCPRuntimeError(f"Unknown MCP server: {server}")

    env = os.environ.copy()

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", MCP_SERVER_MODULES[server]],
        env=env,
    )

    with ExitStack() as stack:
        devnull = stack.enter_context(open(os.devnull, "w", encoding="utf-8"))

        async with stdio_client(server_params, errlog=devnull) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments or {})

    return _normalize_mcp_result(result)


def _normalize_mcp_result(result: Any) -> Any:
    """
    Normalize MCP CallToolResult values into plain Python objects.

    FastMCP may return structuredContent, structured_content, dict content,
    TextContent objects, JSON strings, or Python-literal strings depending on
    the tool/server/runtime path. This keeps the rest of the application from
    depending on those transport details.
    """

    if hasattr(result, "model_dump"):
        dumped = result.model_dump(mode="json")
    else:
        dumped = result

    if isinstance(dumped, dict):
        structured = dumped.get("structuredContent") or dumped.get("structured_content")
        if structured is not None:
            return _unwrap_result_container(structured)

        content = dumped.get("content", [])
        text_values = _extract_text_values(content)

        if len(text_values) == 1:
            return _unwrap_result_container(_parse_text_payload(text_values[0]))

        if text_values:
            return [_unwrap_result_container(_parse_text_payload(value)) for value in text_values]

        return _unwrap_result_container(dumped)

    if isinstance(dumped, str):
        return _unwrap_result_container(_parse_text_payload(dumped))

    return dumped


def _extract_text_values(content: Any) -> list[str]:
    if not isinstance(content, list):
        return []

    text_values = []

    for item in content:
        if isinstance(item, dict) and "text" in item:
            text_values.append(item["text"])
            continue

        if hasattr(item, "text"):
            text_values.append(item.text)
            continue

        if isinstance(item, str):
            text_values.append(item)

    return text_values

def _unwrap_result_container(value: Any) -> Any:
    """
    FastMCP commonly wraps returned tool values as {"result": <payload>}.
    The application wants the payload itself.
    """

    if isinstance(value, dict) and set(value.keys()) == {"result"}:
        return value["result"]

    return value

def _parse_text_payload(value: str) -> Any:
    """
    Parse tool text payloads into Python objects when possible.

    Prefer JSON, then support Python literal strings because some FastMCP paths
    serialize Python return values with repr-style single quotes.
    """

    value = value.strip()

    if not value:
        return value

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value