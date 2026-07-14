from mcp.server.fastmcp import FastMCP

from mcp_servers.policy_server.app.tools import register_policy_tools


mcp = FastMCP("policy-server")

register_policy_tools(mcp)


if __name__ == "__main__":
    mcp.run()