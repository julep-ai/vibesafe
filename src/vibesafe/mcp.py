"""
MCP (Model Context Protocol) server for vibesafe.

Exposes vibesafe CLI commands as JSON-RPC for editor integration.
"""

import json
import sys
from typing import Any

from vibesafe import __version__
from vibesafe.codegen import generate_for_unit
from vibesafe.core import vibesafe
from vibesafe.runtime import update_index, write_shim
from vibesafe.testing import run_all_tests, test_unit


class MCPServer:
    """Basic MCP server for vibesafe commands."""

    def __init__(self):
        self.methods = {
            "scan": self.scan,
            "compile": self.compile,
            "test": self.test,
            "save": self.save,
            "status": self.status,
        }

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Handle a JSON-RPC request.

        Args:
            request: JSON-RPC request dict

        Returns:
            JSON-RPC response dict
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method not in self.methods:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": "Method not found"},
                "id": request_id,
            }

        try:
            result = self.methods[method](params)
            return {"jsonrpc": "2.0", "result": result, "id": request_id}
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": request_id,
            }

    def scan(self, params: dict[str, Any]) -> dict[str, Any]:
        """Scan for vibesafe units."""
        registry = vibesafe.get_registry()

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
            return {"error": "target parameter required"}

        try:
            checkpoint_info = generate_for_unit(target, force=force)
            update_index(
                target,
                checkpoint_info["spec_hash"],
                created=checkpoint_info.get("created_at"),
            )
            shim_path = write_shim(target)

            return {
                "success": True,
                "spec_hash": checkpoint_info["spec_hash"],
                "chk_hash": checkpoint_info["chk_hash"],
                "shim_path": str(shim_path),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

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
            # Test all
            results = run_all_tests()
            failed = [uid for uid, r in results.items() if not r.passed]

            if failed:
                return {"success": False, "failed_units": failed}

            return {"success": True, "message": "All units passed"}
        else:
            result = test_unit(target)
            if not result.passed:
                return {
                    "success": False,
                    "errors": result.errors,
                }

            return {"success": True, "message": f"Unit {target} passed"}

    def status(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get overall status."""
        from vibesafe.config import get_config

        config = get_config()
        registry = vibesafe.get_registry()

        return {
            "version": __version__,
            "units": len(registry),
            "env": config.project.env,
            "provider": config.get_provider().model,
        }


def run_mcp_server() -> None:
    """
    Run MCP server in stdio mode.

    Reads JSON-RPC requests from stdin and writes responses to stdout.
    """
    server = MCPServer()

    for line in sys.stdin:
        if not line.strip():
            continue

        try:
            request = json.loads(line)
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": f"Parse error: {e}"},
                "id": None,
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    run_mcp_server()
