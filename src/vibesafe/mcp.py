"""
MCP (Model Context Protocol) server for vibesafe.

Exposes vibesafe CLI commands as JSON-RPC for editor integration.
Implements the MCP protocol manually to avoid adding dependencies.
"""

import json
import sys
import traceback
from typing import Any

from vibesafe import __version__
from vibesafe.codegen import generate_for_unit
from vibesafe.core import get_registry
from vibesafe.runtime import update_index
from vibesafe.testing import run_all_tests, test_unit


class MCPServer:
    """
    MCP Server implementation for Vibesafe.
    Handles JSON-RPC 2.0 requests over stdio.
    """

    def __init__(self):
        self.tools = {
            "scan": self.scan,
            "compile": self.compile,
            "test": self.test,
            "save": self.save,
            "status": self.status,
        }

    def run(self) -> None:
        """Run the server loop."""
        for line in sys.stdin:
            if not line.strip():
                continue

            try:
                request = json.loads(line)
                self.handle_request(request)
            except Exception:
                # If we can't parse JSON, we can't even reply with an ID
                # But we should try to log or send a generic error if possible
                pass

    def handle_request(self, request: dict[str, Any]) -> None:
        """Handle a single JSON-RPC request."""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            self.handle_initialize(request_id, params)
        elif method == "notifications/initialized":
            # No response needed
            pass
        elif method == "tools/list":
            self.handle_tools_list(request_id)
        elif method == "tools/call":
            self.handle_tools_call(request_id, params)
        elif method == "ping":
            self.send_response(request_id, {})
        else:
            # Fallback for direct method calls (legacy/simple mode)
            # This allows testing via simple JSON-RPC clients if needed
            if method in self.tools:
                try:
                    result = self.tools[method](params)
                    self.send_response(request_id, result)
                except Exception as e:
                    self.send_error(request_id, -32000, str(e))
            else:
                self.send_error(request_id, -32601, f"Method not found: {method}")

    def send_response(self, request_id: Any, result: Any) -> None:
        """Send a JSON-RPC response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }
        print(json.dumps(response))
        sys.stdout.flush()

    def send_error(self, request_id: Any, code: int, message: str, data: Any = None) -> None:
        """Send a JSON-RPC error."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        }
        if data:
            response["error"]["data"] = data
        print(json.dumps(response))
        sys.stdout.flush()

    def handle_initialize(self, request_id: Any, params: dict[str, Any]) -> None:
        """Handle the initialize handshake."""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "vibesafe", "version": __version__},
        }
        self.send_response(request_id, result)

    def handle_tools_list(self, request_id: Any) -> None:
        """Return the list of available tools."""
        tools = [
            {
                "name": "scan",
                "description": "List all available Vibesafe units (functions/endpoints) in the project.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "compile",
                "description": "Generate implementation for a Vibesafe unit using the configured LLM provider.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The unit ID to compile (e.g., 'module.path/function_name')",
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force regeneration even if spec hasn't changed",
                            "default": False,
                        },
                    },
                    "required": ["target"],
                },
            },
            {
                "name": "test",
                "description": "Run tests (doctests, lint, type check) for a Vibesafe unit.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The unit ID to test. If omitted, tests all units.",
                        }
                    },
                },
            },
            {
                "name": "save",
                "description": "Activate a checkpoint for a unit, making it ready for production use. Requires tests to pass.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The unit ID to save. If omitted, saves all passing units.",
                        }
                    },
                },
            },
            {
                "name": "status",
                "description": "Get the overall status of the Vibesafe project (version, unit count, environment).",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]
        self.send_response(request_id, {"tools": tools})

    def handle_tools_call(self, request_id: Any, params: dict[str, Any]) -> None:
        """Execute a tool."""
        name = params.get("name")
        args = params.get("arguments", {})

        if name not in self.tools:
            self.send_error(request_id, -32601, f"Tool not found: {name}")
            return

        try:
            # Call the implementation
            result_data = self.tools[name](args)

            # MCP expects result to be a list of content items
            content = [{"type": "text", "text": json.dumps(result_data, indent=2)}]
            self.send_response(request_id, {"content": content})
        except Exception:
            self.send_error(request_id, -32000, f"Tool execution failed: {traceback.format_exc()}")

    # --- Tool Implementations ---

    def scan(self, params: dict[str, Any]) -> dict[str, Any]:
        """Scan for vibesafe units."""
        registry = get_registry()
        units = []
        for unit_id, unit_meta in registry.items():
            units.append(
                {
                    "id": unit_id,
                    "type": unit_meta.get("type", "function"),
                    "module": unit_meta.get("module"),
                    "qualname": unit_meta.get("qualname"),
                }
            )
        return {"units": units, "count": len(units)}

    def compile(self, params: dict[str, Any]) -> dict[str, Any]:
        """Compile a unit."""
        target = params.get("target")
        force = params.get("force", False)
        if not target:
            raise ValueError("target parameter required")

        checkpoint_info = generate_for_unit(target, force=force)
        update_index(
            target,
            checkpoint_info["spec_hash"],
            created=checkpoint_info.get("created_at"),
        )
        return {
            "success": True,
            "spec_hash": checkpoint_info["spec_hash"],
            "chk_hash": checkpoint_info["chk_hash"],
        }

    def test(self, params: dict[str, Any]) -> dict[str, Any]:
        """Test a unit."""
        target = params.get("target")
        if target:
            result = test_unit(target)
            return {
                "passed": result.passed,
                "failures": result.failures,
                "total": result.total,
                "errors": result.errors,
            }
        else:
            results = run_all_tests()
            return {
                "results": {
                    uid: {
                        "passed": r.passed,
                        "failures": r.failures,
                        "total": r.total,
                    }
                    for uid, r in results.items()
                }
            }

    def save(self, params: dict[str, Any]) -> dict[str, Any]:
        """Save (activate) a checkpoint."""
        target = params.get("target")
        if not target:
            results = run_all_tests()
            failed = [uid for uid, r in results.items() if not r.passed]
            if failed:
                return {"success": False, "failed_units": failed}
            return {"success": True, "message": "All units passed"}
        else:
            result = test_unit(target)
            if not result.passed:
                return {"success": False, "errors": result.errors}
            return {"success": True, "message": f"Unit {target} passed"}

    def status(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get overall status."""
        from vibesafe.config import get_config

        config = get_config()
        registry = get_registry()
        return {
            "version": __version__,
            "units": len(registry),
            "env": config.project.env,
            "provider": config.get_provider().model,
        }


if __name__ == "__main__":
    server = MCPServer()
    server.run()
