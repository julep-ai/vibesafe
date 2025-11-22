# Development Workflow

Complete guide to developing, testing, and debugging Claude Code plugins locally.

## Local Development Setup

### 1. Create Local Marketplace

```bash
# Create marketplace directory
mkdir -p ~/.claude/marketplaces/local

# Navigate to your plugin project
cd /path/to/your-plugin

# Link to local marketplace
ln -s $(pwd) ~/.claude/marketplaces/local/your-plugin

# Or copy instead of symlinking
cp -r . ~/.claude/marketplaces/local/your-plugin
```

### 2. Add Marketplace to Claude Code

In Claude Code terminal:
```bash
/plugin marketplace add ~/.claude/marketplaces/local
```

### 3. Install Your Plugin

```bash
/plugin install your-plugin
```

### 4. Verify Installation

```bash
# List installed plugins
/plugin list

# Check if commands appear
/help | grep your-command

# View plugin details
/plugin info your-plugin
```

## Iterative Development

### Make Changes Workflow

```bash
# 1. Edit plugin files
vim commands/my-command.md

# 2. Reload plugin
/plugin disable your-plugin
/plugin enable your-plugin

# 3. Test changes
/my-command test arguments

# 4. Repeat as needed
```

### Alternative: Direct File Editing

For project-scope plugins (`.claude/`):
```bash
# Edit directly - changes take effect immediately
vim .claude/commands/my-command.md

# Test right away
/my-command test
```

## Validation Checklist

### Before Testing

- [ ] **plugin.json validation**
```bash
jq . .claude-plugin/plugin.json
jq '.name, .version, .description' .claude-plugin/plugin.json
```

- [ ] **Name format check**
```bash
jq -r '.name' .claude-plugin/plugin.json | grep -E '^[a-z0-9-]{1,64}$'
```

- [ ] **Version format check**
```bash
jq -r '.version' .claude-plugin/plugin.json | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$'
```

- [ ] **File structure check**
```bash
ls -la .claude-plugin/
ls -la commands/
ls -la skills/*/SKILL.md
```

- [ ] **YAML frontmatter validation** (for skills/commands)
```bash
head -n 10 skills/my-skill/SKILL.md
head -n 10 commands/my-command.md
```

## Testing Components

### Testing Slash Commands

```bash
# 1. Verify command appears
/help | grep my-command

# 2. Test without arguments
/my-command

# 3. Test with single argument
/my-command arg1

# 4. Test with multiple arguments
/my-command arg1 arg2 "arg with spaces"

# 5. Test special characters
/my-command "path/to/file.txt"

# 6. Check allowed-tools work
# (Verify Bash commands execute, files can be read, etc.)
```

**Command Test Checklist**:
- [ ] Command listed in `/help`
- [ ] Description is clear
- [ ] `$ARGUMENTS` substitutes correctly
- [ ] `$1`, `$2`, etc. work for positional args
- [ ] `!bash` commands execute (if allowed)
- [ ] `@file` includes file contents (if used)
- [ ] Error handling works
- [ ] Output is well-formatted

### Testing Agent Skills

Skills are harder to test since they activate automatically. Use these strategies:

**Direct Testing**:
```
User: [Use keywords from skill description]

Example for PDF skill:
"I have a PDF file that needs text extraction"
"Can you extract text from report.pdf?"
"Read the contents of this PDF document"
```

**Skill Activation Checklist**:
- [ ] Skill activates on relevant keywords
- [ ] Claude mentions using the skill
- [ ] Skill has access to required tools
- [ ] Output is correctly formatted
- [ ] Error handling works
- [ ] Works with different phrasings

**If skill doesn't activate**:
1. Make description more specific
2. Add more keywords (file types, actions)
3. Include "Use when user asks to..."
4. Check SKILL.md location and case
5. Verify YAML frontmatter syntax
6. Test with exact keywords from description

### Testing MCP Servers

**1. Test server starts**:
```bash
# TypeScript
node mcp/server.js
# Should start without errors, Ctrl+C to stop

# Python
python mcp/server.py
# Should start without errors, Ctrl+C to stop
```

**2. Check server in Claude Code**:
```bash
/mcp
# Should list your server and tools
```

**3. Test tool invocation**:
```
User: "Use the [tool_name] tool to [action]"

Example:
"Use the get_weather tool to check weather in London"
"Execute the database query tool for SELECT * FROM users"
```

