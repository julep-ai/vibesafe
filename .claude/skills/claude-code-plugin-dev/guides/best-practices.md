# Best Practices

Essential guidelines for building secure, maintainable, and effective Claude Code plugins.

## Plugin Design Principles

### Single Responsibility
Each plugin should have a clear, focused purpose.

✅ **Good**:
- `git-workflow` - Git operations and workflows
- `pdf-tools` - PDF processing and extraction
- `api-docs` - API documentation generation

❌ **Bad**:
- `utils` - Random assortment of unrelated tools
- `everything` - Tries to do too much
- `helper` - Vague, unfocused purpose

### Composability
Design components to work together and with other plugins.

✅ **Good**:
- Skill provides capability, command uses it
- MCP tool does one thing well
- Hook integrates with existing workflows

❌ **Bad**:
- Components tightly coupled
- Duplicate functionality
- Incompatible with standard tools

### User-Centered Design
Design for the user's workflow, not implementation convenience.

✅ **Good**:
- Clear, descriptive command names
- Intuitive argument order
- Helpful error messages
- Good documentation

❌ **Bad**:
- Cryptic abbreviations
- Confusing argument order
- Technical error messages
- Minimal documentation

## Security Best Practices

### Never Commit Secrets

✅ **Good**:
```typescript
const apiKey = process.env.API_KEY;
if (!apiKey) {
  return { error: "API_KEY environment variable not set" };
}
```

❌ **Bad**:
```typescript
const apiKey = "hardcoded-secret-key-123";  // ❌ Never do this!
```

### Validate All Inputs

✅ **Good**:
```typescript
if (!city || typeof city !== 'string') {
  return { error: "City must be a non-empty string" };
}

if (city.length > 100) {
  return { error: "City name too long" };
}

if (!/^[a-zA-Z\s-]+$/.test(city)) {
  return { error: "City name contains invalid characters" };
}
```

❌ **Bad**:
```typescript
// No validation, accepts any input
const result = await fetchData(userInput);
```

### Restrictive Tool Permissions

✅ **Good**:
```yaml
# Specific, minimal permissions
allowed-tools: "Read(*.pdf), Bash(pdftotext:*), Write(output/*.txt)"
```

❌ **Bad**:
```yaml
# Overly permissive
allowed-tools: "Bash(*), Write(*), Read(*)"
```

### Sanitize File Paths

✅ **Good**:
```bash
# Quote paths, validate
if [[ "$FILE_PATH" =~ ^[a-zA-Z0-9/_.-]+$ ]]; then
  prettier --write "$FILE_PATH"
fi
```

❌ **Bad**:
```bash
# Unquoted, unvalidated
prettier --write $FILE_PATH
```

### Use Environment Variables

✅ **Good**:
```json
{
  "servers": {
    "my-server": {
      "type": "stdio",
      "command": "node server.js",
      "env": {
        "API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

❌ **Bad**:
```json
{
  "command": "API_KEY=hardcoded node server.js"
}
```

## Performance Best Practices

### Keep Operations Fast

✅ **Good**:
- Commands complete in <5 seconds
- Hooks complete in <10 seconds
- Cache expensive operations
- Use async operations
- Paginate large datasets

❌ **Bad**:
- Synchronous, blocking operations
- No caching
- Load entire datasets
- Ignore timeouts
- Sequential when parallel possible

### Set Appropriate Timeouts

```json
{
  "timeout": 10,     // ✅ Quick operations
  "timeout": 60,     // ✅ Tests, builds
  "timeout": 300     // ❌ Too long, use async instead
}
```

### Limit Result Sizes

✅ **Good**:
```typescript
const limit = Math.min(input.limit || 100, 1000);  // Cap at 1000
const results = await query(input.query, limit);
```

❌ **Bad**:
```typescript
// No limit, could return millions of rows
const results = await query(input.query);
```

### Use Efficient Algorithms

✅ **Good**:
- Index lookups instead of scans
- Stream large files
- Process in batches
- Use database queries efficiently

❌ **Bad**:
- Load entire database into memory
- O(n²) algorithms on large datasets
- Repeated API calls
- No caching

## Code Quality

### Error Handling

✅ **Good**:
```typescript
try {
  const result = await externalAPI(input);
  return { success: true, data: result };
} catch (error) {
  if (error.code === 'RATE_LIMIT') {
    return {
      success: false,
      error: "Rate limit exceeded. Please try again in 1 minute.",
      retryable: true
    };
  }
  return {
    success: false,
    error: `API error: ${error.message}`
  };
}
```

❌ **Bad**:
```typescript
// No error handling
const result = await externalAPI(input);
return result;
```

### Descriptive Names

✅ **Good**:
```yaml
name: pdf-text-extractor
description: "Extracts text content from PDF files..."
```

```typescript
async function extractPdfText(filePath: string): Promise<string>
```

❌ **Bad**:
```yaml
name: pdf-tool
description: "Does PDF stuff"
```

```typescript
async function doIt(x: string): Promise<any>
```

### Documentation

✅ **Good**:
```typescript
/**
 * Fetches current weather for a location.
 *
 * @param city - City name (e.g., "London")
 * @param country - Optional ISO country code (e.g., "GB")
 * @returns Weather data including temperature, conditions, and humidity
 * @throws {Error} If API request fails or city not found
 */
