# Vibesafe Usage Skill

Expert skill for using Vibesafe - an AI-powered code generation system with verifiable, hash-locked specs.

## Overview

Vibesafe lets developers write readable specs as Python code that AI fills in. It creates a verifiable boundary between human intent and generated code with test-driven iteration.

**Core concept:** Write a spec with doctests → AI generates implementation → Tests verify → Use in production

## Quick Start

### Installation

```bash
# With uv (recommended)
uv pip install vibesafe

# With pip
pip install vibesafe
```

### Project Setup

1. **Create vibesafe.toml configuration:**
```toml
[project]
python = ">=3.12"
env = "dev"  # or "prod"

[provider.default]
kind = "openai-compatible"
model = "gpt-4o-mini"
temperature = 0.0
seed = 42
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"

[paths]
checkpoints = ".vibesafe/checkpoints"
cache = ".vibesafe/cache"
index = ".vibesafe/index.toml"

[prompts]
function = "prompts/function.j2"
http = "prompts/http_endpoint.j2"
```

### Template Resolution

Templates are resolved via `resolve_template_id()` from `vibesafe.config`:

**Resolution priority:**
1. Explicit `template` param on decorator
2. Type-based config default:
   - `http` units → `config.prompts.http`
   - `function` units → `config.prompts.function`

**Example:**
```python
from vibesafe.config import resolve_template_id

# Unit with explicit template
meta = {"template": "custom.j2"}
assert resolve_template_id(meta) == "custom.j2"

# Unit defaulting by type
meta = {"kind": "http"}
assert resolve_template_id(meta) == "prompts/http_endpoint.j2"

meta = {"kind": "function"}
assert resolve_template_id(meta) == "prompts/function.j2"

Impact on hashing: Template ID contributes to spec hash, so changing template (via
decorator or config) changes the hash.
```

2. **Set API key:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. **Add .vibesafe/ to .gitignore:**
```gitignore
.vibesafe/cache/      # LLM response cache (optional)
```

## Writing Specs

### Pure Functions

```python
from vibesafe import vibesafe, VibesafeHandled

@vibesafe.func
def fibonacci(n: int) -> int:
    """
    Return the nth Fibonacci number (0-indexed).

    >>> fibonacci(0)
    0
    >>> fibonacci(1)
    1
    >>> fibonacci(5)
    5
    >>> fibonacci(10)
    55
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    yield VibesafeHandled()
```

**Key components:**
1. **Decorator:** `@vibesafe.func` marks function for generation
2. **Type hints:** Provides signature to AI
3. **Docstring with doctests:** Specifies behavior with examples
4. **Pre-VibesafeHandled code:** Setup/validation before AI takes over
5. **VibesafeHandled marker:** Where AI-generated code begins

### HTTP Endpoints (FastAPI)

```python
from vibesafe import vibesafe, VibesafeHandled

@vibesafe.http(method="POST", path="/calculate")
async def calculate_endpoint(a: int, b: int, op: str) -> dict[str, int]:
    """
    Perform arithmetic operation on two numbers.

    >>> import anyio
    >>> anyio.run(calculate_endpoint, 5, 3, "add")
    {'result': 8}
    >>> anyio.run(calculate_endpoint, 10, 2, "divide")
    {'result': 5}
    """
    valid_ops = ["add", "subtract", "multiply", "divide"]
    if op not in valid_ops:
        raise ValueError(f"Invalid operation: {op}")
    return VibesafeHandled()
```

**HTTP-specific features:**
- `method`: HTTP method (GET, POST, PUT, DELETE, etc.)
- `path`: URL path (can include path parameters)
- `async def`: Must be async for endpoints
- Return `VibesafeHandled()` (not yield)

### FastAPI Integration

```python
from fastapi import FastAPI
from vibesafe.fastapi import mount

app = FastAPI()

# Mount vibesafe health/version routes at /_vibesafe
mount(app)

# Your vibesafe-decorated endpoints are automatically available
# Example: POST /calculate from @vibesafe.http(method="POST", path="/calculate")
```

**Mounted routes:**
- `GET /_vibesafe/health` - Health check endpoint
- `GET /_vibesafe/version` - Vibesafe version info

### Best Practices for Specs

✅ **DO:**
- Write clear, comprehensive docstrings
- Include 3-5 doctest examples covering edge cases
- Add type hints for all parameters and returns
- Include validation/setup code before `VibesafeHandled()`
- Test edge cases (empty inputs, negatives, None, etc.)
- Consider property-based tests for complex logic

