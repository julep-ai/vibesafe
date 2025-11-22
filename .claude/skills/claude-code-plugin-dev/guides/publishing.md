# Publishing & Distribution

Complete guide to publishing and distributing Claude Code plugins.

## Pre-Publishing Checklist

Before publishing your plugin, ensure:

### Documentation
- [ ] README.md with clear description
- [ ] Installation instructions
- [ ] Usage examples for all components
- [ ] Configuration documentation
- [ ] License file (MIT, Apache, etc.)
- [ ] CHANGELOG.md for version history

### Validation
- [ ] plugin.json is valid JSON
- [ ] Name follows format: lowercase-hyphens (max 64 chars)
- [ ] Version follows semantic versioning
- [ ] Description is clear and complete (max 1024 chars)
- [ ] All referenced paths exist
- [ ] No hardcoded secrets or API keys

### Testing
- [ ] All commands tested and working
- [ ] Skills activate correctly
- [ ] MCP servers start without errors
- [ ] Hooks execute properly
- [ ] No breaking errors
- [ ] Edge cases handled

### Code Quality
- [ ] No console.log() or debug code
- [ ] Error messages are user-friendly
- [ ] Code is formatted consistently
- [ ] Comments explain complex logic
- [ ] TODOs are removed or documented

## Publishing to GitHub

### 1. Initialize Git Repository

```bash
cd your-plugin
git init
```

### 2. Create .gitignore

```gitignore
# .gitignore

# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# Environment files
.env
.env.local
*.key
secrets/

# OS files
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Build files
dist/
build/
*.log

# Test files
coverage/
.pytest_cache/
```

### 3. Create README.md

```markdown
# Your Plugin Name

Brief description of what your plugin does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

\`\`\`bash
/plugin install username/your-plugin
\`\`\`

## Usage

### Commands

**`/command-name`** - Description
\`\`\`bash
/command-name arg1 arg2
\`\`\`

### Skills

**skill-name** - Activates when you ask about X, Y, Z

### Tools

**tool_name** - Description of what it does

## Configuration

Any configuration needed (API keys, etc.)

## Examples

Detailed examples of usage

## License

MIT
```

### 4. Commit and Push

```bash
# Stage all files
git add .

# Create initial commit
git commit -m "Initial release: v1.0.0"

# Create GitHub repo (via gh CLI or web interface)
gh repo create your-plugin --public --source=.

# Or add remote manually
git remote add origin https://github.com/username/your-plugin.git

# Push to GitHub
git push -u origin main

# Tag version
git tag v1.0.0
git push origin v1.0.0
```

### 5. Users Install

Users can now install your plugin:

```bash
/plugin install username/your-plugin
```

## Semantic Versioning

Use semantic versioning: `MAJOR.MINOR.PATCH`

### Version Guidelines

**MAJOR** (X.0.0) - Breaking changes:
- Removed commands, skills, or tools
- Changed command arguments (non-backward compatible)
- Changed tool interfaces
- Removed required parameters

Examples:
- `1.5.2 → 2.0.0`: Removed `/deploy` command
- `1.3.0 → 2.0.0`: Changed `/commit` to require 2 args instead of 1

**MINOR** (x.X.0) - New features (backward compatible):
- New commands, skills, or tools
- New optional parameters
- New functionality that doesn't break existing

Examples:
- `1.2.0 → 1.3.0`: Added new `/test` command
- `1.4.0 → 1.5.0`: Added optional `--verbose` flag

**PATCH** (x.x.X) - Bug fixes:
- Bug fixes
- Documentation updates
- Performance improvements
- No API changes

Examples:
- `1.2.3 → 1.2.4`: Fixed `/deploy` error handling
- `1.5.0 → 1.5.1`: Updated README

### Updating Version

```bash
# Update plugin.json
jq '.version = "1.1.0"' .claude-plugin/plugin.json > tmp.json
mv tmp.json .claude-plugin/plugin.json

# Commit changes
git add .
git commit -m "Release v1.1.0: Add new features"

# Tag release
git tag v1.1.0
git push origin main v1.1.0
```

## Creating Organization Marketplace

For teams sharing multiple plugins internally.

### 1. Create Marketplace Repository

```bash
mkdir company-plugins
cd company-plugins

# Create directory structure
mkdir -p .claude-plugin

# Create marketplace.json
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "Company Plugins",
  "owner": "Acme Corporation",
  "description": "Official plugins for Acme engineering teams",
  "plugins": []
}
EOF

# Initialize git
git init
git add .
git commit -m "Initial marketplace setup"
gh repo create company/plugins --public --source=.
git push -u origin main
```

### 2. Add Plugins to Marketplace

Edit `.claude-plugin/marketplace.json`:

```json
{
  "name": "Company Plugins",
  "owner": "Acme Corporation",
  "description": "Official plugins for Acme engineering teams",
  "plugins": [
    {
      "name": "dev-tools",
      "source": "github",
      "repo": "company/dev-tools-plugin",
      "description": "Development workflow tools",
      "version": "1.0.0",
      "author": "DevOps Team"
    },
    {
      "name": "api-helpers",
      "source": "github",
      "repo": "company/api-helpers-plugin",
      "description": "API documentation and testing tools",
      "version": "2.1.0",
      "author": "API Team"
    }
  ]
}
```

### 3. Team Members Use Marketplace

```bash
# Add company marketplace
/plugin marketplace add company/plugins

# Browse and install plugins
/plugin
/plugin install dev-tools
/plugin install api-helpers
```