**MCP Test Checklist**:
- [ ] Server starts without errors
- [ ] Server listed in `/mcp`
- [ ] All tools are visible
- [ ] Tool names follow naming convention
- [ ] Descriptions are detailed
- [ ] Input schemas are complete
- [ ] Tools execute successfully
- [ ] Error handling returns proper structure
- [ ] Results are well-formatted

### Testing Hooks

Hooks execute automatically on events. Test by triggering events:

**PostToolUse hooks**:
```bash
# Edit a file to trigger PostToolUse
/my-command that uses Edit tool

# Check if hook executed
# Look for hook output (formatting, logging, etc.)
```

**PreToolUse hooks**:
```bash
# Try action that should be blocked
# Verify hook prevents or allows action
```

**Stop hooks**:
```bash
# Complete any command or response
# Check if hook executed at the end
```

**Hook Test Checklist**:
- [ ] Hook fires on correct event
- [ ] Matcher filters appropriately
- [ ] Command executes successfully
- [ ] Exit code is correct
- [ ] Timeout is sufficient
- [ ] Output/side effects are correct
- [ ] No unintended blocking
- [ ] Error handling works

## Debugging Techniques

### Enable Verbose Logging

```bash
# Set debug environment variable (if supported)
export CLAUDE_DEBUG=1

# Or add debug output in hooks
echo "Debug: $TOOL_NAME on $FILE_PATH" >&2
```

### Check Plugin Installation

```bash
# List all installed plugins
/plugin list

# Get plugin details
/plugin info your-plugin

# Check plugin status
/plugin status your-plugin
```

### Validate JSON Files

```bash
# Validate plugin.json
jq empty .claude-plugin/plugin.json && echo "Valid" || echo "Invalid"

# Validate hook files
jq empty hooks/*.json && echo "All valid" || echo "Some invalid"

# Pretty-print for inspection
jq . .claude-plugin/plugin.json
```

### Test Components Independently

**Commands**:
```bash
# Read command file
cat commands/my-command.md

# Check frontmatter parsing
head -n 20 commands/my-command.md
```

**Skills**:
```bash
# Read skill file
cat skills/my-skill/SKILL.md

# Validate YAML frontmatter
head -n 15 skills/my-skill/SKILL.md | grep -A 10 "^---"
```

**MCP Servers**:
```bash
# Test server script
node mcp/server.js &
sleep 2
kill %1

# Check for syntax errors
node -c mcp/server.js
python -m py_compile mcp/server.py
```

**Hooks**:
```bash
# Test hook command directly
FILE_PATH="test.ts" bash -c 'prettier --write "$FILE_PATH"'

# Check exit codes
echo $?
```

### Common Issues and Fixes

**"Plugin not found"**:
```bash
# Check marketplace added
/plugin marketplace list

# Re-add marketplace
/plugin marketplace add ~/.claude/marketplaces/local

# Check plugin exists in marketplace
ls ~/.claude/marketplaces/local/
```

**"Command not appearing in /help"**:
```bash
# Check file location
ls .claude-plugin/plugin.json
ls commands/*.md

# Validate plugin.json
jq '.commands' .claude-plugin/plugin.json

# Check plugin enabled
/plugin list | grep your-plugin
```

**"Skill not activating"**:
```bash
# Read skill description
jq -r '.description' skills/my-skill/SKILL.md | head -n 5

# Check file case
ls skills/*/SKILL.md

# Validate YAML
head -n 15 skills/my-skill/SKILL.md
```

**"MCP tool not available"**:
```bash
# Check server status
/mcp

# Test server directly
node mcp/server.js

# Check plugin.json MCP config
jq '.mcp' .claude-plugin/plugin.json
```

**"Hook not firing"**:
```bash
# Validate hook JSON
jq . hooks/hooks.json

# Check event name
jq '.[].event' hooks/hooks.json

# Verify enabled
jq '.[].enabled' hooks/hooks.json
```

## Test Automation

### Create Test Script

