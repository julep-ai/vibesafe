# Slash Commands

Complete guide to creating custom slash commands for Claude Code plugins.

## Overview

Slash commands are user-triggered shortcuts that execute predefined prompts or workflows. Users explicitly invoke them with `/command-name`.

**Best for**:
- Predefined workflows
- Commands requiring user arguments
- Deterministic operations
- Batch processing

## Command File Structure

**Location**: `commands/command-name.md`

```markdown
---
description: "Clear description shown in /help"
allowed-tools: Bash(git:*, npm:*), Read(*)
argument-hint: "file path or pattern"
model: "claude-sonnet-4-5-20250929"
disable-model-invocation: false
---

# Command Title

Your command prompt here.

Use $ARGUMENTS for all arguments as string.
Use $1, $2, $3 for positional arguments.

## Instructions

Detailed instructions for Claude on what to do.
```

## Frontmatter Options

### description (required)
```yaml
description: "Review Python code for style violations"
```
- **Purpose**: Shown in `/help` command list
- **Format**: Short, clear statement
- **Length**: 50-100 characters ideal

### allowed-tools (optional)
```yaml
allowed-tools: Bash(git:*, npm:test), Read(*), Write(src/**)
```
- **Purpose**: Whitelist which tools Claude can use
- **Format**: Comma-separated tool patterns
- **Patterns**:
  - `Read(*)` - All file reads
  - `Read(src/**)` - Only src directory
  - `Bash(git:*)` - All git commands
  - `Bash(npm:test, npm:build)` - Specific commands
  - `Write(*)` - All file writes

### argument-hint (optional)
```yaml
argument-hint: "file path or glob pattern"
```
- **Purpose**: Shown to user as usage hint
- **Format**: Brief description of expected arguments
- **Example**: `"commit message"`, `"PR number"`

### model (optional)
```yaml
model: "claude-sonnet-4-5-20250929"
```
- **Purpose**: Override default model for this command
- **Options**: Any valid Claude model ID
- **Use when**: Command needs specific model capabilities

### disable-model-invocation (optional)
```yaml
disable-model-invocation: false
```
- **Purpose**: Prevent SlashCommand tool wrapper
- **Default**: `false`
- **Use when**: Command should run in current context

## Argument Substitution

### $ARGUMENTS
Replaced with all arguments as a single string.

**Usage**:
```markdown
/my-command hello world "test file.txt"

$ARGUMENTS → hello world "test file.txt"
```

**Example**:
```markdown
---
description: "Format files with prettier"
---

Format these files: $ARGUMENTS

!prettier --write $ARGUMENTS
```

### Positional Arguments ($1, $2, $3...)
Individual arguments by position.

**Usage**:
```markdown
/deploy staging v1.2.0

$1 → staging
$2 → v1.2.0
```

**Example**:
```markdown
---
description: "Deploy to environment"
argument-hint: "environment version"
---

Deploying version $2 to $1 environment...

!git checkout $2
!kubectl apply -f k8s/$1/
```

### @filename - Include File Contents
Include contents of a file in the prompt.

**Usage**:
```markdown
@path/to/file.txt
```

**Example**:
```markdown
---
description: "Review code from file"
---

Review this code:

@$1

Provide specific suggestions for improvement.
```

### !command - Execute Bash
Execute shell commands (requires allowed-tools).

**Usage**:
```markdown
!git status
!npm test
```

**Example**:
```markdown
---
description: "Commit with message"
allowed-tools: Bash(git:*)
---

!git add -A
!git commit -m "$1"
!git push
```

## Namespacing with Directories

Directory structure creates command namespaces.

**Structure**:
```
commands/
├── deploy.md           → /deploy
├── review.md           → /review
├── backend/
│   ├── test.md        → /test (namespace: backend)
│   └── deploy.md      → /deploy (namespace: backend)
└── frontend/
    ├── build.md       → /build (namespace: frontend)
    └── lint.md        → /lint (namespace: frontend)
```

