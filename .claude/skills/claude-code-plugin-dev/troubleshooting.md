# Troubleshooting Guide

Solutions for common issues when developing Claude Code plugins.

## Commands Not Working

### Command Not Appearing in /help

**Symptoms**: Command doesn't show up when running `/help`

**Check**:
1. File has `.md` extension
2. File is in `commands/` directory (or path specified in plugin.json)
3. plugin.json exists at `.claude-plugin/plugin.json`
4. plugin.json is valid JSON
5. Plugin is installed and enabled

**Solutions**:

```bash
# Validate plugin.json
jq . .claude-plugin/plugin.json

# Check commands configuration
jq '.commands' .claude-plugin/plugin.json

# Verify file location
ls commands/*.md

# Reinstall plugin
/plugin disable your-plugin
/plugin enable your-plugin

# Or reinstall completely
/plugin uninstall your-plugin
/plugin install your-plugin
```

### Command Executes But Fails

**Symptoms**: Command runs but produces errors

**Check**:
1. `allowed-tools` includes required tools
2. Tool patterns are correct
3. Arguments are properly substituted
4. File paths are quoted
5. Commands have proper permissions

**Solutions**:

```bash
# Test bash commands independently
prettier --write "test.ts"
echo $?  # Should be 0 for success

# Check tool permissions in frontmatter
cat commands/your-command.md | head -n 10

# Verify argument substitution
# Add debug output to command:
# !echo "Args: $ARGUMENTS" >&2
```

### Arguments Not Substituting

**Symptoms**: `$ARGUMENTS` or `$1` appear literally in output

**Check**:
1. Variables are in command body, not frontmatter
2. Correct syntax: `$ARGUMENTS`, `$1`, `$2`, etc.
3. No typos in variable names
4. Arguments passed when invoking command

**Solutions**:

```markdown
# ✅ Correct
---
description: "Test command"
---

Command received: $ARGUMENTS
First arg: $1

# ❌ Wrong - in frontmatter
---
description: "Command with $ARGUMENTS"
---
```

---

## Skills Not Activating

### Skill Never Activates

**Symptoms**: Skill exists but Claude never uses it

**Most Common Cause**: Description is too vague or missing keywords

**Solutions**:

1. **Make description extremely specific**:

```yaml
# ❌ Bad (won't activate)
description: "Helps with files"

# ✅ Good (will activate)
description: "Extracts text content from PDF files using pdftotext and OCR, handling multi-page documents and scanned images. Use when user asks to extract text from PDF, read PDF contents, convert PDF to text, or analyze PDF documents."
```

2. **Add explicit keywords**:
   - File types: PDF, CSV, JSON, XML, etc.
   - Actions: extract, convert, analyze, parse
   - Tools: specific command names
   - Domains: database, API, documentation

3. **Include "Use when" trigger**:
```yaml
description: "[What it does]. [Tools used]. Use when user asks to [triggers with keywords]."
```

4. **Test with exact keywords**:
```
User: "I need to extract text from a PDF file"
# Should activate PDF extraction skill
```

### Skill File Not Found

**Symptoms**: Error loading skill

**Check**:
1. File is named `SKILL.md` (exact case, must be this name)
2. File is in `skills/skill-name/` directory structure
3. YAML frontmatter is valid
4. skill-name uses lowercase-hyphens only

**Solutions**:

```bash
# Check file structure
ls -la skills/*/SKILL.md

# Verify YAML syntax
head -n 15 skills/my-skill/SKILL.md

# Correct structure:
skills/
└── my-skill/
    └── SKILL.md       # Must be exactly this name

# ❌ Wrong:
skills/
├── my-skill.md        # Wrong location
└── my-skill/
    └── skill.md       # Wrong case
```

### Skill Activates But Fails

**Symptoms**: Claude mentions using skill but it fails

**Check**:
1. `allowed-tools` includes tools the skill needs
2. Required tools exist on system
3. File paths are accessible
4. No permission errors

**Solutions**:

```bash
# Test tools independently
which pdftotext
pdftotext test.pdf -

# Check allowed-tools in SKILL.md
grep "allowed-tools" skills/*/SKILL.md

# Add more permissive tools temporarily to debug
allowed-tools: "Read(*), Bash(*)"

# Then narrow down once working
```

---

## MCP Servers Not Working

### Server Won't Start

**Symptoms**: Plugin installs but MCP server doesn't start

