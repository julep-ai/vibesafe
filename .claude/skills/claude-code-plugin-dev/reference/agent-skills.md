# Agent Skills (2025 Schema)

Complete guide to creating Agent Skills that Claude automatically activates based on context.

## Overview

Agent Skills are **model-invoked capabilities** that Claude autonomously decides to use based on the task context. Unlike slash commands, users don't explicitly invoke them.

**Best for**:
- Context-aware capabilities
- File type processing (PDF, CSV, etc.)
- Domain expertise (SQL, APIs, etc.)
- Automatic tool selection

## Skill File Structure

**Location**: `skills/skill-name/SKILL.md`

**Required filename**: `SKILL.md` (exact case, must be this name)

```markdown
---
name: skill-name
description: "[What it does] + [When to use] + [Specific keywords]. (max 1024 chars)"
version: "1.0.0"
tags: ["keyword1", "keyword2"]
allowed-tools: "Read(*), Bash(tool:*)"
model: "claude-sonnet-4-5-20250929"
---

# Skill Title

Detailed explanation of what this skill does.

## When to Use

Claude activates this when the user asks about [specific triggers].

## Available Tools

List the tools this skill uses and why.

## Examples

Working examples demonstrating the skill.
```

## 2025 Schema Fields

### name (required)
```yaml
name: pdf-text-extraction
```
- **Format**: Lowercase letters, hyphens only
- **Max length**: 64 characters
- **Purpose**: Skill identifier
- **Invalid**: Underscores, spaces, uppercase

### description (required - MOST IMPORTANT!)
```yaml
description: "Extracts text from PDF files using pdftotext and pdf2txt.py, handling multi-page documents and complex layouts. Use when the user asks to extract, read, or analyze text from PDF files, convert PDFs to text, or process PDF documents."
```

**This is the MOST CRITICAL field**. Claude uses it to decide when to activate your skill.

**Formula**: `[What] + [How] + [When with keywords]`

**Must include**:
1. **What it does** (specific action)
2. **Tools/methods used** (how it works)
3. **When to use** with **explicit keywords**
4. **File types** if applicable
5. **Actions** (extract, convert, analyze, etc.)
6. **Domains** (database, API, documentation, etc.)

**Good example**:
```yaml
description: "Analyzes SQL database queries for performance issues using EXPLAIN and query plans. Suggests index optimizations, query rewrites, and caching strategies. Use when user asks about slow queries, database optimization, SQL performance, query tuning, or analyzing PostgreSQL/MySQL performance."
```

**Bad example**:
```yaml
description: "Helps with database stuff"  # ❌ Too vague, no keywords
```

### version (required)
```yaml
version: "1.0.0"
```
- **Format**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Purpose**: Track skill changes
- **Update**: When changing functionality

### tags (optional but recommended)
```yaml
tags: ["pdf", "extraction", "documents", "text-processing"]
```
- **Purpose**: Discovery, categorization
- **Format**: Array of strings
- **Include**: File types, actions, domains

### allowed-tools (NEW in 2025)
```yaml
allowed-tools: "Read(*), Bash(pdftotext:*, pdf2txt:*)"
```
- **Purpose**: Restrict tool access for security
- **Format**: Comma-separated tool patterns
- **Patterns**:
  - `Read(*)` - All file reads
  - `Read(*.pdf)` - Only PDF files
  - `Bash(command:*)` - Specific command family
  - `Write(output/**)` - Specific directory

### model (optional)
```yaml
model: "claude-sonnet-4-5-20250929"
```
- **Purpose**: Override default model
- **Use when**: Skill needs specific capabilities

### icon (optional)
```yaml
icon: "icons/pdf-icon.png"
```
- **Purpose**: Visual identifier
- **Format**: Relative path to image

### category (optional)
```yaml
category: "document-processing"
```
- **Purpose**: Group related skills
- **Examples**: "development", "data-analysis", "devops"

## Critical: Skill Activation

### Why Skills Fail to Activate

**Problem**: You create a skill but Claude never uses it.

**Common causes**:

1. **Generic description**
```yaml
# ❌ BAD
description: "Helps with documents"
description: "Useful for file processing"
description: "Handles various tasks"
```

2. **Missing keywords**
```yaml
# ❌ BAD
description: "Extracts content from files"
# Missing: what file type? PDF? Word? Text?
```

3. **No activation triggers**
```yaml
# ❌ BAD
description: "PDF text extraction tool"
# Missing: "Use when user asks to..."
```

4. **Wrong file location**
```
skills/my-skill.md          # ❌ Wrong
skills/my-skill/skill.md    # ❌ Wrong case
skills/my-skill/SKILL.md    # ✅ Correct!
```

### How to Write Descriptions That Work

**Template**:
```
"[Action] [Object] using [Tools], [details about capabilities].
Use when user asks [trigger phrases with keywords]."
```

**Example 1: PDF Extraction**
```yaml
description: "Extracts and converts text from PDF documents using pdftotext and OCR, handling scanned images, multi-page files, and complex layouts. Use when user asks to extract text from PDF, read PDF contents, convert PDF to text, or analyze PDF documents."
```