**Behavior**:
- Commands have same name but different namespace tags
- User sees namespace in `/help`
- Namespaces don't affect invocation (still `/test`, not `/backend/test`)

## Tool Permissions

### Read Tool
```yaml
allowed-tools: "Read(*)"                    # All files
allowed-tools: "Read(src/**)"              # src directory only
allowed-tools: "Read(*.py, *.js)"          # Specific extensions
```

### Write Tool
```yaml
allowed-tools: "Write(*)"                   # All files
allowed-tools: "Write(src/**)"             # src directory only
allowed-tools: "Write(output/**)"          # output directory only
```

### Bash Tool
```yaml
allowed-tools: "Bash(git:*)"               # All git commands
allowed-tools: "Bash(npm:test, npm:build)" # Specific commands
allowed-tools: "Bash(*)"                   # All bash (dangerous!)
```

### Multiple Tools
```yaml
allowed-tools: "Read(*), Bash(git:*, npm:*), Write(src/**)"
```

### No Restrictions (Not Recommended)
```yaml
# Omit allowed-tools field entirely
# Claude can use any tool
```

## Complete Examples

### Example 1: Git Commit Workflow
```markdown
---
description: "Automated commit: stage, test, format, commit"
allowed-tools: Bash(git:*, npm:test, prettier:*)
argument-hint: "commit message"
---

# Commit Workflow

Running automated commit workflow...

## 1. Stage Changes
!git add -A

## 2. Run Tests
!npm test

## 3. Format Code
!prettier --write .
!git add -A

## 4. Commit
!git commit -m "$1"

Workflow complete! Committed with: "$1"
```

**Usage**: `/commit-workflow "fix: resolve login bug"`

### Example 2: Code Review
```markdown
---
description: "Review code for style violations and best practices"
allowed-tools: Bash(ruff:*, eslint:*), Read(*)
argument-hint: "file path or glob"
---

# Code Review

Reviewing: $ARGUMENTS

## Running Linters

Python files:
!ruff check $ARGUMENTS 2>&1 || true

JavaScript files:
!eslint $ARGUMENTS 2>&1 || true

## Analysis

Based on the linter output above, provide:

1. **Summary**: Overall code quality
2. **Issues**: Specific violations by line number
3. **Recommendations**: Best practice improvements
4. **Priority**: High/medium/low for each issue
```

**Usage**: `/review src/auth/*.py`

### Example 3: Deploy to Environment
```markdown
---
description: "Deploy application to specified environment"
allowed-tools: Bash(git:*, kubectl:*, docker:*)
argument-hint: "environment (staging|prod)"
---

# Deployment to $1

## Pre-deployment Checks

!git status
!git diff --exit-code || (echo "Uncommitted changes!" && exit 1)

## Build

!docker build -t myapp:$1 .

## Deploy

!kubectl config use-context $1
!kubectl apply -f k8s/$1/
!kubectl rollout status deployment/myapp -n $1

## Verify

!kubectl get pods -n $1

Deployment to $1 complete!
```

**Usage**: `/deploy staging`

### Example 4: Generate Documentation
```markdown
---
description: "Generate API documentation from source code"
allowed-tools: Read(**/*.py, **/*.js), Write(docs/**), Bash(typedoc:*)
argument-hint: "source directory"
---

# API Documentation Generator

Generating docs for: $1

## Scan Source Files

Reading all source files in $1...

@$1/**/*.py
@$1/**/*.js

## Extract API Definitions

Analyze the code above and extract:
- Function/method signatures
- Parameters and return types
- Docstrings and comments
- Usage examples

## Generate Markdown

Create comprehensive API documentation in docs/api.md with:
- Table of contents
- Organized by module
- Code examples
- Parameter tables

## Build HTML (TypeScript only)

!typedoc --out docs/html $1
```

