---
description: "Vibesafe developer tools: scan, gen, fix, check"
allowed-tools: "Bash(vibesafe), Bash(vibe), mcp__vibesafe__*"
argument-hint: "subcommand [target]"
---

# Vibesafe Command

Executes Vibesafe developer workflows.

## Subcommands

### `/vibe scan`
Lists all Vibesafe units in the project and their status.

### `/vibe gen <target>`
Generates the implementation for the specified target unit.
Example: `/vibe gen examples.math.ops/fibonacci`

### `/vibe fix <target>`
Interactively fixes a failing unit. Runs tests, analyzes failures, and suggests spec updates.
Example: `/vibe fix examples.math.ops/fibonacci`

### `/vibe check [target]`
Runs verification (lint, type check, doctests) for the target or all units.
Example: `/vibe check`

## Implementation

{% if args[0] == "scan" %}
!vibesafe scan
{% elif args[0] == "gen" %}
Using MCP to compile {{ args[1] }}...
!vibesafe compile --target {{ args[1] }}
{% elif args[0] == "fix" %}
Running interactive fix for {{ args[1] }}...
!vibesafe test --target {{ args[1] }}
{% elif args[0] == "check" %}
!vibesafe check {{ args[1] if args[1] else "" }}
{% else %}
Unknown subcommand. Usage: /vibe [scan|gen|fix|check] [target]
{% endif %}