**Keywords included**: PDF, extract, convert, text, OCR, scanned, read, analyze

**Example 2: SQL Analysis**
```yaml
description: "Analyzes SQL database queries, interprets results, and suggests optimizations using EXPLAIN plans and index analysis. Supports PostgreSQL, MySQL, and SQLite. Use when user asks about database queries, slow SQL performance, query optimization, analyzing data patterns, or executing SELECT statements."
```

**Keywords included**: SQL, database, queries, PostgreSQL, MySQL, SQLite, performance, optimization, SELECT, analyze

**Example 3: API Documentation**
```yaml
description: "Generates API documentation from OpenAPI/Swagger specifications, creating markdown with endpoints, parameters, examples, and authentication details. Use when user needs to document REST APIs, create API references, parse OpenAPI specs, or generate endpoint documentation."
```

**Keywords included**: API, OpenAPI, Swagger, REST, documentation, endpoints, parameters, authentication

### Activation Testing

**Test your skill**:
```
User: "I have a PDF file that needs text extraction"
Expected: Claude activates PDF extraction skill

User: "Can you analyze this SQL query performance?"
Expected: Claude activates SQL analysis skill

User: "Help me document my REST API"
Expected: Claude activates API documentation skill
```

**If skill doesn't activate**:
1. Add more specific keywords to description
2. Include file types explicitly
3. Add "Use when user asks to [action]"
4. Test with different phrasings

## Complete Skill Examples

### Example 1: PDF Text Extraction

**File**: `skills/pdf-extraction/SKILL.md`

```markdown
---
name: pdf-extraction
description: "Extracts and converts text content from PDF files using pdftotext and pdf2txt.py, handling multi-page documents, scanned images with OCR, and complex layouts. Use when user asks to extract text from PDF, read PDF contents, convert PDF to text, parse PDF documents, or analyze PDF files."
version: "1.0.0"
tags: ["pdf", "extraction", "ocr", "documents", "text-processing"]
allowed-tools: "Read(*.pdf, **/*.pdf), Bash(pdftotext:*, pdf2txt:*)"
---

# PDF Text Extraction Skill

Extracts text content from PDF files using multiple methods for maximum compatibility.

## When to Use

Claude automatically activates this skill when you:
- Mention extracting text from PDFs
- Ask to read or analyze PDF contents
- Need to convert PDFs to text format
- Want to parse PDF documents

## Available Tools

- **pdftotext**: Fast extraction for standard PDFs
- **pdf2txt.py**: Advanced extraction for complex layouts
- **Read tool**: Access PDF files from the filesystem

## How It Works

1. Detect PDF file location
2. Try `pdftotext` for fast extraction
3. Fall back to `pdf2txt.py` for complex documents
4. Return formatted text with structure preserved

## Examples

### Basic Extraction
```
User: Extract text from report.pdf
Claude: I'll use my PDF extraction skill...
```

### Multi-page Analysis
```
User: Analyze the content in these 50 PDF files
Claude: Using PDF extraction to process all files...
```

## Limitations

- Scanned images require OCR (may be slow)
- Heavily formatted PDFs may lose layout
- Encrypted PDFs need password
</markdown>
```

### Example 2: SQL Query Analysis

**File**: `skills/sql-analysis/SKILL.md`

```markdown
---
name: sql-analysis
description: "Analyzes SQL database queries and performance using EXPLAIN plans, suggests index optimizations and query rewrites. Executes safe SELECT queries and interprets results. Supports PostgreSQL, MySQL, and SQLite. Use when user asks about database queries, slow SQL performance, query optimization, analyzing data patterns, or executing SELECT statements."
version: "1.0.0"
tags: ["sql", "database", "postgresql", "mysql", "optimization", "queries", "performance"]
allowed-tools: "Read(*.sql, **/*.sql), Bash(psql:*, mysql:*, sqlite3:*)"
---

# SQL Query Analysis Skill

Analyzes database queries, optimizes performance, and interprets results.

## When to Use

Claude activates this skill when you ask about:
- SQL queries or database analysis
- Performance optimization for slow queries
- Query result interpretation
- Data pattern analysis
- Database schema inspection

## Supported Databases

- PostgreSQL (via `psql`)
- MySQL (via `mysql`)
- SQLite (via `sqlite3`)

## Capabilities

### Query Execution
- Safe SELECT query execution
- Result formatting and interpretation
- Multi-row analysis

### Performance Analysis
- EXPLAIN plan interpretation
- Index suggestions
- Query optimization recommendations
- Bottleneck identification

### Schema Analysis
- Table structure inspection
- Relationship mapping
- Column type analysis

## Examples

### Execute and Analyze
```
User: Run this query and tell me the top customers
Claude: I'll execute the query using my SQL analysis skill...
```

### Performance Optimization
```
User: This query is really slow, can you optimize it?
Claude: Let me analyze the query performance...
```

## Safety Features

- Only executes READ operations (SELECT)
- Blocks INSERT, UPDATE, DELETE, DROP
- Validates queries before execution
- Limits result sizes for safety
</markdown>
```

### Example 3: API Documentation Generator

**File**: `skills/api-docs/SKILL.md`

