---
name: vibesafe-expert
description: "Manages Vibesafe specs and implementations. Activates when user asks to fix tests, explain generated code, or scaffold new specs. Use this to run 'vibesafe' commands via MCP."
version: "0.1.0"
tags: ["vibesafe", "testing", "codegen"]
allowed-tools: "mcp__vibesafe__*, Bash(vibesafe), Read(*), Write(*)"
model: "claude-3-5-sonnet-20241022"
---

# Vibesafe Expert Skill

This skill allows Claude to interact with the Vibesafe system to generate, test, and fix code.

## Capabilities

1.  **Scan**: List all available Vibesafe units.
2.  **Compile**: Generate implementation for a unit (using `mcp__vibesafe__compile`).
3.  **Test**: Run tests for a unit (using `mcp__vibesafe__test`).
4.  **Fix**: Analyze test failures and suggest spec improvements.
5.  **Scaffold**: Create new `@vibesafe` specs.

## Usage Examples

### Fixing a failing test
User: "Fix the fibonacci test failure."
Action:
1. Run `mcp__vibesafe__test(target="...")` to get failure details.
2. Analyze the failure.
3. Read the spec file.
4. Update the spec (docstring/doctests) to address the edge case.
5. Run `mcp__vibesafe__compile(target="...", force=True)`.
6. Run `mcp__vibesafe__test(target="...")` to verify.

### Explaining generated code
User: "What does the generated code for 'auth' do?"
Action:
1. Read the generated implementation (via `mcp__vibesafe__scan` to find path, or just read the spec).
2. Explain the logic.

### Scaffolding
User: "Create a new vibesafe unit for calculating tax."
Action:
1. Create a new file (or append to existing).
2. Write the `@vibesafe` decorated function with types and doctests.
3. Run `mcp__vibesafe__scan` to register it.
4. Run `mcp__vibesafe__compile` to generate it.