❌ **DON'T:**
- Write implementation - let AI generate it
- Skip doctests - they're essential for verification
- Use complex dependencies without documenting them
- Mix spec logic with implementation

### Property-Based Testing (Hypothesis)

For complex functions, you can add Hypothesis property-based tests in your spec:

```python
from hypothesis import given, strategies as st

@vibesafe.func
def add(a: int, b: int) -> int:
    """
    Add two integers.

    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    """
    yield VibesafeHandled()

# Property-based test (optional)
@given(a=st.integers(), b=st.integers())
def test_add_commutative(a: int, b: int):
    """Test that addition is commutative."""
    assert add(a, b) == add(b, a)

@given(a=st.integers())
def test_add_identity(a: int):
    """Test that adding zero is identity."""
    assert add(a, 0) == a
```

**Hypothesis tests:**
- Run during `vibesafe test`
- Generate hundreds of test cases automatically
- Find edge cases you might miss
- Provide stronger verification than examples alone

## Core API

Vibesafe uses module-level decorators and registry functions:

```python
from vibesafe import vibesafe
from vibesafe.core import get_registry, get_unit

@vibesafe.func
def my_function(...):
    """Decorator registers to global module-level registry"""
    yield VibesafeHandled()

# Access registry
registry = get_registry()  # Returns dict[str, dict[str, Any]]

# Get specific unit
unit_meta = get_unit("module.path/function_name")  # Returns dict | None

Key functions:
- get_registry() → Global registry of all decorated units
- get_unit(unit_id) → Metadata for specific unit
- resolve_template_id(unit_meta, config) → Determine template path
```

## CLI Commands

### Scan for Units

```bash
# List all vibesafe-decorated functions
vibesafe scan

# List and generate shims (DEPRECATED)
vibesafe scan --write-shims
```

**Note:** `--write-shims` is deprecated as of v0.2. The shim system is no longer needed for importing generated code.

**Output shows:**
- Unit ID (module path + function name)
- Type (function or http)
- Number of doctests
- Compilation status

### Compile (Generate Code)

```bash
# Compile all units
vibesafe compile

# Compile specific unit
vibesafe compile --target app.math.ops/fibonacci

# Compile entire module
vibesafe compile --target app.math.ops

# Force recompilation
vibesafe compile --force
```

**What happens:**
1. Extracts spec (signature, docstring, body)
2. Computes spec hash
3. Renders prompt from template
4. Calls LLM with deterministic seed (with caching)
5. Cleans generated code (strips markdown blocks)
6. Validates implementation (checks function signature)
7. Saves generated code to checkpoint
8. Updates index.toml

### Test Generated Code

```bash
# Test all units
vibesafe test

# Test specific unit
vibesafe test --target app.math.ops/fibonacci
```

**Tests run:**
- All doctest examples from spec
- Hypothesis property-based tests (if defined)
- Quality gates: ruff linting and mypy type checking
- Optional sandbox execution for isolation

### Save (Activate) Checkpoints

```bash
# Save all (only if all tests pass)
vibesafe save

# Save specific unit
vibesafe save --target app.math.ops/fibonacci

# Save HTTP endpoints with dependency freezing
vibesafe save --target app.api.routes/calculate --freeze-http-deps
```

**Save means:**
- Tests must pass
- Checkpoint is marked as "active" in index
- Ready for production use

**Dependency Freezing (`--freeze-http-deps`):**
- Captures runtime package versions for HTTP endpoints
- Writes `requirements.vibesafe.txt` with pinned versions
- Records dependencies in checkpoint `meta.toml` under `[deps]`
- Ensures reproducible deployments

### Status and Drift Detection

```bash
# Show registry state and drift
vibesafe status

# Compare current spec hash to active checkpoint
vibesafe diff

# Compare specific unit
vibesafe diff --target app.math.ops/fibonacci
```

**Status shows:**
- All registered units
- Active checkpoint status
- Spec drift warnings (when spec changed vs active checkpoint)

**Diff shows:**
- Current spec hash vs active checkpoint hash
- Indicates if recompilation is needed

### Full Verification

```bash
# Run complete verification pipeline
vibesafe check

# Check specific unit
vibesafe check --target app.math.ops/fibonacci
```

**Check runs:**
1. Ruff linting
2. Mypy type checking
3. All doctests
4. Drift detection
5. Reports any failures