### 4. Update Marketplace

```bash
# Edit marketplace.json to add/update plugins
vim .claude-plugin/marketplace.json

# Commit and push
git add .
git commit -m "Add new plugin: database-tools"
git push

# Team members refresh
/plugin marketplace refresh
```

## Plugin Sources

Plugins can be installed from multiple sources:

### GitHub Repositories
```bash
/plugin install username/repo-name
```

### Local Directories
```bash
/plugin install /absolute/path/to/plugin
/plugin install ~/my-plugins/custom-plugin
```

### Git URLs
```bash
/plugin install https://github.com/user/plugin.git
```

### Relative Paths (in marketplace.json)
```json
{
  "plugins": [
    {
      "name": "local-plugin",
      "source": "./plugins/local-plugin"
    }
  ]
}
```

## Distribution Best Practices

### Version Management

✅ **DO**:
- Follow semantic versioning strictly
- Tag all releases in git
- Update CHANGELOG.md
- Document breaking changes
- Increment version for all releases

❌ **DON'T**:
- Skip version updates
- Reuse version numbers
- Make breaking changes in patches
- Forget to tag releases
- Skip changelog updates

### Documentation

✅ **DO**:
- Provide comprehensive README
- Include usage examples
- Document all features
- Explain configuration
- List requirements/dependencies

❌ **DON'T**:
- Assume users know how it works
- Skip installation instructions
- Forget to document breaking changes
- Omit configuration details
- Leave TODOs in public docs

### Security

✅ **DO**:
- Use environment variables for secrets
- Document security requirements
- Validate all inputs
- Use restrictive tool permissions
- Review code before publishing

❌ **DON'T**:
- Commit API keys or tokens
- Use overly permissive tool access
- Skip input validation
- Ignore security warnings
- Publish without security review

### Maintenance

✅ **DO**:
- Respond to issues
- Review pull requests
- Keep dependencies updated
- Fix reported bugs
- Maintain documentation

❌ **DON'T**:
- Ignore user feedback
- Let dependencies rot
- Skip security updates
- Abandon the project silently
- Break backward compatibility without notice

## Publishing Checklist

Before each release:

### Code
- [ ] All features working as documented
- [ ] Tests passing
- [ ] No debug code
- [ ] Error handling complete
- [ ] Code formatted consistently

### Documentation
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] Version number bumped
- [ ] Examples tested
- [ ] Breaking changes documented

### Testing
- [ ] Installed and tested locally
- [ ] All components verified
- [ ] Edge cases handled
- [ ] No breaking changes (or documented)
- [ ] Works on fresh install

### Git
- [ ] All changes committed
- [ ] Version tagged
- [ ] Pushed to GitHub
- [ ] Release notes created
- [ ] Previous versions work

### Security
- [ ] No secrets committed
- [ ] Dependencies reviewed
- [ ] Permissions appropriate
- [ ] Input validation complete
- [ ] Security issues addressed

## Release Process

### 1. Prepare Release

```bash
# Update version
vim .claude-plugin/plugin.json

# Update CHANGELOG
vim CHANGELOG.md

# Run tests
./test-plugin.sh

# Commit
git add .
git commit -m "Prepare release v1.2.0"
```

### 2. Create Release

```bash
# Tag version
git tag -a v1.2.0 -m "Release v1.2.0"

# Push
git push origin main v1.2.0
```

### 3. Create GitHub Release

```bash
# Using gh CLI
gh release create v1.2.0 \
  --title "Version 1.2.0" \
  --notes "
## Features
- Added new /deploy command
- Improved error handling

## Bug Fixes
- Fixed skill activation issue
- Corrected MCP server timeout

## Breaking Changes
None
"
```

Or create release manually on GitHub:
1. Go to Releases
2. Click "Create a new release"
3. Select tag v1.2.0
4. Add release notes
5. Publish

### 4. Announce Release

- Update README if needed
- Notify users (if you have a channel)
- Update marketplace listing
- Post in community forums

## Continuous Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Test Plugin

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Validate plugin.json
      run: |
        jq empty .claude-plugin/plugin.json

    - name: Check name format
      run: |
        NAME=$(jq -r '.name' .claude-plugin/plugin.json)
        echo "$NAME" | grep -E '^[a-z0-9-]{1,64}$'

    - name: Check version format
      run: |
        VERSION=$(jq -r '.version' .claude-plugin/plugin.json)
        echo "$VERSION" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$'

    - name: Test MCP servers
      run: |
        if [ -f mcp/server.js ]; then
          node -c mcp/server.js
        fi

    - name: Validate hooks
      run: |
        for hook in hooks/*.json; do
          [ -f "$hook" ] && jq empty "$hook"
        done
```

## Migration Guide Template

When making breaking changes, provide migration guide:

```markdown
# Migration Guide: v1.x to v2.0

## Breaking Changes

### Command Renamed
**Before**:
\`\`\`bash
/old-command arg
\`\`\`

**After**:
\`\`\`bash
/new-command arg
\`\`\`

### Parameter Added
**Before**:
\`\`\`bash
/deploy
\`\`\`

**After** (now requires environment):
\`\`\`bash
/deploy staging
\`\`\`

## Automated Migration

We provide a script to help migrate:
\`\`\`bash
./migrate-to-v2.sh
\`\`\`
```

## Next Steps

- **Development workflow**: See [Development Workflow](development-workflow.md)
- **Best practices**: See [Best Practices](best-practices.md)
- **Examples**: See [Complete Plugin Examples](../examples/complete-plugins.md)