async function getWeather(city: string, country?: string)
```

❌ **Bad**:
```typescript
// Gets weather
async function getWeather(city, country)
```

### Consistent Style

✅ **Good**:
- Use linter (ESLint, Ruff)
- Follow language conventions
- Consistent indentation
- Meaningful variable names
- Clear code structure

❌ **Bad**:
- No formatting
- Mixed styles
- Inconsistent naming
- Poor structure

## Skill Activation Best Practices

### Write Specific Descriptions

✅ **Good**:
```yaml
description: "Extracts text from PDF files using pdftotext and OCR, handling multi-page documents and scanned images. Use when user asks to extract text from PDF, read PDF contents, convert PDF to text, or analyze PDF documents."
```

**Why it works**:
- Mentions file type (PDF) explicitly
- Lists tools used (pdftotext, OCR)
- Includes activation keywords (extract, read, convert, analyze)
- Describes capabilities (multi-page, scanned)

❌ **Bad**:
```yaml
description: "Helps with documents"
```

**Why it fails**:
- No file type mentioned
- No specific actions
- No activation keywords
- Too vague

### Include Action Keywords

Include these keyword types:

**File types**: PDF, CSV, JSON, XML, Markdown, YAML
**Actions**: extract, convert, analyze, parse, generate, validate
**Tools**: specific command names (pdftotext, jq, etc.)
**Domains**: database, API, documentation, testing

✅ **Good**:
```yaml
description: "Analyzes SQL queries for PostgreSQL and MySQL databases using EXPLAIN plans. Suggests index optimizations and query rewrites. Use when user asks about slow queries, database performance, SQL optimization, or analyzing query execution plans."
```

**Keywords included**: SQL, PostgreSQL, MySQL, EXPLAIN, index, optimization, performance, query

### Test Activation

Test with natural language:

```
User: "I have a PDF that needs text extraction"
Expected: PDF extraction skill activates

User: "Can you analyze this database query?"
Expected: SQL analysis skill activates

User: "Help me document my API"
Expected: API documentation skill activates
```

If skill doesn't activate, add more keywords to description.

## Tool Permission Best Practices

### Principle of Least Privilege

Grant only the permissions actually needed.

✅ **Good**:
```yaml
# PDF skill needs
allowed-tools: "Read(*.pdf, **/*.pdf), Bash(pdftotext:*), Write(output/*.txt)"
```

❌ **Bad**:
```yaml
# Overly permissive
allowed-tools: "Read(*), Bash(*), Write(*)"
```

### Be Specific with Patterns

✅ **Good**:
```yaml
# Specific git commands
allowed-tools: "Bash(git:status, git:log, git:diff)"

# Specific directories
allowed-tools: "Write(docs/**, output/**)"

# Specific file types
allowed-tools: "Read(*.json, *.yaml)"
```

❌ **Bad**:
```yaml
# Too broad
allowed-tools: "Bash(git:*)"  # All git commands
allowed-tools: "Write(*)"      # All files
```

### Document Why Permissions Needed

```markdown
## Tool Permissions

This skill requires:
- `Read(*.pdf)` - To access PDF files for extraction
- `Bash(pdftotext:*)` - To run PDF extraction tool
- `Write(output/*.txt)` - To save extracted text

These permissions are necessary for the skill's core functionality.
```

## Hook Best Practices

### Keep Hooks Fast

✅ **Good**:
```json
{
  "event": "PostToolUse",
  "action": {
    "command": "prettier --write \"$FILE_PATH\" 2>/dev/null || true"
  },
  "timeout": 5
}
```

❌ **Bad**:
```json
{
  "event": "PostToolUse",
  "action": {
    "command": "npm run full-test-suite"  // Takes 5 minutes
  },
  "timeout": 300
}
```

### Handle Errors Gracefully

✅ **Good**:
```bash
# Non-critical: continue on error
prettier --write "$FILE_PATH" 2>/dev/null || true