### Interactive REPL Mode

```bash
# Interactive compile/test loop for a unit
vibesafe repl --target app.math.ops/fibonacci
```

**REPL mode:**
- More permissive (allows missing doctests)
- Quick iteration cycle
- Immediate feedback on changes
- Perfect for developing specs

## Using Generated Code

### Direct Import (Recommended)

```python
# Decorated function automatically loads generated code
from app.math.ops import fibonacci

# When called, this loads the active checkpoint
result = fibonacci(10)
print(f"fibonacci(10) = {result}")
```

**Note:** This works when the checkpoint has been saved/activated. The decorator intercepts the import and loads from `.vibesafe/checkpoints/`.

### Using the Runtime Loader (Most Reliable)

```python
# Import the loader
from vibesafe.runtime import load_active

# Load specific functions by unit ID
multiply = load_active("test_vibesafe/multiply")
factorial = load_active("test_vibesafe/factorial")

# Use them
print(multiply(5, 7))    # 35
print(factorial(5))       # 120
```

**Advantages:**
- Works for all compiled functions
- No dependency on shim files
- Direct access to active checkpoints
- Better for programmatic usage

### Direct Usage in Application

```python
# The decorated function automatically loads generated code
from app.math.ops import fibonacci

# When called, this loads the active checkpoint
result = fibonacci(10)
```

**Caveat:** This only works if the checkpoint has been saved/activated.

## Workflow Patterns

### Standard Development Flow

```bash
# 1. Write spec with doctests
vim app/math/ops.py

# 2. Scan to verify registration
vibesafe scan

# 3. Check status before compilation
vibesafe status

# 4. Compile to generate code
vibesafe compile --target app.math.ops/fibonacci

# 5. Test the implementation
vibesafe test --target app.math.ops/fibonacci

# 6. If tests pass, save/activate
vibesafe save --target app.math.ops/fibonacci

# 7. Verify no drift
vibesafe diff

# 8. Use in code
python -c "from app.math.ops import fibonacci; print(fibonacci(10))"
```

### Iteration Flow (When Tests Fail)

```bash
# 1. Check what failed
vibesafe test --target app.math.ops/fibonacci

# 2. Update spec (add more examples, clarify docstring)
vim app/math/ops.py

# 3. Recompile with force
vibesafe compile --target app.math.ops/fibonacci --force

# 4. Test again
vibesafe test --target app.math.ops/fibonacci

# 5. Repeat until tests pass
```

### Batch Processing

```bash
# Compile all functions in a module
vibesafe compile --target app.math

# Test everything
vibesafe test

# Save everything (only if all pass)
vibesafe save
```

## Understanding the System

### Architecture & Core Modules

Vibesafe is organized into specialized modules in `src/vibesafe/`:

**Core System:**
- **core.py** - Module-level decorators (`@vibesafe.func`/`@vibesafe.http`) and registry (`get_registry()`, `get_unit()`)
- **ast_parser.py** - `SpecExtractor` class for parsing function specs using Python AST
- **codegen.py** - `CodeGenerator` pipeline for orchestrating code generation
- **runtime.py** - Checkpoint loading (`load_active()`, `write_shim()`, `update_index()`)
- **hashing.py** - Deterministic hashing for specs, checkpoints, and dependencies

**Provider & Configuration:**
- **providers.py** - LLM integration (`Provider` protocol, `OpenAICompatibleProvider`, `CachedProvider`)
- **config.py** - Configuration management via `vibesafe.toml` (Pydantic models)

**Testing & Validation:**
- **testing.py** - Doctest verification, quality gates (ruff/mypy), and Hypothesis support
- **exceptions.py** - Typed exceptions for better error handling

**Interfaces:**
- **cli.py** - Command-line interface (scan, compile, test, save, status, diff, check, repl)
- **mcp.py** - Model Context Protocol server for editor integration (JSON-RPC over stdio)
- **fastapi.py** - FastAPI helpers (`mount()` for health/version routes)

**Key Mechanisms:**
- **Hash-Locked Checkpoints** - Deterministic hashing ensures reproducibility
- **LLM Response Caching** - Responses cached by spec hash + seed in `.vibesafe/cache/`
- **Static Dependency Analysis** - Tracks names referenced in specs, includes in spec hash
- **Quality Gates** - Automatic ruff linting and mypy type checking before save
- **Markdown Stripping** - Auto-cleans LLM responses wrapped in code blocks

### MCP Server (Editor Integration)

