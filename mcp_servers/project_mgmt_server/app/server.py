from mcp.server.fastmcp import FastMCP

from mcp_servers.project_mgmt_server.app.tools import register_project_mgmt_tools


mcp = FastMCP("project-mgmt-server")

register_project_mgmt_tools(mcp)


if __name__ == "__main__":
    mcp.run()