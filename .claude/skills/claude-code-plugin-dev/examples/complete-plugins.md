# Complete Plugin Examples

Full working examples of Claude Code plugins for common use cases.

## Example 1: Git Workflow Plugin

Simple plugin with commands and hooks for Git operations.

### Structure

```
git-workflow-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── commit-flow.md
│   └── pr-create.md
├── hooks/
│   └── pre-commit.json
└── README.md
```

### plugin.json

```json
{
  "name": "git-workflow",
  "version": "1.0.0",
  "author": "Dev Team",
  "description": "Git workflow automation with commit helpers and PR creation. Includes pre-commit formatting and linting hooks.",
  "repository": "https://github.com/yourorg/git-workflow",
  "license": "MIT",

  "commands": {
    "path": "commands"
  },

  "hooks": {
    "path": "hooks"
  }
}
```

### commands/commit-flow.md

```markdown
---
description: "Automated commit workflow: stage, test, format, commit"
allowed-tools: Bash(git:*, npm:test, prettier:*)
argument-hint: "commit message"
---

# Automated Commit Workflow

Running pre-commit workflow for: "$1"

## 1. Stage All Changes

!git add -A

## 2. Run Tests

!npm test || (echo "❌ Tests failed! Please fix before committing." && exit 1)

## 3. Format Code

!prettier --write .
!git add -A

## 4. Create Commit

!git commit -m "$1"

✅ Successfully committed with message: "$1"
```

### commands/pr-create.md

```markdown
---
description: "Create pull request with automated title and description"
allowed-tools: Bash(git:*, gh:*)
argument-hint: "target branch (default: main)"
---

# Create Pull Request

Target branch: ${1:-main}

## 1. Get Current Branch

!CURRENT_BRANCH=$(git branch --show-current)

## 2. Push Current Branch

!git push -u origin $CURRENT_BRANCH

## 3. Generate PR Description

Based on recent commits:

!git log origin/${1:-main}..HEAD --pretty=format:"- %s"

## 4. Create PR

!gh pr create --base ${1:-main} --head $CURRENT_BRANCH --fill

✅ Pull request created!
```

### hooks/pre-commit.json

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
        "command": "if [[ $FILE_PATH == *.js || $FILE_PATH == *.ts ]]; then prettier --write \"$FILE_PATH\" 2>/dev/null && eslint --fix \"$FILE_PATH\" 2>/dev/null; fi"
      },
      "timeout": 10,
      "enabled": true
    },
    {
      "event": "PreToolUse",
      "matcher": {
        "toolName": "Bash:git:commit"
      },
      "action": {
        "type": "command",
        "command": "npm test --silent || (echo '❌ Tests must pass before committing' && exit 2)"
      },
      "timeout": 60,
      "enabled": true
    }
  ]
}
```

---

## Example 2: PDF Processing Plugin

Plugin with skills and MCP server for PDF processing.

### Structure

```
pdf-tools-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── pdf-extraction/
│       └── SKILL.md
├── mcp/
│   └── pdf-server.ts
└── README.md
```

### plugin.json

```json
{
  "name": "pdf-tools",
  "version": "1.0.0",
  "author": "Document Team",
  "description": "PDF text extraction and processing tools with OCR support",
  "repository": "https://github.com/yourorg/pdf-tools",
  "license": "MIT",

  "skills": {
    "path": "skills"
  },

  "mcp": {
    "servers": {
      "pdf-tools": {
        "type": "stdio",
        "command": "node mcp/pdf-server.js"
      }
    }
  }
}
```

### skills/pdf-extraction/SKILL.md

```markdown
---
name: pdf-extraction
description: "Extracts text content from PDF files using pdftotext and OCR technology, handling multi-page documents, scanned images, and complex layouts. Use when user asks to extract text from PDF, read PDF contents, convert PDF to text, parse PDF documents, or analyze PDF files. Supports both digital and scanned PDFs."
version: "1.0.0"
tags: ["pdf", "extraction", "ocr", "documents", "text-processing"]
allowed-tools: "Read(*.pdf, **/*.pdf), Bash(pdftotext:*), mcp__pdf-tools__*"
---