Vibesafe includes a Model Context Protocol server for editor integration:

```bash
# Run MCP server (stdio mode)
python -m vibesafe.mcp
```

**Available MCP methods:**
- `scan` - List all decorated units
- `compile` - Generate implementations
- `test` - Run doctests
- `save` - Activate checkpoints
- `status` - Show registry state

**Use with editors:**
- VS Code extensions that support MCP
- Emacs/Vim plugins with JSON-RPC support
- Any editor with stdio-based plugin system

### Directory Structure

```
myproject/
├── vibesafe.toml           # Configuration
├── app/
│   └── math/
│       └── ops.py         # Your specs (decorated functions)
└── .vibesafe/
    ├── checkpoints/       # Generated implementations
    │   └── app/math/ops/fibonacci/
    │       └── <hash>/
    │           ├── impl.py      # Generated code
    │           └── meta.toml    # Metadata
    ├── index.toml         # Active checkpoint mapping
    └── cache/             # LLM response cache
```

### Hash-Based Verification

**Spec Hash:** Deterministically computed from:
- Function signature (name, parameters, return type)
- Docstring (including all doctests)
- Pre-VibesafeHandled body (setup code)
- Vibesafe version
- Template ID
- Provider model and parameters (temperature, seed)
- Static dependency digest (names referenced in spec)

**Checkpoint Hash:** Computed from:
- Spec hash
- Prompt hash (rendered template)
- Generated code

**Dependency Digest:** Includes:
- Source code of referenced functions/classes
- File paths and hashes
- Transitive dependencies

**In dev mode:** Warns on mismatch, auto-regenerates
**In prod mode:** Hard error on mismatch

### Index Management

The `.vibesafe/index.toml` file tracks active checkpoints:

```toml
[units."app.math.ops/fibonacci"]
checkpoint_hash = "abc123..."
spec_hash = "def456..."
activated_at = "2025-01-15T10:30:00Z"

[units."app.api.routes/calculate"]
checkpoint_hash = "ghi789..."
spec_hash = "jkl012..."
activated_at = "2025-01-15T11:00:00Z"
```

**Index operations:**
- `update_index()` - Updates mapping when saving checkpoints
- `load_active(unit_id)` - Loads implementation from active checkpoint
- Drift detection compares current spec_hash to index spec_hash

### Environment Modes

**Development (env = "dev"):**
- Hash mismatches trigger warnings
- Auto-regeneration enabled
- Easier iteration

**Production (env = "prod"):**
- Hash mismatches cause errors
- Strict verification
- Guarantees code integrity

## Advanced Usage

### Custom Providers

```toml
[provider.anthropic]
kind = "openai-compatible"  # Use OpenAI-compatible interface
model = "claude-3-sonnet-20240229"
base_url = "https://api.anthropic.com/v1"
api_key_env = "ANTHROPIC_API_KEY"
```

Use with decorator:
```python
@vibesafe.func(provider="anthropic")
def my_function(x: int) -> int:
    """Uses Anthropic provider."""
    yield VibesafeHandled()
```

### Custom Templates

Create `prompts/my_template.j2`:
```jinja2
You are generating code for this function:

{{ signature }}

Documentation:
{{ docstring }}

Generate complete implementation that passes these tests:
{% for example in doctests %}
{{ example.source }}
Expected: {{ example.want }}
{% endfor %}
```

Use with decorator:
```python
@vibesafe.func(template="prompts/my_template.j2")
def my_function(x: int) -> int:
    """Uses custom template."""
    yield VibesafeHandled()
```

### Inspecting Generated Code

```bash
# Find the checkpoint directory
ls .vibesafe/checkpoints/app/math/ops/fibonacci/

# Read the implementation
cat .vibesafe/checkpoints/app/math/ops/fibonacci/<hash>/impl.py

# Read metadata
cat .vibesafe/checkpoints/app/math/ops/fibonacci/<hash>/meta.toml
```

### Cache Management

```bash
# View cache size
du -sh .vibesafe/cache/

# Clear cache (will regenerate on next compile)
rm -rf .vibesafe/cache/

# Cache is keyed by prompt hash
ls .vibesafe/cache/
```

## Troubleshooting

### "has not been compiled yet" Error

**Problem:** Called decorated function before compilation
```python
RuntimeError: Function app.math.ops/fibonacci has not been compiled yet
```

