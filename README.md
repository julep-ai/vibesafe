# Vibesafe

**Vibe safely** - AI-powered code generation with verifiable specs.

Vibesafe is a developer-facing system that lets engineers write readable specs as Python code that AI fills in. It creates a verifiable, hash-locked boundary between human intent and generated code, while keeping iteration and integration friction-free.

## Core Goals

- **Readable Specs**: Developers write small, typed, example-based specs they themselves will read
- **Trustable Code**: Generated code is hash-verifiable and versioned; no hidden AI state
- **Fast Iteration**: Iteration loop is fast, local, and test-driven
- **Composability**: Generated functions compose naturally with normal Python modules

## Quick Start

### Installation

```bash
# Install with uv
uv pip install -e .

# Or with pip
pip install -e .
```

### Basic Usage

1. **Write a spec:**

```python
# examples/math/ops.py
from vibesafe import vibesafe, VibesafeHandled

@vibesafe.func
def sum_str(a: str, b: str) -> str:
    """
    Add two integers represented as strings.

    >>> sum_str("2", "3")
    '5'
    >>> sum_str("10", "20")
    '30'
    """
    a_int, b_int = int(a), int(b)
    yield VibesafeHandled()
```

2. **Configure vibesafe:**

```toml
# vibesafe.toml
[provider.default]
kind = "openai-compatible"
model = "gpt-4o-mini"
api_key_env = "OPENAI_API_KEY"
```

3. **Generate implementation:**

```bash
# Set API key
export OPENAI_API_KEY="your-key-here"

# Compile the function
vibesafe compile --target examples.math.ops/sum_str

# Test it
vibesafe test --target examples.math.ops/sum_str

# Use it in code
from __generated__.examples.math.ops import sum_str
print(sum_str("5", "7"))  # "12"
```

## Features

### Phase 1 (MVP) - Implemented ✅

- ✅ Python 3.12+ support
- ✅ Pure functions with `@vibesafe.func`
- ✅ HTTP endpoints with `@vibesafe.http` (FastAPI)
- ✅ Doctest-based verification
- ✅ Hash-locked checkpoints
- ✅ OpenAI-compatible providers
- ✅ CLI commands: `scan`, `compile`, `test`, `save`
- ✅ Jinja2 prompt templates
- ✅ Basic MCP server for editor integration

### Phase 2 (Coming Soon)

- Interactive REPL mode
- Property-based tests with Hypothesis
- Advanced dependency tracing
- Multiple provider backends
- Sandbox execution
- Web UI dashboard

## CLI Commands

### `vibesafe scan`

List all vibesafe units in the project:

```bash
vibesafe scan
vibesafe scan --write-shims  # Also generate __generated__ shims
```

### `vibesafe compile`

Generate implementations:

```bash
vibesafe compile                        # Compile all units
vibesafe compile --target MODULE        # Compile specific module
vibesafe compile --target UNIT_ID       # Compile specific unit
vibesafe compile --force                # Force recompilation
```

### `vibesafe test`

Run doctest verification:

```bash
vibesafe test                  # Test all units
vibesafe test --target UNIT_ID # Test specific unit
```

### `vibesafe save`

Activate checkpoints (after tests pass):

```bash
vibesafe save                  # Save all (if all tests pass)
vibesafe save --target UNIT_ID # Save specific unit
```

## Architecture

```
project/
├── vibesafe.toml          # Configuration
├── prompts/
│   ├── function.j2        # Function prompt template
│   └── http_endpoint.j2   # HTTP endpoint template
├── examples/
│   └── math/
│       └── ops.py         # Spec with @vibesafe.func
├── __generated__/         # Generated shims
│   └── examples/
│       └── math/
│           └── ops.py     # Auto-generated imports
└── .vibesafe/
    ├── checkpoints/       # Implementation checkpoints
    │   └── examples/math/ops/sum_str/
    │       └── <hash>/
    │           ├── impl.py
    │           └── meta.toml
    ├── index.toml         # Active checkpoint mapping
    └── cache/             # LLM response cache
```

## How It Works

1. **Spec Definition**: Mark functions with `@vibesafe.func` or `@vibesafe.http`
2. **AST Extraction**: Parse signature, docstring, and pre-VibesafeHandled body
3. **Hash Computation**: Create deterministic hash from spec + model + template
4. **Code Generation**: Render prompt via Jinja2, call LLM with seed
5. **Verification**: Run doctests against generated implementation
6. **Checkpoint Storage**: Save implementation with metadata in `.vibesafe/`
7. **Runtime Loading**: `__generated__` shims load active checkpoints

## Configuration

See `vibesafe.toml` for full configuration options:

- **Provider settings**: Model, temperature, API keys
- **Path configuration**: Where checkpoints and cache are stored
- **Prompt templates**: Customize code generation prompts
- **Sandbox options**: Optional execution isolation

## Examples

See the `examples/` directory for:

- `examples/math/ops.py` - Pure function examples
- `examples/api/routes.py` - FastAPI endpoint examples

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run tests in parallel
pytest -n auto

# Type checking
mypy src/vibesafe

# Linting
ruff check src/vibesafe

# Format code
ruff format src/vibesafe
```

## CI/CD

The repository uses GitHub Actions for continuous integration:

### Standard CI Pipeline
- **Linting**: Runs `ruff` to check code style and quality
- **Type Checking**: Runs `mypy` for static type analysis
- **Testing**: Runs `pytest` with parallel execution and coverage reporting
- **Matrix Testing**: Tests on Python 3.12 and 3.13

### Claude-Powered Automation

This repository includes AI-powered code review and test analysis:

- **Automated Code Review**: Claude Sonnet 4 reviews all PRs, providing:
  - Summary of changes
  - Code quality feedback
  - Security and performance concerns
  - Actionable suggestions

- **Test Failure Analysis**: When tests fail, Claude analyzes the failure and provides:
  - Root cause analysis
  - Debugging steps
  - Classification (bug vs. flaky test vs. environment issue)
  - Priority assessment

**Setup:** See [`.github/CLAUDE_ACTIONS.md`](.github/CLAUDE_ACTIONS.md) for configuration instructions.

**Requirements:** Set `ANTHROPIC_API_KEY` in repository secrets.

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