# PDF Text Extraction Skill

Automatically extracts text from PDF files using multiple methods for maximum compatibility.

## When to Use

Claude activates this skill when you:
- Ask to extract text from a PDF file
- Need to read or analyze PDF contents
- Want to convert PDFs to text format
- Need to process PDF documents
- Mention PDF file analysis

## Methods Used

1. **pdftotext**: Fast extraction for digital PDFs
2. **OCR**: Optical character recognition for scanned documents
3. **pdf-tools MCP**: Advanced PDF parsing

## Supported Features

- Multi-page PDF extraction
- Scanned document OCR
- Layout preservation
- Table extraction
- Metadata parsing

## Examples

### Basic Extraction
```
User: Extract text from report.pdf
Claude: I'll use my PDF extraction skill to get the text...
```

### Batch Processing
```
User: Extract text from all PDFs in the reports folder
Claude: Processing multiple PDFs using extraction skill...
```

## Limitations

- Encrypted PDFs require password
- OCR accuracy depends on scan quality
- Very large PDFs (>100MB) may be slow
- Complex layouts may lose formatting
```

### mcp/pdf-server.ts

```typescript
import { createSdkMcpServer, tool } from "@anthropic-ai/sdk/mcp";
import { z } from "zod";
import { exec } from "child_process";
import { promisify } from "util";
import * as fs from "fs/promises";

const execAsync = promisify(exec);

const server = createSdkMcpServer({
  name: "pdf-tools",
  version: "1.0.0",
  tools: [
    tool({
      name: "extract_pdf_text",
      description: "Extracts text content from a PDF file using pdftotext. Takes a file path as input and returns the extracted text content. Handles multi-page documents and preserves basic layout. Use this when you need to extract readable text from PDF files for analysis or processing.",
      input_schema: z.object({
        file_path: z.string().describe("Absolute path to the PDF file"),
        layout: z.boolean().default(true).describe("Preserve layout formatting")
      })
    }, async ({ file_path, layout }) => {
      try {
        // Verify file exists
        await fs.access(file_path);

        // Extract text using pdftotext
        const layoutFlag = layout ? "-layout" : "";
        const { stdout, stderr } = await execAsync(
          `pdftotext ${layoutFlag} "${file_path}" -`
        );

        if (stderr) {
          return {
            success: false,
            error: `pdftotext error: ${stderr}`
          };
        }

        return {
          success: true,
          text: stdout,
          pages: stdout.split('\f').length
        };
      } catch (error) {
        return {
          success: false,
          error: `Failed to extract PDF: ${error.message}`
        };
      }
    }),

    tool({
      name: "pdf_metadata",
      description: "Extracts metadata from a PDF file including title, author, creation date, page count, and file size. Takes a file path as input. Use when you need information about a PDF file without reading its full contents.",
      input_schema: z.object({
        file_path: z.string().describe("Absolute path to the PDF file")
      })
    }, async ({ file_path }) => {
      try {
        await fs.access(file_path);

        const { stdout } = await execAsync(`pdfinfo "${file_path}"`);

        // Parse pdfinfo output
        const lines = stdout.split('\n');
        const metadata: any = {};

        for (const line of lines) {
          const [key, ...valueParts] = line.split(':');
          if (key && valueParts.length > 0) {
            metadata[key.trim()] = valueParts.join(':').trim();
          }
        }

        return {
          success: true,
          metadata
        };
      } catch (error) {
        return {
          success: false,
          error: `Failed to get metadata: ${error.message}`
        };
      }
    })
  ]
});

