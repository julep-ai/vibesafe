# Plugin Manifest (plugin.json)

Complete reference for the required plugin.json configuration file.

## Location

**Required location**: `.claude-plugin/plugin.json`

This file **must** exist in the `.claude-plugin/` directory at your plugin root.

## Complete Schema

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "email": "you@example.com",
  "description": "Clear, specific description of what the plugin does (max 1024 chars)",
  "repository": "https://github.com/username/my-plugin",
  "license": "MIT",

  "commands": {
    "path": "commands",
    "enabled": true
  },

  "skills": {
    "path": "skills",
    "enabled": true
  },

  "agents": {
    "path": "agents",
    "enabled": true
  },

  "hooks": {
    "path": "hooks",
    "enabled": true
  },

  "mcp": {
    "servers": {
      "server-name": {
        "type": "stdio",
        "command": "node server.js"
      },
      "another-server": {
        "type": "http",
        "url": "http://localhost:8080"
      }
    }
  }
}
```

## Required Fields

### name
- **Type**: String
- **Format**: Lowercase letters, numbers, hyphens only
- **Max length**: 64 characters
- **Purpose**: Plugin identifier used in commands

**Valid examples**:
```json
"name": "my-plugin"
"name": "api-tools-v2"
"name": "db-helper"
```

**Invalid examples**:
```json
"name": "My_Plugin"      // ❌ Uppercase and underscore
"name": "plugin.name"    // ❌ Dots not allowed
"name": "my plugin"      // ❌ Spaces not allowed
```

### version
- **Type**: String
- **Format**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Purpose**: Version tracking, updates

**Format**: `major.minor.patch`
- **Major**: Breaking changes (1.0.0 → 2.0.0)
- **Minor**: New features, backward compatible (1.0.0 → 1.1.0)
- **Patch**: Bug fixes (1.0.0 → 1.0.1)

**Examples**:
```json
"version": "1.0.0"       // Initial release
"version": "1.2.5"       // 2 features, 5 patches
"version": "2.0.0"       // Breaking change
```

### description
- **Type**: String
- **Max length**: 1024 characters
- **Purpose**: Shown in marketplace, plugin list
- **Should include**: What it does, who it's for, main features

**Good examples**:
```json
"description": "Git workflow automation with commands for commits, PR creation, and code review. Includes pre-commit hooks for formatting and linting. Ideal for teams using GitHub."
```

**Poor examples**:
```json
"description": "Useful tools"  // ❌ Too vague
```

## Optional Fields

### author
- **Type**: String
- **Purpose**: Plugin creator name
- **Example**: `"author": "Jane Smith"`

### email
- **Type**: String
- **Format**: Valid email address
- **Purpose**: Contact information
- **Example**: `"email": "jane@example.com"`

### repository
- **Type**: String
- **Format**: Valid URL
- **Purpose**: Source code location, used for updates
- **Example**: `"repository": "https://github.com/username/plugin"`

### license
- **Type**: String
- **Purpose**: Legal license
- **Common values**: MIT, Apache-2.0, GPL-3.0, ISC
- **Example**: `"license": "MIT"`

## Component Configuration

All component sections are **optional**. Only include what your plugin provides.

### commands
```json
"commands": {
  "path": "commands",      // Relative path to commands directory
  "enabled": true          // Enable/disable all commands
}
```

- **path**: Directory containing `.md` command files
- **enabled**: Boolean to enable/disable component
- **Default path**: `"commands"`

### skills
```json
"skills": {
  "path": "skills",        // Relative path to skills directory
  "enabled": true
}
```

- **path**: Directory containing skill folders with `SKILL.md` files
- **enabled**: Boolean to enable/disable component
- **Default path**: `"skills"`

### agents
```json
"agents": {
  "path": "agents",        // Relative path to agents directory
  "enabled": true
}
```

- **path**: Directory containing `.md` agent files
- **enabled**: Boolean to enable/disable component
- **Default path**: `"agents"`

### hooks
```json
"hooks": {
  "path": "hooks",         // Relative path to hooks directory
  "enabled": true
}
```

- **path**: Directory containing `.json` hook files
- **enabled**: Boolean to enable/disable component
- **Default path**: `"hooks"`

## MCP Server Configuration

### stdio Server (Node.js/Python)
```json
"mcp": {
  "servers": {
    "my-server": {
      "type": "stdio",
      "command": "node server.js"
    }
  }
}
```

### HTTP Server
```json
"mcp": {
  "servers": {
    "my-server": {
      "type": "http",
      "url": "http://localhost:8080"
    }
  }
}
```

### SSE (Server-Sent Events) Server
```json
"mcp": {
  "servers": {
    "my-server": {
      "type": "sse",
      "url": "http://localhost:8080/events"
    }
  }
}
```

### Multiple Servers
```json
"mcp": {
  "servers": {
    "weather-api": {
      "type": "stdio",
      "command": "node weather-server.js"
    },
    "database": {
      "type": "http",
      "url": "http://localhost:5432"
    }
  }
}
```

## Validation

### Using jq (Command Line)

**Check valid JSON**:
```bash
jq . .claude-plugin/plugin.json
```

**Extract specific fields**:
```bash
jq '.name, .version, .description' .claude-plugin/plugin.json
```

**Validate name format**:
```bash
jq -r '.name' .claude-plugin/plugin.json | grep -E '^[a-z0-9-]{1,64}$'
```

**Check version format**:
```bash
jq -r '.version' .claude-plugin/plugin.json | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$'
```

### Common Validation Errors

**Invalid JSON syntax**:
```json
{
  "name": "my-plugin",
  "version": "1.0.0",  // ❌ Trailing comma before closing brace
}
```

**Name format error**:
```json
{
  "name": "My_Plugin"  // ❌ Must be lowercase-hyphens only
}
```

**Missing required fields**:
```json
{
  "name": "my-plugin"
  // ❌ Missing version and description
}
```

**Invalid version**:
```json
{
  "version": "v1.0"     // ❌ Must be X.Y.Z format
}
```

## Minimal Examples

### Plugin with Commands Only
```json
{
  "name": "quick-commands",
  "version": "1.0.0",
  "description": "Quick productivity commands for daily tasks",

  "commands": {
    "path": "commands"
  }
}
```

### Plugin with Skills Only
```json
{
  "name": "pdf-tools",
  "version": "1.0.0",
  "description": "PDF extraction and analysis skills",

  "skills": {
    "path": "skills"
  }
}
```

### Plugin with MCP Server Only
```json
{
  "name": "weather-tools",
  "version": "1.0.0",
  "description": "Weather API integration via MCP",

  "mcp": {
    "servers": {
      "weather": {
        "type": "stdio",
        "command": "node weather-server.js"
      }
    }
  }
}
```

### Complete Plugin (All Components)
```json
{
  "name": "dev-toolkit",
  "version": "1.0.0",
  "author": "Dev Team",
  "email": "team@example.com",
  "description": "Complete development toolkit with commands, skills, and automation",
  "repository": "https://github.com/team/dev-toolkit",
  "license": "MIT",

  "commands": {
    "path": "commands",
    "enabled": true
  },

  "skills": {
    "path": "skills",
    "enabled": true
  },

  "agents": {
    "path": "agents",
    "enabled": true
  },

  "hooks": {
    "path": "hooks",
    "enabled": true
  },

  "mcp": {
    "servers": {
      "api-tools": {
        "type": "stdio",
        "command": "node mcp/api-server.js"
      }
    }
  }
}
```

## Path Resolution

All paths in plugin.json are **relative to the plugin root** (where `.claude-plugin/` is located).

**Plugin structure**:
```
my-plugin/                    ← Plugin root
├── .claude-plugin/
│   └── plugin.json          ← paths start from parent directory
├── commands/                ← "path": "commands"
├── skills/                  ← "path": "skills"
└── custom-commands/         ← "path": "custom-commands"
```

**Valid paths**:
```json
"commands": {
  "path": "commands"          // → my-plugin/commands/
}