# Critical: block on error with clear message
npm test || (echo "❌ Tests failed! Fix before committing." && exit 2)
```

❌ **Bad**:
```bash
# Unhandled errors block unexpectedly
prettier --write "$FILE_PATH"
```

### Use Appropriate Matchers

✅ **Good**:
```json
{
  "event": "PostToolUse",
  "matcher": {
    "toolName": "Edit|Write"  // Only format after edits/writes
  }
}
```

❌ **Bad**:
```json
{
  "event": "PostToolUse",
  "matcher": {
    "toolName": "*"  // Runs on every tool use
  }
}
```

## MCP Tool Best Practices

### Write Detailed Descriptions

✅ **Good**:
```typescript
description: "Fetches current weather conditions for a specific geographic location using the OpenWeatherMap API. Takes a city name and optional country code as input. Returns temperature in Fahrenheit, weather conditions, humidity percentage, and wind speed in mph. Use this when the user asks about current weather, temperature, or atmospheric conditions for a specific location."
```

**Includes**:
- What it does
- Data source (OpenWeatherMap)
- Inputs (city, country)
- Outputs (temperature, conditions, etc.)
- When to use

❌ **Bad**:
```typescript
description: "Gets weather"
```

### Complete Input Schemas

✅ **Good**:
```typescript
input_schema: z.object({
  city: z.string()
    .min(1)
    .max(100)
    .describe("City name (e.g., 'London', 'New York')"),
  country: z.string()
    .length(2)
    .optional()
    .describe("ISO 3166 country code (e.g., 'US', 'GB')")
})
```

❌ **Bad**:
```typescript
input_schema: z.object({
  city: z.string(),
  country: z.string().optional()
})
```

### Return Consistent Structure

✅ **Good**:
```typescript
// Success
return {
  success: true,
  data: { /* results */ }
};

// Error
return {
  success: false,
  error: "User-friendly message",
  details: { code: "ERROR_CODE" }
};
```

❌ **Bad**:
```typescript
// Inconsistent returns
return result;                    // Sometimes
return { data: result };          // Other times
throw new Error("Failed");        // Sometimes
```

## Version Control Best Practices

### Commit Messages

✅ **Good**:
```bash
git commit -m "feat: add PDF extraction skill"
git commit -m "fix: resolve skill activation issue"
git commit -m "docs: update README with examples"
```

**Format**: `<type>: <description>`
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation
- **refactor**: Code refactoring
- **test**: Test updates
- **chore**: Maintenance

❌ **Bad**:
```bash
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "WIP"
```

### Branch Strategy

✅ **Good**:
```bash
main          # Stable releases
develop       # Integration branch
feature/x     # New features
fix/y         # Bug fixes
```

❌ **Bad**:
```bash
# All work on main with no branches
```

## Testing Best Practices

### Test All Components

- [ ] Commands execute correctly
- [ ] Skills activate as expected
- [ ] MCP tools work properly
- [ ] Hooks fire appropriately
- [ ] Error handling works
- [ ] Edge cases handled

### Automated Testing

```bash
#!/bin/bash
# Run before committing

# Validate JSON
jq empty .claude-plugin/plugin.json

# Check syntax
node -c mcp/*.js
python -m py_compile mcp/*.py

# Run tests if present
npm test || pytest
```

### Document Test Scenarios

```markdown
## Test Scenarios

1. **Basic Usage**: Run /command with typical arguments
2. **Edge Cases**: Empty input, special characters, very long input
3. **Error Conditions**: Invalid input, missing files, network errors
4. **Integration**: Works with other plugins/tools
```

## Maintenance Best Practices

### Respond to Issues

- Acknowledge issues quickly
- Reproduce problems
- Provide fixes or workarounds
- Document solutions

### Keep Dependencies Updated

```bash
# Check for updates
npm outdated
pip list --outdated

# Update dependencies
npm update
pip install --upgrade package
```

### Monitor Security

- Subscribe to security advisories
- Update vulnerable dependencies
- Review permissions regularly
- Audit code for issues

### Document Changes

Update CHANGELOG.md:

```markdown
# Changelog

## [1.2.0] - 2025-11-21

### Added
- New /deploy command for staging
- PDF extraction skill

### Fixed
- Skill activation issue
- MCP server timeout

### Changed
- Updated dependencies
```

## Next Steps

- **Development workflow**: See [Development Workflow](development-workflow.md)
- **Publishing**: See [Publishing & Distribution](publishing.md)
- **Examples**: See [Complete Plugin Examples](../examples/complete-plugins.md)
