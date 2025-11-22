# Plugin Structure & Architecture

Complete guide to Claude Code plugin architecture, file organization, and component types.

## Plugin Component Types

Claude Code plugins can include any combination of five component types:

### 1. Slash Commands (`commands/`)
- **Trigger**: Manual user invocation (`/command`)
- **Best for**: Predefined workflows, shortcuts, batch operations
- **Example**: `/commit-workflow`, `/review-code`, `/deploy-staging`

### 2. Agent Skills (`skills/`)
- **Trigger**: Automatic (Claude decides based on context)
- **Best for**: Context-aware capabilities, file processing, domain expertise
- **Example**: PDF extraction, SQL analysis, API documentation

### 3. Subagents (`agents/`)
- **Trigger**: Explicit delegation or automatic
- **Best for**: Complex multi-step tasks, specialized workflows
- **Example**: Code review agent, testing agent, deployment agent

### 4. MCP Servers (`mcp/`)
- **Trigger**: Claude invokes tools via Model Context Protocol
- **Best for**: API integrations, database access, external services
- **Example**: Weather API, database queries, file system operations

### 5. Hooks (`hooks/`)
- **Trigger**: Lifecycle events (tool use, prompt submit, etc.)
- **Best for**: Automation, formatting, validation, notifications
- **Example**: Auto-format on save, pre-commit checks, logging

## Required Directory Structure

```
my-plugin/
├── .claude-plugin/
│   ├── plugin.json              # REQUIRED - Plugin manifest
│   └── marketplace.json         # Optional - For marketplace creation
│
├── commands/                    # Slash commands
│   ├── command-name.md         # Becomes /command-name
│   └── namespace/              # Creates command namespace
│       └── sub-command.md      # Becomes /sub-command (namespace: namespace)
│
├── skills/                      # Agent Skills (2025 schema)
│   ├── skill-name/
│   │   ├── SKILL.md           # REQUIRED - Must be named SKILL.md
│   │   ├── reference.md       # Optional - Additional docs
│   │   └── examples/          # Optional - Example files
│   └── another-skill/
│       └── SKILL.md
│
├── agents/                      # Subagent definitions
│   ├── agent-name.md
│   └── another-agent.md
│
├── hooks/                       # Event handlers
│   ├── hooks.json             # Hook configurations
│   └── pre-commit.json        # Can split into multiple files
│
├── mcp/                         # MCP server implementations
│   ├── server-name.ts         # TypeScript server
│   ├── server-name.js         # JavaScript server
│   └── server-name.py         # Python server
│
└── README.md                    # Plugin documentation
```

## File Naming Conventions

### Plugin Name (in plugin.json)
- **Format**: Lowercase letters, numbers, hyphens only
- **Max length**: 64 characters
- **Valid**: `my-awesome-plugin`, `db-tools-v2`, `api-helper`
- **Invalid**: `My_Plugin`, `plugin.name`, `PLUGIN`

### Command Files
- **Extension**: `.md` (Markdown)
- **Naming**: Hyphens become part of command name
- **Example**: `deploy-staging.md` → `/deploy-staging`

### Skill Folders
- **Folder name**: Lowercase with hyphens (becomes skill ID)
- **Required file**: `SKILL.md` (exact case)
- **Example**: `pdf-extraction/SKILL.md`

### Agent Files
- **Extension**: `.md` (Markdown)
- **Naming**: Lowercase with hyphens
- **Example**: `code-reviewer.md`

### Hook Files
- **Extension**: `.json` (JSON)
- **Naming**: Descriptive of purpose
- **Example**: `pre-commit.json`, `post-edit.json`

### MCP Server Files
- **Extension**: `.ts`, `.js`, `.py`
- **Naming**: Match server name in plugin.json
- **Example**: `weather-api.ts`, `db-tools.py`

## Plugin Scope Hierarchy

Plugins can exist at three scope levels with specific precedence rules:

### 1. Project Scope (`.claude/`)
- **Location**: Project root `.claude/` directory
- **Sharing**: Committed to git, shared with team
- **Precedence**: **Highest** - Overrides user and installed plugins
- **Use when**: Team needs shared commands, project-specific workflows

```bash
project-root/
└── .claude/
    ├── commands/
    ├── skills/
    └── settings.json
```