**Check**:
1. Server file exists at correct path
2. Command in plugin.json is correct
3. Dependencies are installed
4. No syntax errors in server code
5. File has execute permissions (Unix)

**Solutions**:

```bash
# Test server directly
node mcp/server.js
# Or
python mcp/server.py

# Check for syntax errors
node -c mcp/server.js
python -m py_compile mcp/server.py

# Install dependencies
npm install
pip install -r requirements.txt

# Check plugin.json MCP configuration
jq '.mcp' .claude-plugin/plugin.json

# Verify command path is relative to plugin root
{
  "mcp": {
    "servers": {
      "my-server": {
        "type": "stdio",
        "command": "node mcp/server.js"  # Not /mcp/server.js
      }
    }
  }
}
```

### Tools Not Available

**Symptoms**: Server starts but tools don't appear

**Check**:
1. Tools are exported from server
2. Tool names follow naming convention
3. Tool descriptions exist
4. Input schemas are valid

**Solutions**:

```typescript
// Verify tools are in server definition
const server = createSdkMcpServer({
  name: "my-tools",
  version: "1.0.0",
  tools: [
    tool({ name: "my_tool", ... }, async () => {})
  ]
});

export default server;  // Must export!
```

```bash
# Check tool availability in Claude Code
/mcp

# Should list:
# my-tools
#   - mcp__my-tools__my_tool
```

### Tool Invocation Fails

**Symptoms**: Tool is available but fails when called

**Check**:
1. Input schema matches parameters
2. Required parameters are handled
3. Return value is properly structured
4. Error handling is correct

**Solutions**:

```typescript
// Add comprehensive error handling
tool({ ... }, async (input) => {
  try {
    // Validate inputs
    if (!input.required_param) {
      return {
        success: false,
        error: "required_param is missing"
      };
    }

    // Execute operation
    const result = await operation(input);

    // Return consistent structure
    return {
      success: true,
      data: result
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      details: { stack: error.stack }
    };
  }
});
```

---

## Hooks Not Firing

### Hook Never Executes

**Symptoms**: Hook configured but never runs

**Check**:
1. Hook event name is valid
2. Hook is `enabled: true`
3. Matcher pattern is correct
4. JSON syntax is valid
5. Tool name matches pattern

**Solutions**:

```bash
# Validate hook JSON
jq . hooks/hooks.json

# Check event names
jq '.[].event' hooks/hooks.json

# Valid events:
# SessionStart, SessionEnd, UserPromptSubmit,
# PreToolUse, PostToolUse, PermissionRequest,
# Stop, SubagentStop, Notification, PreCompact

# Test with catch-all matcher
{
  "event": "PostToolUse",
  "matcher": {
    "toolName": "*"  # Matches all tools
  },
  "action": {
    "type": "command",
    "command": "echo 'Hook fired!' >&2"
  }
}
```

### Hook Fails Silently

**Symptoms**: Hook should run but nothing happens

**Check**:
1. Command exists on system
2. Exit code is appropriate
3. Timeout is sufficient
4. No silent failures

**Solutions**:

```bash
# Test command independently
FILE_PATH="test.ts" bash -c 'prettier --write "$FILE_PATH"'
echo $?  # Check exit code

# Add error output
{
  "action": {
    "command": "prettier --write \"$FILE_PATH\" 2>&1 || (echo 'Prettier failed' >&2; exit 0)"
  }
}

# Increase timeout if needed
{
  "timeout": 30  # From 10
}
```

### Hook Blocks Unexpectedly

**Symptoms**: Hook stops execution when it shouldn't

**Check**:
1. Exit code is 0 for success
2. Exit code 2 only for blocking errors
3. Error handling is correct

**Solutions**:

```bash
# Don't block on non-critical errors
# ❌ Wrong (blocks on any error)
prettier --write "$FILE_PATH"

# ✅ Right (continues on error)
prettier --write "$FILE_PATH" || true

# ✅ Right (suppresses errors)
prettier --write "$FILE_PATH" 2>/dev/null

# Only use exit 2 for critical blocks
npm test || (echo "Tests must pass!" && exit 2)
```

---

## Plugin Installation Issues

### Plugin Not Found

**Symptoms**: `/plugin install` says plugin not found

**Check**:
1. Marketplace is added
2. Plugin exists in marketplace
3. Repository is accessible
4. plugin.json exists

**Solutions**:

