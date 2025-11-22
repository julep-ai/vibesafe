"""
Integration-style tests for the MCP server using JSON-RPC over stdio.
"""

import io
import json
import sys

import pytest

from vibesafe.mcp import MCPServer


@pytest.mark.integration
def test_mcp_run_serves_initialize_and_tools(monkeypatch, clear_vibesafe_registry):
    """Drive MCPServer.run with JSON-RPC lines to mimic a real client."""
    server = MCPServer()

    # Simulated client messages
    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": {}},
    ]
    stdin = io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n")
    stdout = io.StringIO()

    # Patch stdio used inside MCPServer
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)

    server.run()

    responses = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]

    # Should emit one response per request, in order
    assert [resp["id"] for resp in responses] == [1, 2, 3]
    assert all(resp["jsonrpc"] == "2.0" for resp in responses)

    init_resp = responses[0]
    assert "result" in init_resp
    assert init_resp["result"]["serverInfo"]["name"] == "vibesafe"

    tools_resp = responses[1]
    assert "result" in tools_resp
    assert isinstance(tools_resp["result"].get("tools"), list)
    assert any(tool["name"] == "scan" for tool in tools_resp["result"]["tools"])

    ping_resp = responses[2]
    assert ping_resp["result"] == {}