export default server;
```

---

## Example 3: Database Tools Plugin

Complete plugin with commands, skills, and MCP server for database operations.

### Structure

```
database-tools-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── db-query.md
│   └── db-schema.md
├── skills/
│   └── sql-analysis/
│       └── SKILL.md
├── mcp/
│   └── db-server.py
└── README.md
```

### plugin.json

```json
{
  "name": "database-tools",
  "version": "1.0.0",
  "author": "Data Team",
  "description": "Database query, analysis, and schema inspection tools for PostgreSQL, MySQL, and SQLite",
  "repository": "https://github.com/yourorg/database-tools",
  "license": "MIT",

  "commands": {
    "path": "commands"
  },

  "skills": {
    "path": "skills"
  },

  "mcp": {
    "servers": {
      "db-tools": {
        "type": "stdio",
        "command": "python mcp/db-server.py"
      }
    }
  }
}
```

### commands/db-query.md

```markdown
---
description: "Execute safe database query and analyze results"
allowed-tools: "mcp__db-tools__execute_query"
argument-hint: "SQL SELECT query"
---

# Database Query Execution

Query: $ARGUMENTS

## Safety Check

Validating that query is read-only (SELECT only)...

## Execute Query

Using database tools to execute the query and retrieve results.

## Results Analysis

Analyzing the query results:
1. Row count and summary statistics
2. Notable patterns or outliers
3. Data quality observations
4. Recommendations for further analysis
```

### commands/db-schema.md

```markdown
---
description: "Display database schema and table information"
allowed-tools: "mcp__db-tools__list_tables, mcp__db-tools__table_schema"
---

# Database Schema

Retrieving database schema information...

## Tables

List all tables with row counts and descriptions.

## Relationships

Identify foreign key relationships between tables.

## Indexes

Show indexes on each table for performance analysis.
```

### skills/sql-analysis/SKILL.md

```markdown
---
name: sql-analysis
description: "Analyzes SQL database queries and performance using EXPLAIN plans, suggests index optimizations and query rewrites. Executes safe SELECT queries and interprets results for PostgreSQL, MySQL, and SQLite databases. Use when user asks about database queries, slow SQL performance, query optimization, analyzing data patterns, executing SELECT statements, or database analysis."
version: "1.0.0"
tags: ["sql", "database", "postgresql", "mysql", "sqlite", "optimization", "queries", "performance", "analysis"]
allowed-tools: "Read(*.sql, **/*.sql), mcp__db-tools__*"
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
- SELECT statement execution

## Supported Databases

- PostgreSQL (via psql)
- MySQL (via mysql)
- SQLite (via sqlite3)

## Capabilities

### Query Execution
- Safe SELECT query execution (read-only)
- Result formatting and interpretation
- Multi-row analysis and aggregation

### Performance Analysis
- EXPLAIN plan interpretation
- Index usage analysis
- Query optimization recommendations
- Bottleneck identification

### Schema Analysis
- Table structure inspection
- Relationship mapping between tables
- Column type and constraint analysis
- Index coverage review

## Examples

### Execute and Interpret Query
```
User: Run this query and show me the top 10 customers by revenue
Claude: I'll execute the SQL query and analyze the results...
```

### Performance Optimization
```
User: This query is taking 30 seconds, can you optimize it?
Claude: Let me analyze the query performance using EXPLAIN...
```

### Schema Exploration
```
User: What tables do we have and how are they related?
Claude: I'll inspect the database schema...
```

## Safety Features

- Only executes READ operations (SELECT)
- Automatically blocks INSERT, UPDATE, DELETE, DROP
- Validates queries before execution
- Limits result sizes for safety (max 1000 rows)
- Prevents SQL injection
```

### mcp/db-server.py

```python
from anthropic.mcp import createSdkMcpServer, tool
from typing import Optional, Dict, Any, List
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'database.db')

