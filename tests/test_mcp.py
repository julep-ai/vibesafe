"""
Tests for vibesafe.mcp module.
"""

import json

import pytest

from vibesafe import VibeCoded, vibesafe
from vibesafe.mcp import MCPServer


def _parse_single_response(output: str) -> dict:
    """Parse a single JSON-RPC response line from captured stdout."""
    lines = [line for line in output.strip().splitlines() if line]
    assert len(lines) == 1, f"Expected single response line, got {len(lines)}: {lines}"
    return json.loads(lines[0])


class TestMCPServer:
    """Tests for MCPServer class."""

    def test_initialization(self):
        """Test MCP server initialization."""
        server = MCPServer()
        assert "scan" in server.tools
        assert "compile" in server.tools
        assert "test" in server.tools
        assert "save" in server.tools
        assert "status" in server.tools

    def test_handle_request_unknown_method(self, capsys):
        """Test handling unknown method."""
        server = MCPServer()
        request = {"jsonrpc": "2.0", "method": "unknown_method", "id": 1}
        server.handle_request(request)

        response = _parse_single_response(capsys.readouterr().out)
        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    def test_handle_request_scan(self, clear_vibesafe_registry, capsys):
        """Test handling scan request."""

        @vibesafe
        def test_func(x: int) -> int:
            """Test."""
            raise VibeCoded()

        server = MCPServer()
        request = {"jsonrpc": "2.0", "method": "scan", "params": {}, "id": 1}
        server.handle_request(request)

        response = _parse_single_response(capsys.readouterr().out)
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "units" in response["result"]
        assert "count" in response["result"]

    def test_handle_request_status(self, capsys):
        """Test handling status request."""
        server = MCPServer()
        request = {"jsonrpc": "2.0", "method": "status", "params": {}, "id": 1}
        server.handle_request(request)

        response = _parse_single_response(capsys.readouterr().out)
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "version" in response["result"]
        assert "units" in response["result"]

    def test_handle_request_with_error(self, mocker, capsys):
        """Test handling request that raises error."""
        server = MCPServer()

        # Mock scan tool to raise error
        def raise_error(params):
            raise RuntimeError("Test error")

        server.tools["scan"] = raise_error

        request = {"jsonrpc": "2.0", "method": "scan", "params": {}, "id": 1}
        server.handle_request(request)

        response = _parse_single_response(capsys.readouterr().out)
        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == -32000
        assert "Test error" in response["error"]["message"]

    def test_scan_method(self, clear_vibesafe_registry):
        """Test scan method."""

        @vibesafe
        def func1(x: int) -> int:
            raise VibeCoded()

        @vibesafe
        def func2(y: str) -> str:
            raise VibeCoded()

        server = MCPServer()
        result = server.scan({})

        assert "units" in result
        assert "count" in result
        assert result["count"] >= 2

    def test_compile_method_no_target(self):
        """Test compile method without target."""
        server = MCPServer()
        with pytest.raises(ValueError, match="target parameter required"):
            server.compile({})

    def test_test_method_no_target(self):
        """Test test method without target."""
        server = MCPServer()
        result = server.test({})
        assert "results" in result  # Tests all units

    def test_save_method_no_target(self):
        """Test save method without target."""
        server = MCPServer()
        result = server.save({})
        # Should test all units
        assert "success" in result

    def test_status_method(self):
        """Test status method."""
        server = MCPServer()
        result = server.status({})

        assert "version" in result
        assert "units" in result
        assert "env" in result
        assert "provider" in result
