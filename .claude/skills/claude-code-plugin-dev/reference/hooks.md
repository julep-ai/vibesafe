# Hooks (Event Handlers)

Complete guide to implementing event-driven automation with hooks.

## Overview

Hooks are event handlers that execute automatically at specific lifecycle points in Claude Code. They enable automation, validation, formatting, and custom workflows.

**Best for**:
- Automatic code formatting
- Pre/post-commit validation
- Logging and notifications
- Tool use tracking
- Custom automations

## Hook Configuration

**File**: `hooks/hooks.json`

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "toolName": "Edit|Write"
      },
      "action": {
        "type": "command",
        "command": "prettier --write \"$FILE_PATH\""
      },
      "timeout": 10,
      "enabled": true
    }
  ]
}
```

## Available Hook Events

### SessionStart
- **Trigger**: When Claude Code session begins
- **Use for**: Initialize environment, load config, set variables
- **Example**: Load API keys, set up logging

### SessionEnd
- **Trigger**: When Claude Code session ends
- **Use for**: Cleanup, save state, final logging
- **Example**: Close connections, archive logs

### UserPromptSubmit
- **Trigger**: User submits a prompt
- **Use for**: Pre-processing, validation, context injection
- **Example**: Add project context, validate requests

### PreToolUse
- **Trigger**: Before Claude executes a tool
- **Use for**: Blocking operations, validation, safety checks
- **Example**: Block dangerous commands, require approval

### PostToolUse
- **Trigger**: After Claude executes a tool
- **Use for**: Formatting, logging, notifications, cleanup
- **Example**: Auto-format code, log changes, notify team

### PermissionRequest
- **Trigger**: Claude requests user permission
- **Use for**: Auto-approve/deny based on rules
- **Example**: Auto-approve safe operations

### Stop
- **Trigger**: Claude finishes generating response
- **Use for**: Validation, post-processing, cleanup
- **Example**: Run tests, check conventions

### SubagentStop
- **Trigger**: Subagent completes its task
- **Use for**: Aggregate results, notify parent
- **Example**: Collect subagent outputs

### Notification
- **Trigger**: System sends notification
- **Use for**: Desktop alerts, external notifications
- **Example**: Send Slack message, desktop popup

### PreCompact
- **Trigger**: Before context window compaction
- **Use for**: Save important context, cleanup
- **Example**: Archive conversation state

## Hook Structure

### Required Fields

```json
{
  "event": "PostToolUse",        // Which event triggers this hook
  "action": {                    // What to do
    "type": "command",           // "command" or "prompt"
    "command": "echo hello"      // Command to execute
  }
}
```

### Optional Fields

```json
{
  "event": "PostToolUse",
  "matcher": {                   // Filter when hook runs
    "toolName": "Edit|Write"
  },
  "action": {
    "type": "command",
    "command": "prettier --write \"$FILE_PATH\""
  },
  "timeout": 10,                 // Max execution time (seconds)
  "enabled": true                // Enable/disable hook
}
```

## Matchers

Matchers filter when hooks execute based on context.

### Tool Name Matching

**Exact match**:
```json
"matcher": {
  "toolName": "Edit"
}
```

**Multiple tools** (OR):
```json
"matcher": {
  "toolName": "Edit|Write|Delete"
}
```

**All tools**:
```json
"matcher": {
  "toolName": "*"
}
```

**Pattern matching**:
```json
"matcher": {
  "toolName": "Bash:git:*"      // All git bash commands
}
```

## Action Types

### Command Actions

Execute shell commands.

```json
"action": {
  "type": "command",
  "command": "prettier --write \"$FILE_PATH\""
}
```

**Available variables**:
- `$FILE_PATH` - Modified file path (PostToolUse)
- `$TOOL_NAME` - Tool that was used
- `$CLAUDE_PROJECT_DIR` - Project root
- `$CLAUDE_PLUGIN_ROOT` - Plugin directory
- All environment variables

**Exit codes**:
- `0` - Success (continue normally)
- `2` - Blocking error (show stderr to Claude, halt)
- Other - Non-blocking error (logged but continues)

### Prompt Actions

Send prompts to Claude for processing.

```json
"action": {
  "type": "prompt",
  "prompt": "Did the code follow our style guidelines?"
}
```

**Use for**:
- Decision making
- Code review
- Analysis
- Validation requiring understanding

## Complete Hook Examples

### Example 1: Auto-Format on Save

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "toolName": "Edit|Write"
      },
      "action": {
        "type": "command",
        "command": "if [[ $FILE_PATH == *.ts || $FILE_PATH == *.tsx ]]; then prettier --write \"$FILE_PATH\" 2>/dev/null; fi"
      },
      "timeout": 10,
      "enabled": true
    },
    {
      "event": "PostToolUse",
      "matcher": {
        "toolName": "Edit|Write"
      },
      "action": {
        "type": "command",
        "command": "if [[ $FILE_PATH == *.py ]]; then black \"$FILE_PATH\" 2>/dev/null && ruff check --fix \"$FILE_PATH\" 2>/dev/null; fi"
      },
      "timeout": 15,
      "enabled": true
    }
  ]
}
```

