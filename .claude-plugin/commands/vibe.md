---
name: vibe
description: "Run vibesafe CLI commands through the MCP server. Usage: /vibe <subcommand> [args] where subcommand ∈ {scan, compile, test, save, diff, status, mcp, init}."
arguments:
  - name: subcommand
    description: "vibesafe subcommand to execute (scan | compile | test | save | diff | status | mcp | init)"
    required: true
---

Run Vibesafe toolchain actions via MCP.

Examples:
- `/vibe scan`
- `/vibe compile --target app.math.ops/fibonacci`
- `/vibe test --target app.math.ops/fibonacci`
- `/vibe status`
- `/vibe diff`
- `/vibe save --target app.math.ops/fibonacci`
- `/vibe init`
