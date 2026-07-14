from mcp.server.fastmcp import FastMCP

from mcp_servers.document_server.app.tools import register_document_tools


mcp = FastMCP("document-server")

register_document_tools(mcp)


if __name__ == "__main__":
    mcp.run()