### Example 2: Pre-Commit Validation

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matcher": {
        "toolName": "Bash:git:commit"
      },
      "action": {
        "type": "command",
        "command": "npm test || (echo 'Tests failed! Fix before committing.' && exit 2)"
      },
      "timeout": 60,
      "enabled": true
    }
  ]
}
```

### Example 3: Change Logging

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "toolName": "Edit|Write|Delete"
      },
      "action": {
        "type": "command",
        "command": "echo \"$(date): $TOOL_NAME on $FILE_PATH\" >> ~/.claude/changes.log"
      },
      "timeout": 3,
      "enabled": true
    }
  ]
}
```

### Example 4: Test on Stop

```json
{
  "hooks": [
    {
      "event": "Stop",
      "matcher": {
        "toolName": "*"
      },
      "action": {
        "type": "command",
        "command": "npm test --silent && echo '✅ Tests passed' || echo '❌ Tests failed'"
      },
      "timeout": 60,
      "enabled": true
    }
  ]
}
```

### Example 5: Notify Team on Deploy

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "toolName": "Bash:kubectl:*"
      },
      "action": {
        "type": "command",
        "command": "curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK -d '{\"text\":\"Deployment executed\"}'"
      },
      "timeout": 5,
      "enabled": true
    }
  ]
}
```

### Example 6: Session Initialization

```json
{
  "hooks": [
    {
      "event": "SessionStart",
      "action": {
        "type": "command",
        "command": "echo \"export PROJECT_ENV=development\" > $CLAUDE_ENV_FILE"
      },
      "timeout": 3,
      "enabled": true
    }
  ]
}
```

## Environment Variables

### Available in Hooks

**Standard variables**:
- `$CLAUDE_PROJECT_DIR` - Project root directory
- `$CLAUDE_PLUGIN_ROOT` - Plugin installation directory
- `$CLAUDE_ENV_FILE` - File for persisting env vars across hooks
- All system environment variables

**Tool-specific variables**:
- `$FILE_PATH` - File path (for Edit/Write/Read tools)
- `$TOOL_NAME` - Name of tool executed
- `$COMMAND` - Bash command (for Bash tool)

### Persisting Variables

**Save variable**:
```bash
echo "export MY_VAR=value" >> $CLAUDE_ENV_FILE
```

**Use in later hooks**:
```bash
source $CLAUDE_ENV_FILE
echo $MY_VAR
```

## Input/Output Protocol

### Input (JSON via stdin)

Hooks receive JSON with session and event context:

```json
{
  "session": {
    "id": "session-uuid",
    "workspaceDir": "/path/to/workspace",
    "currentDir": "/path/to/current"
  },
  "event": {
    "type": "PostToolUse",
    "tool": "Edit",
    "status": "success",
    "output": "File modified: example.ts"
  }
}
```

### Output

**Exit codes**:
- `0` - Success, continue normally
- `2` - Blocking error, halt execution, show stderr to Claude
- Other - Non-blocking error, logged but continues

**Special JSON output**:
```json
{
  "decision": "approve",
  "additionalContext": "Optional context to add to conversation"
}
```

**stdout**: Logged if verbose mode enabled

**stderr**: Shown to user on blocking errors (exit 2)

## Timeout Behavior

```json
{
  "timeout": 10  // Seconds
}
```

**What happens on timeout**:
1. Hook process is killed
2. Treated as non-blocking error
3. Execution continues
4. Warning logged

**Choosing timeouts**:
- **Quick operations** (formatting): 5-10s
- **Tests**: 30-60s
- **Builds**: 60-120s
- **Network calls**: 10-30s

## Best Practices

### Hook Design

✅ **DO**:
- Keep hooks fast and focused
- Use appropriate timeouts
- Handle errors gracefully
- Log important actions
- Test hooks independently
- Use matchers to filter appropriately

❌ **DON'T**:
- Create slow hooks (>30s)
- Use hooks for long-running processes
- Ignore error handling
- Create hooks with side effects in unrelated tools
- Forget to set enabled flag

### Command Safety

✅ **DO**:
- Quote file paths: `"$FILE_PATH"`
- Check file existence before operations
- Use `2>/dev/null` to suppress errors
- Add `|| true` for non-critical commands
- Validate inputs

❌ **DON'T**:
- Use unquoted paths (breaks with spaces)
- Assume files exist
- Let errors halt unintentionally
- Execute without validation
- Use dangerous commands without checks

### Error Handling

✅ **DO**:
```bash
# Non-critical: ignore errors
prettier --write "$FILE_PATH" 2>/dev/null || true

