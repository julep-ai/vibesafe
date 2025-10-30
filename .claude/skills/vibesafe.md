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
generated = "__generated__"

[prompts]
function = "prompts/function.j2"
http = "prompts/http_endpoint.j2"
```

2. **Set API key:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. **Add .vibesafe/ to .gitignore:**
```gitignore
.vibesafe/cache/      # LLM response cache (optional)
__generated__/       # Generated shims (optional)
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

### Best Practices for Specs

✅ **DO:**
- Write clear, comprehensive docstrings
- Include 3-5 doctest examples covering edge cases
- Add type hints for all parameters and returns
- Include validation/setup code before `VibesafeHandled()`
- Test edge cases (empty inputs, negatives, None, etc.)

❌ **DON'T:**
- Write implementation - let AI generate it
- Skip doctests - they're essential for verification
- Use complex dependencies without documenting them
- Mix spec logic with implementation

## CLI Commands

### Scan for Units

```bash
# List all vibesafe-decorated functions
vibesafe scan

# List and generate shims
vibesafe scan --write-shims
```

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
4. Calls LLM with deterministic seed
5. Saves generated code to checkpoint
6. Updates index.toml
7. Writes __generated__ shim

### Test Generated Code

```bash
# Test all units
vibesafe test

# Test specific unit
vibesafe test --target app.math.ops/fibonacci
```

**Tests run:**
- All doctest examples from spec
- Type checking (if configured)
- Linting (if configured)

### Save (Activate) Checkpoints

```bash
# Save all (only if all tests pass)
vibesafe save

# Save specific unit
vibesafe save --target app.math.ops/fibonacci
```

**Save means:**
- Tests must pass
- Checkpoint is marked as "active" in index
- Ready for production use

## Using Generated Code

### Import from __generated__

```python
# After compilation and successful tests
from __generated__.app.math.ops import fibonacci

result = fibonacci(10)  # Uses AI-generated implementation
print(f"fibonacci(10) = {result}")
```

### Direct Usage in Application

```python
# The decorated function automatically loads generated code
from app.math.ops import fibonacci

# When called, this loads the active checkpoint
result = fibonacci(10)
```

## Workflow Patterns

### Standard Development Flow

```bash
# 1. Write spec with doctests
vim app/math/ops.py

# 2. Scan to verify registration
vibesafe scan

# 3. Compile to generate code
vibesafe compile --target app.math.ops/fibonacci

# 4. Test the implementation
vibesafe test --target app.math.ops/fibonacci

# 5. If tests pass, save/activate
vibesafe save --target app.math.ops/fibonacci

# 6. Use in code
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

### Directory Structure

```
myproject/
├── vibesafe.toml           # Configuration
├── app/
│   └── math/
│       └── ops.py         # Your specs
├── __generated__/         # Auto-generated shims
│   └── app/
│       └── math/
│           └── ops.py     # import from here
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
- Function signature
- Docstring
- Pre-VibesafeHandled body
- Vibesafe version
- Template ID
- Provider model
- Dependencies

**Checkpoint Hash:** Computed from:
- Spec hash
- Prompt hash
- Generated code

**In dev mode:** Warns on mismatch, auto-regenerates
**In prod mode:** Hard error on mismatch

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

### Tests Failing

**Problem:** Generated code doesn't pass doctests

**Solutions:**
1. **Add more doctest examples** to clarify behavior
2. **Improve docstring** to be more explicit
3. **Add pre-VibesafeHandled setup** code to show context
4. **Check doctest format** - must be exact
5. **Force recompile** with different seed:
```toml
[provider.default]
seed = 43  # Try different seed
```

### Import Errors

**Problem:** Can't import from __generated__

**Solution:**
```bash
# Regenerate shims
vibesafe scan --write-shims

# Check index
cat .vibesafe/index.toml

# Verify checkpoint exists
vibesafe scan
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

# Workflow
vibesafe scan                              # List units
vibesafe compile --target module/func     # Generate
vibesafe test --target module/func        # Test
vibesafe save --target module/func        # Activate

# Flags
--force                                   # Force recompile
--write-shims                            # Generate __generated__

# Import
from __generated__.module import func    # Use generated code
```

## Resources

- Repository: https://github.com/julep-ai/vibesafe
- Examples: See `examples/` directory
- Templates: See `prompts/` directory
