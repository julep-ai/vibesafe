"""
End-to-end check using the mcp-use client against the Vibesafe MCP server.
"""

import json
import sys

import pytest
from mcp_use import MCPClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_use_client_can_call_status(clear_vibesafe_registry):
    """Spawn the server via mcp-use and call the status tool over MCP."""
    client = MCPClient.from_dict(
        {
            "mcpServers": {
                "vibesafe": {
                    "command": sys.executable,
                    "args": ["-c", "from vibesafe.mcp import MCPServer; MCPServer().run()"],
                }
            }
        }
    )

    try:
        await client.create_all_sessions()
        session = client.get_session("vibesafe")

        tools = await session.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "status" in tool_names

        result = await session.call_tool(name="status", arguments={})
        content = result.content[0]
        payload = json.loads(content.text)

        assert "version" in payload
        assert "units" in payload
        assert payload["units"] >= 0
    finally:
        await client.close_all_sessions()