### 2. User Scope (`~/.claude/`)
- **Location**: User home directory
- **Sharing**: Personal, not shared
- **Precedence**: **Medium** - Overrides installed plugins
- **Use when**: Personal productivity tools, cross-project utilities

```bash
~/.claude/
├── commands/
├── skills/
└── settings.json
```

### 3. Plugin Scope (Installed from Marketplace)
- **Location**: Claude Code plugin directory
- **Sharing**: Installed via `/plugin install`
- **Precedence**: **Lowest** - Can be overridden by project/user
- **Use when**: Distributing reusable plugins, community tools

## Precedence Rules

When components have the same name across scopes:

```
Project (.claude/)
    ↓ overrides
User (~/.claude/)
    ↓ overrides
Installed Plugin
```

**Example**:
- Project has `/deploy` command → Uses project version
- User has `/deploy` command → Uses user version (if no project version)
- Plugin has `/deploy` command → Uses plugin version (if no project/user version)

## Minimal Plugin Requirements

The absolute minimum for a valid plugin:

```
my-plugin/
└── .claude-plugin/
    └── plugin.json
```

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What my plugin does"
}
```

This creates a valid (but empty) plugin. Add components as needed.

## Component Interaction Patterns

### Commands Calling Skills
Commands can trigger skill activation by using relevant keywords:

```markdown
---
description: "Analyze PDF document"
---

Please extract and analyze the text from this PDF: $ARGUMENTS
```

Claude sees "extract" and "PDF" and may activate a PDF extraction skill.

### Skills Using MCP Tools
Skills can specify which MCP tools they need:

```yaml
---
name: database-analyst
allowed-tools: "mcp__db-tools__execute_query"
---
```

### Hooks Running After Commands
Hooks can trigger after slash commands finish:

```json
{
  "event": "Stop",
  "action": {
    "type": "command",
    "command": "echo 'Command completed' >> ~/log.txt"
  }
}
```

### Agents Delegating to Other Agents
Subagents can be composed hierarchically for complex workflows.

## Plugin Loading Order

When Claude Code starts:

1. **Load system defaults** (built-in Claude Code features)
2. **Load installed plugins** (from marketplace)
3. **Load user scope** (`~/.claude/`) - Overrides plugins
4. **Load project scope** (`.claude/`) - Overrides user and plugins
5. **Register all components** (commands, skills, hooks, etc.)
6. **Start MCP servers** (if configured)

## Environment Variables

Available during plugin execution:

- `CLAUDE_PROJECT_DIR`: Project root directory
- `CLAUDE_PLUGIN_ROOT`: Plugin installation directory
- `CLAUDE_ENV_FILE`: File for persisting environment variables
- Standard system environment variables

## Best Practices

### File Organization

✅ **DO**:
- Group related commands in subdirectories (creates namespaces)
- Keep skill documentation in skill folders
- Use descriptive file names
- Include README.md for documentation

❌ **DON'T**:
- Mix unrelated components in same directory
- Use spaces or special characters in file names
- Create deeply nested structures (max 2-3 levels)
- Commit large binary files

### Component Selection

**Use Commands when**:
- User needs explicit control
- Workflow is deterministic
- Arguments are required

**Use Skills when**:
- Capability should activate automatically
- Context determines when to use
- No user input needed

**Use MCP when**:
- Integrating external APIs
- Database access needed
- Tool has specific parameters

**Use Hooks when**:
- Automation is required
- Event-driven behavior needed
- No user interaction wanted

### Naming Strategy

**Descriptive names**:
```
✅ pdf-text-extractor
✅ sql-query-analyzer
✅ git-commit-workflow
```

**Avoid generic names**:
```
❌ utils
❌ helper
❌ tools
```

## Directory Size Recommendations

- **Small plugin**: 1-5 components, <100KB
- **Medium plugin**: 5-15 components, <500KB
- **Large plugin**: 15+ components, <2MB

Keep plugins focused. If exceeding these sizes, consider splitting into multiple plugins.

## Next Steps

- **Configure manifest**: See [Plugin Manifest](plugin-manifest.md)
- **Create commands**: See [Slash Commands](slash-commands.md)
- **Build skills**: See [Agent Skills](agent-skills.md)
- **Add tools**: See [MCP Servers](mcp-servers.md)
- **Setup hooks**: See [Hooks](hooks.md)