**Solution:**
```bash
vibesafe compile --target app.math.ops/fibonacci
vibesafe test --target app.math.ops/fibonacci
vibesafe save --target app.math.ops/fibonacci
```

### "No vibesafe units found" When Running Scan

**Problem:** `vibesafe scan` shows "No vibesafe units found" even though you have decorated functions

**Root Cause:** The scan command only imports Python files from these directories:
- `app/**/*.py`
- `src/**/*.py`
- `*.py` (root level)

Files in other directories like `examples/`, `tests/`, or subdirectories won't be discovered.

**Solutions:**
1. **Move your specs** to one of the scanned directories (app/, src/, or root)
2. **Create a root-level file** that imports your specs:
```python
# specs.py (in project root)
from my_module.functions import *  # imports decorated functions
```
3. **Use PYTHONPATH** if files are elsewhere:
```bash
PYTHONPATH=examples vibesafe scan  # May not work in all cases
```

### Syntax Errors in Generated Code (Fixed in Latest Version)

**Problem:** Tests fail with `invalid syntax (impl.py, line 1)` even though compilation succeeded

**Root Cause (Fixed):** AI was returning code wrapped in markdown blocks (` ```python...``` `), which the older version didn't strip.

**Solution:**
- ✅ **This is now fixed** in the latest version (the code automatically strips markdown blocks)
- If using an older version, manually remove markdown delimiters from `.vibesafe/checkpoints/*/impl.py`
- Or update to the latest version with the fix

**Manual Fix for Old Versions:**
```bash
# Find the impl.py file
find .vibesafe -name "impl.py" -path "*your_function*"

# Edit to remove ```python and ``` markers
vim .vibesafe/checkpoints/.../impl.py
```

### Tests Failing

**Problem:** Generated code doesn't pass doctests

**Solutions:**
1. **Add more doctest examples** to clarify behavior
2. **Improve docstring** to be more explicit
3. **Add pre-VibesafeHandled setup** code to show context
4. **Check doctest format** - must be exact (including whitespace)
5. **Inspect generated code** to see what AI created:
```bash
# Find and read the implementation
find .vibesafe/checkpoints -name "impl.py" -path "*your_function*" -exec cat {} \;
```
6. **Force recompile** with different seed or clearer spec:
```toml
[provider.default]
seed = 43  # Try different seed
```
7. **Check doctest output format** - some types need special formatting:
```python
# For dicts, lists - order matters!
>>> word_frequency("hello world hello")
{'hello': 2, 'world': 1}  # Dict order may vary in Python <3.7
```

### Import Errors

**Problem:** Can't import decorated functions

**Solution:**
```bash
# Check that function was compiled and saved
vibesafe scan

# Check index for active checkpoints
cat .vibesafe/index.toml

# Verify checkpoint exists and is active
vibesafe status
```

### API Key Issues

**Problem:** `ValueError: API key not found`

**Solution:**
```bash
# Set environment variable matching config
export OPENAI_API_KEY="your-key"

# Or update vibesafe.toml
api_key_env = "CUSTOM_API_KEY"
export CUSTOM_API_KEY="your-key"
```

### Hash Mismatch in Production

**Problem:** `HashMismatchError` in prod

**Solution:**
This means generated code was modified. Either:
1. Recompile to regenerate
2. Fix the modification
3. Switch to dev mode temporarily

### Spec Drift Detected

**Problem:** `vibesafe diff` shows drift (spec changed vs active checkpoint)

**Root Cause:**
- Modified docstring or doctests
- Changed function signature
- Updated pre-VibesafeHandled code
- Changed template, provider, or vibesafe version

**Solution:**
```bash
# Review what changed
vibesafe diff --target module/func

# Recompile with new spec
vibesafe compile --target module/func --force

# Test new implementation
vibesafe test --target module/func

# Activate if tests pass
vibesafe save --target module/func
```

### Quality Gates Failing

**Problem:** `vibesafe test` or `vibesafe save` fails on ruff/mypy checks

**Solutions:**
1. **Fix linting issues:**
```bash
# Run ruff manually to see issues
ruff check src tests examples

# Auto-fix where possible
ruff check --fix src tests examples
```

2. **Fix type errors:**
```bash
# Run mypy manually
mypy src/vibesafe

# Add type hints or use type: ignore comments
```

3. **Configure quality gates in vibesafe.toml:**
```toml
[testing]
run_ruff = true
run_mypy = true
```

## Best Practices

### Spec Writing

