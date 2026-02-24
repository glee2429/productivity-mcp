"""Composition root — wires FastMCP, lifespan, and all tools (Pattern 5)."""

from mcp.server.fastmcp import FastMCP

from productivity_mcp.db import app_lifespan
from productivity_mcp.orchestrators import daily
from productivity_mcp.tools import calendar, notes, tasks

mcp = FastMCP("Productivity MCP", lifespan=app_lifespan)

# Register all tool modules
tasks.register_tools(mcp)
notes.register_tools(mcp)
calendar.register_tools(mcp)
daily.register_tools(mcp)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