# Critical: block on error
npm test || (echo "Tests failed!" && exit 2)

# Conditional: check before executing
[[ -f "$FILE_PATH" ]] && prettier --write "$FILE_PATH"
```

❌ **DON'T**:
```bash
# No error handling
prettier --write $FILE_PATH

# Blocks unconditionally
prettier --write "$FILE_PATH" || exit 2
```

### Performance

✅ **DO**:
- Use matchers to filter hooks
- Keep commands fast
- Run expensive operations async
- Cache results when possible
- Set reasonable timeouts

❌ **DON'T**:
- Run hooks on every event
- Execute slow operations synchronously
- Skip timeout configuration
- Run redundant operations
- Chain many hooks unnecessarily

## Troubleshooting

### Hook Not Firing

**Check**:
1. Event name is valid
2. Hook is `enabled: true`
3. Matcher pattern is correct
4. Tool name matches pattern
5. hook.json is valid JSON

**Debug**:
```json
{
  "event": "PostToolUse",
  "matcher": {
    "toolName": "*"
  },
  "action": {
    "type": "command",
    "command": "echo 'Hook fired!' >&2"
  }
}
```

### Command Failing

**Check**:
1. Command exists: `which prettier`
2. File paths are quoted
3. Exit code is appropriate
4. Timeout is sufficient
5. Environment variables are set

**Debug**:
```bash
# Test command independently
prettier --write "test.ts"

# Check exit code
echo $?
```

### Blocking Unintentionally

**Problem**: Hook blocks execution unexpectedly

**Solution**: Use exit code 0 or handle errors:
```bash
# Don't block on failure
prettier --write "$FILE_PATH" || true

# Or suppress errors
prettier --write "$FILE_PATH" 2>/dev/null
```

### Timeout Issues

**Problem**: Hook times out

**Solutions**:
1. Increase timeout for slow operations
2. Run long operations in background
3. Optimize command performance
4. Use async operations

## Multiple Hook Files

You can split hooks across multiple JSON files:

```
hooks/
├── formatting.json      # Formatting hooks
├── testing.json         # Test hooks
├── logging.json         # Logging hooks
└── deployment.json      # Deployment hooks
```

All files are loaded and merged.

## Security Considerations

### Safe Commands

✅ **Safe**:
```bash
prettier --write "$FILE_PATH"
eslint --fix "$FILE_PATH"
git add "$FILE_PATH"
npm test
```

❌ **Dangerous**:
```bash
rm -rf "$DIRECTORY"        # Destructive
eval "$USER_INPUT"         # Code injection
curl $URL | bash           # Remote code execution
chmod 777 "$FILE_PATH"     # Overly permissive
```

### Input Validation

**Always validate**:
```bash
# Check file exists
[[ -f "$FILE_PATH" ]] || exit 0

# Check file type
[[ "$FILE_PATH" == *.ts ]] || exit 0

# Validate patterns
echo "$FILE_PATH" | grep -E '^[a-zA-Z0-9/._-]+$' || exit 2
```

### Secrets Management

**Don't**:
```bash
# ❌ Hardcoded secrets
curl -H "Authorization: Bearer hardcoded-token"
```

**Do**:
```bash
# ✅ Environment variables
curl -H "Authorization: Bearer $API_TOKEN"
```

## Next Steps

- **Create commands**: See [Slash Commands](slash-commands.md)
- **Add skills**: See [Agent Skills](agent-skills.md)
- **Build tools**: See [MCP Servers](mcp-servers.md)
- **Test hooks**: See [Development Workflow](../guides/development-workflow.md)