"commands": {
  "path": "src/commands"      // → my-plugin/src/commands/
}

"commands": {
  "path": "./commands"        // → my-plugin/commands/
}
```

**Invalid paths**:
```json
"commands": {
  "path": "/commands"         // ❌ Absolute paths not allowed
}

"commands": {
  "path": "../commands"       // ❌ Parent directory not allowed
}
```

## Best Practices

### Versioning Strategy

**Initial release**:
```json
"version": "1.0.0"
```

**Adding new command** (backward compatible):
```json
"version": "1.1.0"           // Increment minor
```

**Bug fix** (no API changes):
```json
"version": "1.0.1"           // Increment patch
```

**Breaking change** (removed command, changed args):
```json
"version": "2.0.0"           // Increment major
```

### Description Writing

**Formula**: What + For Whom + Key Features

```json
"description": "Git workflow automation for teams using GitHub. Includes commands for commits, PR creation, code review, and pre-commit hooks for formatting. Supports monorepos and conventional commits."
```

**Include**:
- Primary purpose
- Target users
- Main features (3-5 items)
- Compatible systems/tools

**Avoid**:
- Marketing language ("amazing", "revolutionary")
- Vague terms ("helps with things")
- Excessive length (>500 chars for clarity)

### Component Organization

**Enable only what you provide**:
```json
{
  "commands": { "path": "commands" },
  "skills": { "path": "skills" }
  // ✅ Only commands and skills, no hooks/agents
}
```

**Don't include empty components**:
```json
{
  "commands": { "path": "commands" },
  "hooks": { "path": "hooks" }      // ❌ If hooks/ is empty
}
```

## Troubleshooting

### Plugin Won't Install

**Check**:
1. Valid JSON syntax: `jq . .claude-plugin/plugin.json`
2. Required fields present: name, version, description
3. Name format: lowercase-hyphens only
4. File location: `.claude-plugin/plugin.json` (exact path)

### Commands Not Loading

**Check**:
1. `commands.path` points to existing directory
2. Directory contains `.md` files
3. `commands.enabled` is `true` (or omitted, defaults true)

### MCP Server Won't Start

**Check**:
1. `command` path is correct relative to plugin root
2. Server file has execute permissions (Unix)
3. Server type matches implementation (stdio/http/sse)
4. Dependencies are installed (for Node/Python servers)

## Next Steps

- **Create commands**: See [Slash Commands](slash-commands.md)
- **Build skills**: See [Agent Skills](agent-skills.md)
- **Add MCP servers**: See [MCP Servers](mcp-servers.md)
- **Configure hooks**: See [Hooks](hooks.md)