```markdown
---
name: api-documentation
description: "Generates comprehensive API documentation from OpenAPI/Swagger specifications, source code, or existing endpoints. Creates markdown documentation with endpoint details, parameters, request/response examples, authentication, and error codes. Use when user needs to document REST APIs, create API references, parse OpenAPI specs, generate endpoint documentation, or document GraphQL APIs."
version: "1.0.0"
tags: ["api", "documentation", "openapi", "swagger", "rest", "graphql", "endpoints"]
allowed-tools: "Read(*.yaml, *.yml, *.json, **/*.md), Write(docs/**)"
---

# API Documentation Generation Skill

Generates comprehensive, user-friendly API documentation.

## When to Use

Claude activates when you need to:
- Document REST or GraphQL APIs
- Parse OpenAPI/Swagger specs
- Create endpoint documentation
- Generate API references
- Document authentication flows

## Input Formats

- **OpenAPI/Swagger**: YAML or JSON specs
- **Source Code**: Parse from code comments
- **Existing Endpoints**: Live API inspection
- **Manual Descriptions**: User-provided details

## Output Format

Generated documentation includes:

1. **Overview**: API purpose and architecture
2. **Authentication**: Methods and examples
3. **Endpoints**: Complete endpoint list
4. **Parameters**: Request params with types
5. **Responses**: Success and error examples
6. **Code Examples**: Multiple languages
7. **Error Codes**: Detailed error reference

## Examples

### From OpenAPI Spec
```
User: Generate docs from api-spec.yaml
Claude: I'll parse the OpenAPI spec and create comprehensive documentation...
```

### From Source Code
```
User: Document the API endpoints in src/api/
Claude: Analyzing source code to extract API documentation...
```

## Features

- Automatic example generation
- Request/response formatting
- Authentication flow diagrams
- Error code reference tables
- Multi-language code samples
</markdown>
```

## Tool Permissions Best Practices

### Read Permissions
```yaml
# Specific file types
allowed-tools: "Read(*.pdf, *.txt)"

# Specific directories
allowed-tools: "Read(data/**, config/**)"

# All files (use cautiously)
allowed-tools: "Read(*)"
```

### Bash Permissions
```yaml
# Specific command families
allowed-tools: "Bash(git:*, npm:*)"

# Specific commands
allowed-tools: "Bash(pdftotext:*, ps:aux)"

# All bash (dangerous!)
allowed-tools: "Bash(*)"
```

### Write Permissions
```yaml
# Specific directories (safest)
allowed-tools: "Write(output/**, temp/**)"

# Specific file types
allowed-tools: "Write(*.md, *.txt)"

# All writes (use carefully)
allowed-tools: "Write(*)"
```

### Multiple Tools
```yaml
allowed-tools: "Read(*.pdf), Bash(pdftotext:*), Write(output/*.txt)"
```

## Troubleshooting

### Skill Not Activating

1. **Make description more specific**:
```yaml
# Before (doesn't activate):
description: "Helps with files"

# After (activates):
description: "Extracts text from PDF files using pdftotext. Use when user asks to extract, read, or analyze PDF contents."
```

2. **Add explicit keywords**:
- File types: PDF, CSV, JSON, XML
- Actions: extract, convert, analyze, parse
- Tools: specific command names

3. **Verify file structure**:
```
✅ skills/pdf-extraction/SKILL.md
❌ skills/pdf-extraction/skill.md (wrong case)
❌ skills/pdf-extraction.md (wrong structure)
```

4. **Check YAML syntax**:
```bash
# Validate YAML frontmatter
head -n 20 skills/my-skill/SKILL.md
```

### Skill Activates But Fails

1. **Check allowed-tools**:
```yaml
# Ensure skill has permission for tools it needs
allowed-tools: "Bash(pdftotext:*)"
```

2. **Verify tools exist**:
```bash
which pdftotext
which pdf2txt.py
```

3. **Test tool independently**:
```bash
pdftotext sample.pdf -
```

## Best Practices

### Description Writing

✅ **DO**:
- Be extremely specific
- Include file types explicitly
- List actions (extract, convert, analyze)
- Add "Use when user asks to [action]"
- Include tool names
- Mention supported formats

❌ **DON'T**:
- Use generic language
- Omit keywords
- Forget activation triggers
- Be vague about capabilities

### Tool Permissions

✅ **DO**:
- Use most restrictive permissions
- Specify exact patterns
- Document why permissions needed
- Test with minimal permissions first

❌ **DON'T**:
- Grant blanket access (`Bash(*)`)
- Allow unnecessary write access
- Forget to document permissions
- Over-permission "just in case"

### Versioning

✅ **DO**:
- Update version on changes
- Document version changes
- Follow semantic versioning

❌ **DON'T**:
- Forget to bump version
- Make breaking changes in patches
- Skip version documentation

## Next Steps

- **Add commands**: See [Slash Commands](slash-commands.md)
- **Create MCP tools**: See [MCP Servers](mcp-servers.md)
- **Test skill activation**: See [Development Workflow](../guides/development-workflow.md)
- **See examples**: See [Complete Plugin Examples](../examples/complete-plugins.md)
