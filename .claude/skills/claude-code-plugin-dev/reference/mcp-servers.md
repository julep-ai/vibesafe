# MCP Servers (Custom Tools)

Complete guide to implementing custom tools via Model Context Protocol (MCP) servers.

## Overview

MCP servers expose custom tools that Claude can invoke. They provide external integrations, API access, database connections, and custom operations.

**Best for**:
- API integrations
- Database operations
- File system operations
- External service connections
- Custom calculations or processing

## MCP Server Types

### 1. stdio (Standard Input/Output)
- **Communication**: stdin/stdout
- **Best for**: Local tools, CLI wrappers
- **Languages**: Node.js, Python, any language

### 2. HTTP
- **Communication**: HTTP REST API
- **Best for**: Remote services, web APIs
- **Deployment**: Separate server process

### 3. SSE (Server-Sent Events)
- **Communication**: HTTP with event stream
- **Best for**: Real-time updates, streaming
- **Use case**: Long-running operations

## TypeScript Implementation

### Basic Structure

```typescript
import { createSdkMcpServer, tool } from "@anthropic-ai/sdk/mcp";
import { z } from "zod";

const server = createSdkMcpServer({
  name: "my-tools",
  version: "1.0.0",
  tools: [
    tool({
      name: "tool_name",
      description: "Detailed description (3-4 sentences minimum)",
      input_schema: z.object({
        param: z.string().describe("Parameter description")
      })
    }, async (input) => {
      // Implementation
      return { result: "data" };
    })
  ]
});

export default server;
```

### Complete Example: Weather API

```typescript
import { createSdkMcpServer, tool } from "@anthropic-ai/sdk/mcp";
import { z } from "zod";
import fetch from "node-fetch";

const server = createSdkMcpServer({
  name: "weather-tools",
  version: "1.0.0",
  tools: [
    tool({
      name: "get_weather",
      description: "Fetches current weather conditions for a specific geographic location using the OpenWeatherMap API. Takes a city name and optional country code as input. Returns temperature in Fahrenheit, weather conditions, humidity percentage, and wind speed in mph. Use this when the user asks about current weather, temperature, or atmospheric conditions for a specific location.",
      input_schema: z.object({
        city: z.string().describe("City name (e.g., 'London', 'New York')"),
        country: z.string().optional().describe("ISO 3166 country code (e.g., 'US', 'GB')")
      })
    }, async ({ city, country }) => {
      try {
        const location = country ? `${city},${country}` : city;
        const apiKey = process.env.OPENWEATHER_API_KEY;

        const response = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?q=${location}&appid=${apiKey}&units=imperial`
        );

        if (!response.ok) {
          return {
            success: false,
            error: `Weather API error: ${response.statusText}`
          };
        }

        const data = await response.json();

        return {
          success: true,
          location: `${data.name}, ${data.sys.country}`,
          temperature: data.main.temp,
          feels_like: data.main.feels_like,
          conditions: data.weather[0].description,
          humidity: data.main.humidity,
          wind_speed: data.wind.speed
        };
      } catch (error) {
        return {
          success: false,
          error: error.message
        };
      }
    }),

    tool({
      name: "get_forecast",
      description: "Retrieves 5-day weather forecast for a location including daily high/low temperatures, conditions, and precipitation probability. Returns forecast data in 3-hour intervals. Use when user asks about upcoming weather, future conditions, or weather predictions for a city.",
      input_schema: z.object({
        city: z.string().describe("City name"),
        country: z.string().optional().describe("ISO country code"),
        days: z.number().min(1).max(5).default(3).describe("Number of days to forecast (1-5)")
      })
    }, async ({ city, country, days }) => {
      // Implementation similar to above
      return { forecast: [] };
    })
  ]
});

export default server;
```

## Python Implementation

### Basic Structure

```python
from anthropic.mcp import createSdkMcpServer, tool
from typing import Optional, Dict, Any

server = createSdkMcpServer(
    name="my-tools",
    version="1.0.0",
    tools=[
        tool(
            name="tool_name",
            description="Detailed description",
            input_schema={
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "Parameter description"}
                },
                "required": ["param"]
            }
        )
        async def tool_name(param: str) -> Dict[str, Any]:
            return {"result": "data"}
    ]
)
```

### Complete Example: Database Tools

```python
from anthropic.mcp import createSdkMcpServer, tool
from typing import Optional, Dict, Any, List
import sqlite3