1. **Start simple, iterate:** Begin with basic examples, add edge cases
2. **Cover edge cases:** Empty inputs, None, negatives, large values
3. **Use doctest ELLIPSIS:** For long outputs: `{...}`
4. **Type everything:** Full type hints help AI generate better code
5. **Document pre-conditions:** Use pre-VibesafeHandled code

### Compilation Strategy

1. **Compile incrementally:** Test individual functions before batch
2. **Use force sparingly:** Only when spec changes
3. **Version control checkpoints:** Consider committing .vibesafe/checkpoints
4. **Review generated code:** Inspect before production use

### Testing Strategy

1. **Test early and often:** Don't wait to batch test
2. **Add tests as you find issues:** Expand doctest coverage
3. **Use property-based tests:** For complex functions (Phase 2)
4. **Integration test generated code:** Test with real data

### Production Deployment

1. **Commit .vibesafe/checkpoints:** For reproducibility
2. **Use prod mode:** Set `env = "prod"` in vibesafe.toml
3. **Pin provider model:** Specify exact model version
4. **Monitor hash integrity:** Check logs for mismatches
5. **Version generated code:** Tag releases

## When to Use This Skill

✅ **Use this skill when:**
- Writing vibesafe spec functions
- Generating implementations with vibesafe
- Testing generated code
- Debugging vibesafe issues
- Setting up vibesafe projects
- Iterating on specs

❌ **Don't use for:**
- Building the vibesafe library itself
- Modifying vibesafe source code
- Non-Python languages
- Stateful/side-effectful code (use with caution)

## Quick Reference Card

```bash
# Setup
export OPENAI_API_KEY="key"

# Discovery & Status
vibesafe scan                              # List units
vibesafe scan --write-shims                # List + generate shims
vibesafe status                            # Show registry state & drift
vibesafe diff                              # Compare spec to active checkpoint

# Compilation & Testing
vibesafe compile --target module/func      # Generate code
vibesafe compile --force                   # Force recompile
vibesafe test --target module/func         # Run doctests + quality gates
vibesafe check                             # Full verification pipeline

# Activation
vibesafe save --target module/func         # Activate checkpoint
vibesafe save --freeze-http-deps           # Save + freeze dependencies

# Interactive Development
vibesafe repl --target module/func         # Interactive compile/test loop

# Editor Integration
python -m vibesafe.mcp                     # Run MCP server (stdio)

# Import Generated Code
from module import func                    # Direct import (recommended)
from vibesafe.runtime import load_active   # Load by unit ID
func = load_active("module/func")
```

## Tested Working Examples

These examples have been tested and verified to work with vibesafe:

### Simple Arithmetic

```python
from vibesafe import vibesafe, VibesafeHandled

@vibesafe.func
def multiply(a: int, b: int) -> int:
    """
    Multiply two integers.

    >>> multiply(2, 3)
    6
    >>> multiply(5, 7)
    35
    >>> multiply(-3, 4)
    -12
    >>> multiply(0, 10)
    0
    """
    yield VibesafeHandled()
```

**Generated Implementation:**
```python
def multiply(a: int, b: int) -> int:
    return a * b
```

### Recursive Functions

```python
@vibesafe.func
def factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer.

    >>> factorial(0)
    1
    >>> factorial(1)
    1
    >>> factorial(5)
    120
    >>> factorial(7)
    5040
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    yield VibesafeHandled()
```

**Generated Implementation:**
```python
def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
```

### String Manipulation

```python
@vibesafe.func
def reverse_string(text: str) -> str:
    """
    Reverse a string.

    >>> reverse_string("hello")
    'olleh'
    >>> reverse_string("Python")
    'nohtyP'
    >>> reverse_string("12345")
    '54321'
    >>> reverse_string("")
    ''
    """
    yield VibesafeHandled()
```

**Generated Implementation:**
```python
def reverse_string(text: str) -> str:
    return text[::-1]
```

### List Generation

```python
@vibesafe.func
def fibonacci_list(n: int) -> list[int]:
    """
    Generate list of first n Fibonacci numbers.

    >>> fibonacci_list(5)
    [0, 1, 1, 2, 3]
    >>> fibonacci_list(10)
    [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    >>> fibonacci_list(1)
    [0]
    >>> fibonacci_list(0)
    []
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    yield VibesafeHandled()
```

**Generated Implementation:**
```python
def fibonacci_list(n: int) -> list:
    if n < 0:
        raise ValueError("n must be non-negative")

    fib_sequence = []
    a, b = 0, 1

    for _ in range(n):
        fib_sequence.append(a)
        a, b = b, a + b

    return fib_sequence
```