```bash
#!/bin/bash
# test-plugin.sh

set -e  # Exit on error

echo "🔍 Testing plugin..."

# 1. Validate JSON
echo "Validating plugin.json..."
jq empty .claude-plugin/plugin.json

# 2. Check name format
echo "Checking name format..."
NAME=$(jq -r '.name' .claude-plugin/plugin.json)
echo "$NAME" | grep -E '^[a-z0-9-]{1,64}$' || (echo "❌ Invalid name format" && exit 1)

# 3. Validate version
echo "Checking version format..."
VERSION=$(jq -r '.version' .claude-plugin/plugin.json)
echo "$VERSION" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' || (echo "❌ Invalid version" && exit 1)

# 4. Check file structure
echo "Checking file structure..."
[[ -f .claude-plugin/plugin.json ]] || (echo "❌ Missing plugin.json" && exit 1)

# 5. Validate commands
if [[ -d commands ]]; then
    echo "Validating commands..."
    find commands -name "*.md" | while read cmd; do
        echo "  Checking $cmd"
        head -n 1 "$cmd" | grep "^---$" || echo "  ⚠️  Missing frontmatter in $cmd"
    done
fi

# 6. Validate skills
if [[ -d skills ]]; then
    echo "Validating skills..."
    find skills -name "SKILL.md" | while read skill; do
        echo "  Checking $skill"
        head -n 1 "$skill" | grep "^---$" || echo "  ⚠️  Missing frontmatter in $skill"
    done
fi

# 7. Test MCP servers
if [[ -d mcp ]]; then
    echo "Testing MCP servers..."
    for server in mcp/*.{js,ts,py}; do
        [[ -f "$server" ]] || continue
        echo "  Checking $server"
        if [[ "$server" == *.js ]]; then
            node -c "$server" || (echo "  ❌ Syntax error in $server" && exit 1)
        elif [[ "$server" == *.py ]]; then
            python -m py_compile "$server" || (echo "  ❌ Syntax error in $server" && exit 1)
        fi
    done
fi

# 8. Validate hooks
if [[ -d hooks ]]; then
    echo "Validating hooks..."
    for hook in hooks/*.json; do
        [[ -f "$hook" ]] || continue
        echo "  Checking $hook"
        jq empty "$hook" || (echo "  ❌ Invalid JSON in $hook" && exit 1)
    done
fi

echo "✅ All tests passed!"
```

**Run tests**:
```bash
chmod +x test-plugin.sh
./test-plugin.sh
```

## Integration Testing

### Test End-to-End Workflows

```bash
# 1. Install plugin
/plugin install your-plugin

# 2. Test command
/my-command test-arg

# 3. Trigger skill
# (Ask question with skill keywords)

# 4. Invoke MCP tool
# (Ask Claude to use the tool)

# 5. Trigger hooks
# (Perform actions that trigger hooks)

# 6. Verify all components work together
```

### Create Test Scenarios

Document test scenarios in `tests/scenarios.md`:

```markdown
# Test Scenarios

## Scenario 1: Basic Command Execution
1. Run `/my-command test`
2. Expected: Command executes successfully
3. Expected: Output is formatted correctly

## Scenario 2: Skill Activation
1. Say "I need to extract text from a PDF"
2. Expected: PDF extraction skill activates
3. Expected: Claude mentions using the skill

## Scenario 3: Hook Execution
1. Edit a TypeScript file
2. Expected: Prettier runs automatically
3. Expected: File is formatted

## Scenario 4: MCP Tool Use
1. Ask "Get weather for London"
2. Expected: Claude invokes get_weather tool
3. Expected: Returns weather data
```

## Performance Testing

### Measure Hook Timing

```bash
# Add timing to hooks
time prettier --write "$FILE_PATH"

# Check hook timeout is sufficient
# Hook should complete well before timeout
```

### Monitor MCP Server

```bash
# Check server startup time
time node mcp/server.js &

# Monitor memory usage
top -p $(pgrep -f "server.js")

# Test tool response time
# Ask Claude to use tool, note delay
```

## Version Control Integration

### Git Workflow

```bash
# 1. Commit changes
git add .
git commit -m "feat: add new command"

# 2. Tag version
git tag v1.0.0
git push origin main v1.0.0

# 3. Test from git
cd /tmp
git clone your-repo test-plugin
/plugin install /tmp/test-plugin
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run validation before commit
./test-plugin.sh || exit 1
```

## Troubleshooting Workflow

When something doesn't work:

1. **Check logs/output**
   - Look for error messages
   - Check Claude's response

2. **Validate configuration**
   - Run `jq . .claude-plugin/plugin.json`
   - Check file locations

3. **Test independently**
   - Test components outside Claude Code
   - Verify tools work from command line

4. **Simplify**
   - Remove complexity
   - Test minimal version
   - Add features back incrementally

5. **Check documentation**
   - Review reference docs
   - Compare with examples
   - Check for typos

6. **Ask for help**
   - Search community resources
   - Check GitHub issues
   - Ask in forums

## Next Steps

- **Publish plugin**: See [Publishing & Distribution](publishing.md)
- **Review best practices**: See [Best Practices](best-practices.md)
- **See examples**: See [Complete Plugin Examples](../examples/complete-plugins.md)
- **Troubleshooting**: See [Troubleshooting Guide](../troubleshooting.md)
