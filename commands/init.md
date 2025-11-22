---
name: init
description: "Initialize the Vibesafe plugin session: report mode, list commands, and verify MCP connectivity."
arguments: []
---

Run a quick readiness check:
- Show current mode (`VIBESAFE_ENV` or config default)
- List available Vibesafe commands
- Confirm MCP server connectivity

Example:
- `/vibesafe:init`

Steps:
1) `echo "VIBESAFE_ENV=${VIBESAFE_ENV:-<unset>}"`  
2) `vibesafe status || true`  # harmless status check  
3) `echo "Commands: scan, compile, test, save, diff, status, mcp"`  