### Dictionary Operations

```python
@vibesafe.func
def word_frequency(text: str) -> dict[str, int]:
    """
    Count word frequency in text (case-insensitive).

    >>> word_frequency("Hello world hello")
    {'hello': 2, 'world': 1}
    >>> word_frequency("The quick brown fox jumps over the lazy dog")
    {'the': 2, 'quick': 1, 'brown': 1, 'fox': 1, 'jumps': 1, 'over': 1, 'lazy': 1, 'dog': 1}
    >>> word_frequency("")
    {}
    """
    # Normalize text to lowercase for counting
    normalized = text.lower()
    yield VibesafeHandled()
```

**Generated Implementation:**
```python
def word_frequency(text: str) -> dict[str, int]:
    normalized = text.lower()

    if not normalized.strip():
        return {}

    words = normalized.split()
    frequency = {}

    for word in words:
        frequency[word] = frequency.get(word, 0) + 1

    return frequency
```

### Complete Working Demo Script

```python
#!/usr/bin/env python3
"""Demo script showing vibesafe-generated functions."""

from vibesafe.runtime import load_active

# Load AI-generated functions
multiply = load_active("test_vibesafe/multiply")
factorial = load_active("test_vibesafe/factorial")
reverse_string = load_active("test_vibesafe/reverse_string")
fibonacci_list = load_active("test_complex/fibonacci_list")
word_frequency = load_active("test_complex/word_frequency")

# Test them
print("Arithmetic:", multiply(12, 8))           # 96
print("Factorial:", factorial(6))                # 720
print("Reverse:", reverse_string("Python"))     # nohtyP
print("Fibonacci:", fibonacci_list(7))          # [0, 1, 1, 2, 3, 5, 8]
print("Frequency:", word_frequency("hello world hello"))  # {'hello': 2, 'world': 1}
```

**Running the demo:**
```bash
# 1. Create specs with the functions above
# 2. Compile them
vibesafe compile

# 3. Test them
vibesafe test

# 4. Run demo
python demo.py
```

## Current Status & Features

### Phase 1 - MVP Complete ✅

**Implemented:**
- ✅ Python 3.12+ support with full type hints
- ✅ Pure functions via `@vibesafe.func`
- ✅ HTTP endpoints via `@vibesafe.http` (FastAPI integration)
- ✅ Doctest-based verification with quality gates (ruff/mypy)
- ✅ Hash-locked checkpoints with drift detection
- ✅ OpenAI-compatible providers with response caching
- ✅ CLI: scan, compile, test, save, status, diff, check, repl
- ✅ Dependency tracking and freezing (`--freeze-http-deps`)
- ✅ Jinja2 prompt templates (customizable)
- ✅ MCP server for editor integration
- ✅ Automatic markdown code block stripping
- ✅ Hypothesis property-based testing support
- ✅ FastAPI health/version route mounting
- ✅ Static dependency analysis and hashing

**Key Improvements:**
- **Markdown Stripping:** Auto-cleans LLM responses wrapped in code blocks
- **Quality Gates:** Automatic ruff linting and mypy type checking
- **Drift Detection:** `vibesafe diff` shows when specs change
- **Full Verification:** `vibesafe check` runs complete pipeline
- **Interactive REPL:** Fast iteration with `vibesafe repl`
- **Dependency Freezing:** Reproducible deployments with pinned versions
- **LLM Caching:** Responses cached by spec hash for faster recompilation

### Known Limitations

1. **Scan Discovery:** Only scans `app/`, `src/`, and root-level `.py` files (not `examples/`, `tests/`)
2. **Shim Generation:** Overwrites existing shims (one function per file)
3. **Dict Ordering:** Doctest dict comparisons require consistent ordering (Python 3.7+ guaranteed)
4. **Stateful Functions:** Not recommended for functions with side effects
5. **Sandbox Execution:** Basic support, needs enhancement for full isolation

## Advanced Configuration

### Sandbox Execution (Optional)

```toml
[sandbox]
enabled = false      # Set to true for isolated execution
timeout = 10         # Timeout in seconds
memory_mb = 256      # Memory limit
```

**When to enable:**
- Testing untrusted generated code
- Isolating side effects
- Resource-limited environments

**Limitations:**
- Basic implementation in current version
- May affect performance
- Not all system calls supported