server = createSdkMcpServer(
    name="database-tools",
    version="1.0.0",
    tools=[
        tool(
            name="execute_query",
            description=(
                "Executes a read-only SQL SELECT query against the SQLite database. "
                "Takes a SQL query string and optional row limit. Returns query results "
                "as JSON with column names and values. Use when the user needs to fetch "
                "data, analyze database contents, inspect tables, or run SELECT queries. "
                "Only SELECT statements are allowed for safety."
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
                        "description": "Maximum rows to return (default 100)",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        )
        async def execute_query(query: str, limit: int = 100) -> Dict[str, Any]:
            # Validate read-only
            if not query.strip().lower().startswith('select'):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed"
                }

            try:
                conn = sqlite3.connect('database.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Add LIMIT if not present
                if 'limit' not in query.lower():
                    query += f" LIMIT {limit}"

                cursor.execute(query)
                rows = cursor.fetchall()

                results = [dict(row) for row in rows]

                conn.close()

                return {
                    "success": True,
                    "rows": len(results),
                    "data": results
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        ,

        tool(
            name="list_tables",
            description=(
                "Lists all tables in the database with their row counts and column details. "
                "Returns table names, number of rows, and column information including types. "
                "Use when user asks about database schema, available tables, or database structure."
            ),
            input_schema={
                "type": "object",
                "properties": {}
            }
        )
        async def list_tables() -> Dict[str, Any]:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                table_info = []
                for (table_name,) in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]

                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()

                    table_info.append({
                        "name": table_name,
                        "rows": count,
                        "columns": [
                            {"name": col[1], "type": col[2]}
                            for col in columns
                        ]
                    })

                conn.close()

                return {
                    "success": True,
                    "tables": table_info
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    ]
)
```

## Tool Naming Convention

Tools are automatically prefixed with: `mcp__<server-name>__<tool-name>`

**Examples**:
- Server: `weather-tools`, Tool: `get_weather`
  → `mcp__weather-tools__get_weather`

- Server: `db-tools`, Tool: `execute_query`
  → `mcp__db-tools__execute_query`

**Naming rules**:
- Lowercase letters, numbers, hyphens, underscores
- Max 64 characters
- Must match regex: `^[a-zA-Z0-9_-]{1,64}$`

## Tool Descriptions (Critical!)

### Description Requirements

**Minimum**: 3-4 complete sentences

**Must include**:
1. What the tool does
2. What inputs it takes
3. What it returns
4. When to use it

### Bad vs Good Descriptions

❌ **Bad** (too short, vague):
```typescript
description: "Gets weather data"
description: "Queries the database"
description: "Retrieves information"
```

✅ **Good** (detailed, specific):
```typescript
description: "Fetches current weather conditions for a specific geographic location using the OpenWeatherMap API. Takes a city name and optional country code as input. Returns temperature in Fahrenheit, weather conditions, humidity percentage, and wind speed in mph. Use this when the user asks about current weather, temperature, or atmospheric conditions for a specific location."
```

### Description Template

```
"[Action] [Object] [using Method/API], [handling Details]. Takes [Input Description] as input. Returns [Output Description] including [specific fields]. Use this when the user [trigger conditions with keywords]."
```

## Input Schema

### JSON Schema (Python)

```python
input_schema={
    "type": "object",
    "properties": {
        "param1": {
            "type": "string",
            "description": "Detailed parameter description"
        },
        "param2": {
            "type": "number",
            "description": "Numeric parameter",
            "minimum": 0,
            "maximum": 100
        },
        "param3": {
            "type": "string",
            "enum": ["option1", "option2"],
            "description": "Enumerated options"
        },
        "optional_param": {
            "type": "boolean",
            "description": "Optional boolean flag",
            "default": False
        }
    },
    "required": ["param1", "param2"]
}
```

### Zod Schema (TypeScript)

```typescript
input_schema: z.object({
  param1: z.string().describe("Detailed parameter description"),
  param2: z.number().min(0).max(100).describe("Numeric parameter"),
  param3: z.enum(["option1", "option2"]).describe("Enumerated options"),
  optionalParam: z.boolean().default(false).describe("Optional flag")
})
```

### Parameter Types

**Supported types**:
- `string` - Text values
- `number` - Numeric values (int or float)
- `boolean` - true/false
- `array` - Lists of values
- `object` - Nested structures
- `enum` - Predefined options

**Constraints**:
- `minimum`, `maximum` - Numeric bounds
- `minLength`, `maxLength` - String length
- `pattern` - Regex validation
- `enum` - Allowed values list
- `default` - Default value if not provided

## Error Handling

### Return Structure

**Success**:
```typescript
return {
  success: true,
  data: { /* results */ }
};
```

**Error**:
```typescript
return {
  success: false,
  error: "User-friendly error message",
  details: {
    code: "ERROR_CODE",
    retryable: true
  }
};
```

### Error Types

**Validation Errors**:
```typescript
if (!input.city) {
  return {
    success: false,
    error: "City parameter is required"
  };
}
```

**API Errors**:
```typescript
if (!response.ok) {
  return {
    success: false,
    error: `API error: ${response.statusText}`,
    details: { statusCode: response.status }
  };
}
```

**Exception Handling**:
```typescript
try {
  // Tool implementation
} catch (error) {
  return {
    success: false,
    error: error.message,
    details: { stack: error.stack }
  };
}
```

## Plugin Configuration

**File**: `.claude-plugin/plugin.json`

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Plugin with MCP tools",

  "mcp": {
    "servers": {
      "my-tools": {
        "type": "stdio",
        "command": "node mcp/server.js"
      }
    }
  }
}
```

### Server Types Configuration

**stdio** (most common):
```json
"my-server": {
  "type": "stdio",
  "command": "node mcp/server.js"
}
```

**HTTP**:
```json
"my-server": {
  "type": "http",
  "url": "http://localhost:8080"
}
```

**SSE**:
```json
"my-server": {
  "type": "sse",
  "url": "http://localhost:8080/events"
}
```

## Testing MCP Servers

### Test Server Directly

**TypeScript**:
```bash
node mcp/server.js
# Should start without errors
```

**Python**:
```bash
python mcp/server.py
# Should start without errors
```

### Test Tool Invocation

```typescript
// Create test client
const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

const response = await client.messages.create({
  model: "claude-sonnet-4-5-20250929",
  max_tokens: 1024,
  messages: [{
    role: "user",
    content: "Use the get_weather tool for London"
  }],
  mcpServers: {
    "weather-tools": server
  }
});
```

### Check Tool Availability

```bash
# In Claude Code after installing plugin
/mcp

# Should show your server and tools
```

## Best Practices

### Tool Design

✅ **DO**:
- Write detailed descriptions (3+ sentences)
- Include all parameters in schema
- Return structured, consistent data
- Handle errors gracefully
- Validate inputs
- Document return format

❌ **DON'T**:
- Use vague descriptions
- Skip parameter descriptions
- Return inconsistent formats
- Ignore error cases
- Allow invalid inputs
- Forget to document

### Security

✅ **DO**:
- Validate all inputs
- Use environment variables for secrets
- Limit query sizes
- Sanitize user inputs
- Use read-only operations when possible
- Rate limit external API calls

❌ **DON'T**:
- Trust user input blindly
- Hardcode API keys
- Allow unlimited queries
- Execute arbitrary code
- Grant write access unnecessarily
- Skip authentication checks

### Performance

✅ **DO**:
- Cache frequent requests
- Set reasonable timeouts
- Limit result sizes
- Use async operations
- Handle slow APIs gracefully

❌ **DON'T**:
- Make blocking calls
- Return huge datasets
- Skip pagination
- Forget timeouts
- Ignore performance impacts

## Troubleshooting

### Server Won't Start

**Check**:
1. Command path is correct in plugin.json
2. Dependencies are installed (`npm install` / `pip install`)
3. File has execute permissions (Unix)
4. No syntax errors in server code
5. Environment variables are set

### Tools Not Available

**Check**:
1. Server started successfully
2. Tool names follow naming rules
3. Tools exported correctly
4. plugin.json MCP configuration correct
5. Plugin is enabled

### Tool Invocation Fails

**Check**:
1. Input schema matches parameters
2. Required parameters provided
3. Parameter types match schema
4. Error handling returns proper structure
5. No exceptions thrown without catching

## Next Steps

- **Add skills to use tools**: See [Agent Skills](agent-skills.md)
- **Create commands**: See [Slash Commands](slash-commands.md)
- **Test locally**: See [Development Workflow](../guides/development-workflow.md)
- **See examples**: See [Complete Plugin Examples](../examples/complete-plugins.md)
