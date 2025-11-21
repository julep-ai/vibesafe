"""
Tests for vibesafe.mcp module.
"""

from vibesafe import VibeCoded, vibesafe
from vibesafe.mcp import MCPServer


class TestMCPServer:
    """Tests for MCPServer class."""

    def test_initialization(self):
        """Test MCP server initialization."""
        server = MCPServer()
        assert "scan" in server.methods
        assert "compile" in server.methods
        assert "test" in server.methods
        assert "save" in server.methods
        assert "status" in server.methods

    def test_handle_request_unknown_method(self):
        """Test handling unknown method."""
        server = MCPServer()
        request = {"jsonrpc": "2.0", "method": "unknown_method", "id": 1}
        response = server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    def test_handle_request_scan(self, clear_vibesafe_registry):
        """Test handling scan request."""

        @vibesafe
        def test_func(x: int) -> int:
            """Test."""
            raise VibeCoded()

        server = MCPServer()
        request = {"jsonrpc": "2.0", "method": "scan", "params": {}, "id": 1}
        response = server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "units" in response["result"]
        assert "count" in response["result"]

    def test_handle_request_status(self):
        """Test handling status request."""
        server = MCPServer()
        request = {"jsonrpc": "2.0", "method": "status", "params": {}, "id": 1}
        response = server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "version" in response["result"]
        assert "units" in response["result"]

    def test_handle_request_with_error(self, mocker):
        """Test handling request that raises error."""
        server = MCPServer()

        # Mock scan method in the methods dictionary to raise error
        def raise_error(params):
            raise RuntimeError("Test error")

        server.methods["scan"] = raise_error

        request = {"jsonrpc": "2.0", "method": "scan", "params": {}, "id": 1}
        response = server.handle_request(request)

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
        result = server.compile({})
        assert "error" in result
        assert "target parameter required" in result["error"]

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