```bash
# Check marketplace list
/plugin marketplace list

# Add marketplace
/plugin marketplace add ~/.claude/marketplaces/local
/plugin marketplace add username/marketplace-repo

# Verify plugin location
ls ~/.claude/marketplaces/local/your-plugin
ls ~/.claude/marketplaces/local/your-plugin/.claude-plugin/plugin.json

# For GitHub plugins
/plugin install username/repo-name
```

### Installation Fails

**Symptoms**: Installation starts but fails

**Check**:
1. plugin.json is valid JSON
2. Name follows format rules
3. Version follows semver
4. All referenced paths exist

**Solutions**:

```bash
# Validate plugin.json
jq . .claude-plugin/plugin.json

# Check name format (lowercase-hyphens only)
jq -r '.name' .claude-plugin/plugin.json | grep -E '^[a-z0-9-]{1,64}$'

# Check version format (X.Y.Z)
jq -r '.version' .claude-plugin/plugin.json | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$'

# Verify paths exist
jq -r '.commands.path' .claude-plugin/plugin.json | xargs ls
```

---

## General Debugging

### Enable Verbose Output

```bash
# Set debug environment variable (if supported)
export CLAUDE_DEBUG=1

# Add debug output to commands
!echo "Debug: command executed with $ARGUMENTS" >&2

# Add debug output to hooks
{
  "action": {
    "command": "echo \"Hook triggered: $TOOL_NAME on $FILE_PATH\" >&2; your-command"
  }
}
```

### Check Plugin Status

```bash
# List all plugins
/plugin list

# Get plugin info
/plugin info your-plugin

# Check enabled status
/plugin list | grep your-plugin
```

### Validate All JSON

```bash
# Validate plugin.json
jq empty .claude-plugin/plugin.json && echo "Valid" || echo "Invalid"

# Validate all hooks
for hook in hooks/*.json; do
  jq empty "$hook" && echo "$hook: Valid" || echo "$hook: Invalid"
done
```

### Test Components Independently

```bash
# Test commands
cat commands/your-command.md

# Test skills
cat skills/your-skill/SKILL.md

# Test MCP server
node mcp/server.js &
sleep 2
kill %1

# Test hooks
FILE_PATH="test.ts" bash -c 'prettier --write "$FILE_PATH"'
```

### Simplify and Rebuild

When all else fails:

1. **Create minimal plugin**:
```json
{
  "name": "test-plugin",
  "version": "1.0.0",
  "description": "Minimal test plugin"
}
```

2. **Add one component at a time**:
   - Add command → Test
   - Add skill → Test
   - Add MCP server → Test
   - Add hooks → Test

3. **Identify what breaks**:
   - When does it stop working?
   - What was added last?
   - What's different from working state?

---

## Getting Help

If you're still stuck:

1. **Check documentation**:
   - Review relevant reference docs
   - Check examples for similar use cases
   - Compare with working plugins

2. **Search community resources**:
   - GitHub issues in plugin repos
   - Community forums and discussions
   - Example plugins on GitHub

3. **Create minimal reproduction**:
   - Simplify to smallest failing case
   - Document exact steps to reproduce
   - Include error messages and logs

4. **Ask for help**:
   - Provide reproduction steps
   - Share plugin.json and relevant files
   - Include error messages
   - Describe expected vs actual behavior

---

## Quick Diagnostic Checklist

Run through this checklist when debugging:

### Plugin Structure
- [ ] `.claude-plugin/plugin.json` exists
- [ ] plugin.json is valid JSON
- [ ] name is lowercase-hyphens only
- [ ] version follows X.Y.Z format
- [ ] All referenced paths exist

### Commands
- [ ] Files have `.md` extension
- [ ] Files in correct directory
- [ ] Frontmatter YAML is valid
- [ ] allowed-tools patterns are correct
- [ ] Command appears in `/help`

### Skills
- [ ] File named `SKILL.md` (exact case)
- [ ] In `skills/name/` directory
- [ ] YAML frontmatter is valid
- [ ] Description has specific keywords
- [ ] Description includes "Use when"
- [ ] allowed-tools includes needed tools

### MCP Servers
- [ ] Server file exists
- [ ] Command path is correct in plugin.json
- [ ] Dependencies installed
- [ ] Server starts without errors
- [ ] Tools have detailed descriptions
- [ ] Input schemas are complete
- [ ] Server listed in `/mcp`

### Hooks
- [ ] JSON files are valid
- [ ] Event names are correct
- [ ] Matchers use valid patterns
- [ ] Commands execute successfully
- [ ] Timeouts are appropriate
- [ ] enabled is true

Use this checklist systematically to identify issues!
