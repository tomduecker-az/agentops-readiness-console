from mcp.server.fastmcp import FastMCP

from mcp_servers.audit_server.app.tools import register_audit_tools


mcp = FastMCP("audit-server")

register_audit_tools(mcp)


if __name__ == "__main__":
    mcp.run()