### Multiple Providers

```toml
[provider.default]
kind = "openai-compatible"
model = "gpt-4o-mini"
temperature = 0.0
seed = 42
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"

[provider.claude]
kind = "openai-compatible"
model = "claude-3-5-sonnet-20241022"
temperature = 0.0
seed = 42
base_url = "https://api.anthropic.com/v1"
api_key_env = "ANTHROPIC_API_KEY"

[provider.local]
kind = "openai-compatible"
model = "llama-3-70b"
temperature = 0.0
base_url = "http://localhost:8000/v1"
api_key_env = "LOCAL_API_KEY"
```

**Use different providers per function:**
```python
@vibesafe.func(provider="claude")
def complex_logic(x: int) -> int:
    """Uses Claude for complex reasoning."""
    yield VibesafeHandled()

@vibesafe.func(provider="local")
def simple_math(a: int, b: int) -> int:
    """Uses local model for simple tasks."""
    yield VibesafeHandled()
```

## Common Workflows

### New Project Setup

```bash
# 1. Create project structure
mkdir myproject && cd myproject
mkdir -p src/myproject prompts

# 2. Create vibesafe.toml
cat > vibesafe.toml <<'EOF'
[project]
python = ">=3.12"
env = "dev"

[provider.default]
kind = "openai-compatible"
model = "gpt-4o-mini"
temperature = 0.0
seed = 42
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"

[paths]
checkpoints = ".vibesafe/checkpoints"
cache = ".vibesafe/cache"
index = ".vibesafe/index.toml"
EOF

# 3. Set up git
git init
echo ".vibesafe/cache/" >> .gitignore

# 4. Set API key
export OPENAI_API_KEY="your-key"

# 5. Install vibesafe
uv pip install vibesafe

# 6. Write your first spec
# (create src/myproject/math.py with vibesafe decorators)

# 7. Start developing
vibesafe scan --write-shims
vibesafe compile
vibesafe test
vibesafe save
```

### Production Deployment

```bash
# 1. Set production mode
# Edit vibesafe.toml: env = "prod"

# 2. Compile all units
vibesafe compile

# 3. Run full verification
vibesafe check

# 4. Freeze dependencies
vibesafe save --freeze-http-deps

# 5. Commit everything
git add .vibesafe/checkpoints .vibesafe/index.toml vibesafe.toml requirements.vibesafe.txt
git commit -m "Add vibesafe checkpoints for v1.0"

# 6. Deploy
# Include .vibesafe/checkpoints and .vibesafe/index.toml in deployment
```

### CI/CD Integration

```yaml
# .github/workflows/vibesafe.yml
name: Vibesafe CI

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install vibesafe

      - name: Scan units
        run: vibesafe scan

      - name: Check for drift
        run: vibesafe diff

      - name: Run full verification
        run: vibesafe check
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Resources

- **Repository:** https://github.com/julep-ai/vibesafe
- **Examples:** See `examples/` directory in the repo
- **Templates:** See `prompts/` directory for Jinja2 prompt templates
- **Issue Tracker:** Report bugs and request features on GitHub
- **Documentation:** This skill file is the most comprehensive guide

## Reference Information

**Git changes summary:**
- `src/vibesafe/core.py`: Refactored from `VibesafeDecorator` class to module-level `_registry` with `get_registry()` and `get_unit()` helpers
- `src/vibesafe/cli.py`: Deprecated `--write-shims`, removed automatic shim writing
- `src/vibesafe/config.py`: Added `resolve_template_id()` function

**Key file locations:**
- Skills file: `.claude/skills/vibesafe.md`
- Core module: `src/vibesafe/core.py`
- Config module: `src/vibesafe/config.py`
- CLI module: `src/vibesafe/cli.py`

## Skill Usage Guidelines

✅ **Use this skill when:**
- Writing or updating vibesafe spec functions
- Generating implementations with vibesafe CLI
- Testing and verifying generated code
- Debugging vibesafe issues (compilation, testing, drift)
- Setting up new vibesafe projects
- Configuring providers, templates, or quality gates
- Integrating vibesafe with FastAPI applications
- Setting up CI/CD for vibesafe projects

❌ **Don't use this skill for:**
- Developing the vibesafe library itself (core features)
- Modifying vibesafe source code (use development docs)
- Non-Python languages (vibesafe is Python-only)
- Projects without type hints (vibesafe requires them)
- Real-time/stateful code (vibesafe is for deterministic functions)