server = createSdkMcpServer(
    name="db-tools",
    version="1.0.0",
    tools=[
        tool(
            name="execute_query",
            description=(
                "Executes a read-only SQL SELECT query against the database. "
                "Takes a SQL query string and optional row limit. Returns query "
                "results as JSON with column names and values. Use when the user "
                "needs to fetch data, analyze database contents, inspect tables, "
                "or run SELECT queries. Only SELECT statements are allowed for safety."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum rows to return (default 100, max 1000)",
                        "default": 100,
                        "maximum": 1000
                    }
                },
                "required": ["query"]
            }
        )
        async def execute_query(query: str, limit: int = 100) -> Dict[str, Any]:
            # TODO(prototype): swap heuristic checks for a SQL parser to enforce single SELECT safely.
            # Validate read-only
            query_lower = query.strip().lower()
            if not query_lower.startswith('select'):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed for safety"
                }

            # Check for dangerous operations
            dangerous = ['insert', 'update', 'delete', 'drop', 'alter', 'create']
            if any(word in query_lower for word in dangerous):
                return {
                    "success": False,
                    "error": "Query contains forbidden operations"
                }

            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Add LIMIT if not present
                if 'limit' not in query_lower:
                    query += f" LIMIT {min(limit, 1000)}"

                cursor.execute(query)
                rows = cursor.fetchall()

                results = [dict(row) for row in rows]
                conn.close()

                return {
                    "success": True,
                    "row_count": len(results),
                    "data": results
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Query execution failed: {str(e)}"
                }
        ,

        tool(
            name="list_tables",
            description=(
                "Lists all tables in the database with their row counts and column "
                "details. Returns table names, number of rows, and column information "
                "including types and constraints. Use when user asks about database "
                "schema, available tables, table structure, or database overview."
            ),
            input_schema={
                "type": "object",
                "properties": {}
            }
        )
        async def list_tables() -> Dict[str, Any]:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                tables = cursor.fetchall()

                table_info = []
                for (table_name,) in tables:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]

                    # Get column info
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()

                    table_info.append({
                        "name": table_name,
                        "rows": count,
                        "columns": [
                            {
                                "name": col[1],
                                "type": col[2],
                                "not_null": bool(col[3]),
                                "default": col[4],
                                "primary_key": bool(col[5])
                            }
                            for col in columns
                        ]
                    })

                conn.close()

                return {
                    "success": True,
                    "table_count": len(table_info),
                    "tables": table_info
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to list tables: {str(e)}"
                }
    ]
)
```

---

## Example 4: Development Tools Plugin

Plugin with multiple features for development workflows.

### Structure

```
dev-tools-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── test.md
│   ├── lint.md
│   └── deploy/
│       ├── staging.md
│       └── production.md
├── hooks/
│   ├── formatting.json
│   └── testing.json
└── README.md
```

### plugin.json

```json
{
  "name": "dev-tools",
  "version": "1.0.0",
  "description": "Complete development toolkit with testing, linting, deployment, and automation",
  "license": "MIT",

  "commands": {
    "path": "commands"
  },

  "hooks": {
    "path": "hooks"
  }
}
```

### commands/test.md

```markdown
---
description: "Run test suite with coverage reporting"
allowed-tools: Bash(npm:*, pytest:*)
argument-hint: "test pattern or file"
---

# Test Suite

Running tests for: ${ARGUMENTS:-all tests}

## JavaScript/TypeScript Tests

!npm test ${ARGUMENTS:-}

## Python Tests

!pytest ${ARGUMENTS:-.} -v --cov

## Summary

Review test results and coverage reports above.
```

### hooks/formatting.json

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
        "command": "case \"$FILE_PATH\" in *.ts|*.tsx|*.js|*.jsx) prettier --write \"$FILE_PATH\" 2>/dev/null && eslint --fix \"$FILE_PATH\" 2>/dev/null;; *.py) black \"$FILE_PATH\" 2>/dev/null && ruff check --fix \"$FILE_PATH\" 2>/dev/null;; esac"
      },
      "timeout": 15,
      "enabled": true
    }
  ]
}
```

---

These complete examples demonstrate:
- Proper plugin structure
- Real-world use cases
- Integration of multiple component types
- Best practices implementation
- Production-ready code

Use these as templates for your own plugins!