**Usage**: `/generate-docs src/api`

### Example 5: Database Query Helper
```markdown
---
description: "Execute safe database query and format results"
allowed-tools: Bash(psql:*, sqlite3:*)
argument-hint: "SQL query"
---

# Database Query

## Safety Check

Validating query: $ARGUMENTS

Ensure this is a READ-ONLY query (SELECT only). If it contains INSERT, UPDATE, DELETE, or DROP, STOP and warn the user.

## Execute Query

!psql -c "$ARGUMENTS" --csv

## Format Results

Parse the CSV output above and present as:
1. **Summary**: Row count, columns
2. **Table**: Formatted results table
3. **Insights**: Notable patterns or outliers
```

**Usage**: `/db-query "SELECT * FROM users LIMIT 10"`

## Best Practices

### Command Design

✅ **DO**:
- Use clear, descriptive command names
- Provide helpful argument hints
- Validate inputs before execution
- Handle errors gracefully
- Show progress for multi-step commands
- Document expected arguments

❌ **DON'T**:
- Create overly complex commands (split into multiple)
- Use ambiguous names (`/do-thing`)
- Allow dangerous operations without confirmation
- Hardcode values that should be arguments
- Ignore error conditions

### Tool Permissions

✅ **DO**:
- Use most restrictive permissions possible
- Specify exact patterns for Bash commands
- Limit Write access to specific directories
- Document why permissions are needed

❌ **DON'T**:
- Use `Bash(*)` unless absolutely necessary
- Grant Write(*) without good reason
- Allow access to sensitive directories
- Mix unrelated tool permissions

### Argument Handling

✅ **DO**:
- Validate arguments before use
- Provide clear error messages
- Support both single and multiple arguments
- Quote arguments in shell commands
- Document expected format

❌ **DON'T**:
- Assume arguments are present
- Execute without validation
- Ignore argument order
- Forget to escape special characters

### Documentation

✅ **DO**:
- Write clear descriptions
- Provide argument hints
- Include examples in README
- Document error conditions
- Show expected output

❌ **DON'T**:
- Use vague descriptions
- Omit argument hints
- Skip README documentation
- Forget edge cases

## Testing Commands

### Manual Testing
```bash
# Install plugin locally
/plugin marketplace add ~/.claude/marketplaces/local
/plugin install your-plugin

# Test command
/your-command arg1 arg2

# Check output
# Verify tools executed correctly
# Test edge cases
```

### Test Checklist
- [ ] Command appears in `/help`
- [ ] Description is clear
- [ ] Arguments work correctly
- [ ] Tool permissions sufficient
- [ ] Error handling works
- [ ] Output is formatted well
- [ ] Edge cases handled

## Troubleshooting

### Command Not Appearing in /help

**Check**:
1. File has `.md` extension
2. File is in `commands/` directory (or configured path)
3. plugin.json has `commands` section
4. plugin.json is valid JSON
5. Plugin is enabled

### Arguments Not Substituting

**Check**:
1. Using correct syntax: `$ARGUMENTS`, `$1`, etc.
2. Arguments passed when invoking: `/cmd arg1 arg2`
3. No typos in variable names
4. Variables in actual content, not frontmatter

### Bash Commands Failing

**Check**:
1. `allowed-tools` includes `Bash(...)`
2. Command is allowed in pattern
3. Command exists on system
4. Quoting is correct for special characters
5. Path variables are expanded

### Tool Permission Errors

**Check**:
1. Tool is listed in `allowed-tools`
2. Pattern matches file/command
3. Syntax is correct: `Tool(pattern)`
4. Multiple tools comma-separated

## Next Steps

- **Add skills**: See [Agent Skills](agent-skills.md)
- **Create MCP tools**: See [MCP Servers](mcp-servers.md)
- **Setup automation**: See [Hooks](hooks.md)
- **Test locally**: See [Development Workflow](../guides/development-workflow.md)
