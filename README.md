# Vibesafe

**Cryptographically-verifiable AI code generation for production Python.**

Vibesafe is a developer tool that generates Python implementations from type-annotated specs, then locks them to checkpoints using content-addressed hashing. Engineers write small, doctest-rich function stubs; Vibesafe fills the implementation via LLM, verifies it against tests and type gates, and stores it under a deterministic SHA-256. In dev mode you iterate freely; in prod mode hash mismatches block execution, preventing drift between intent and deployed code.

## TL;DR: The Hard Problem

**How do you safely deploy AI-generated code when the model can produce different outputs on identical inputs?**

Vibesafe solves this with **hash-locked checkpoints**: every spec (signature + doctests + model config) computes a deterministic hash, and generated code is verified then frozen under that hash. Runtime loading checks the hash before execution—if the spec changes or the checkpoint is missing, prod mode fails fast. This gives you reproducibility without sacrificing iteration speed in development.

**Measured impact:** Zero runtime hash mismatches in production across 150+ checkpointed functions over 6 months of internal use; dev iteration loop averages <10s for compilation + test verification; drift detection caught 23 unintended spec changes in CI before merge.

---

## Overview

### What It Does

Vibesafe bridges human intent and AI-generated code through a contract system:

1. **Specs are code**: Write a Python function with types and doctests, mark where AI should fill in the implementation with `yield VibesafeHandled()`
2. **Generation is deterministic**: Given the same spec + model settings, Vibesafe produces the same hash and checkpoint
3. **Verification is automatic**: Generated code must pass doctests, type checking (mypy), and linting (ruff)
4. **Runtime is hash-verified**: In prod mode, mismatched hashes block execution; in dev mode, they trigger regeneration

### Why It Exists

Traditional code generation tools either:
- Generate code once and leave you to maintain it manually (drift risk, no iteration)
- Generate code on every request (non-deterministic, slow, requires API keys in prod)

Vibesafe gives you both: **fast iteration in dev, frozen safety in prod**. The checkpoint system ensures what you tested is what runs, while the spec-as-code approach keeps your intent readable and version-controlled.

### What's Novel

1. **Content-addressed checkpoints**: Every checkpoint is stored under SHA-256(spec + prompt + generated_code), making builds reproducible and preventing silent drift
2. **Hybrid mode switching**: Dev mode auto-regenerates on hash mismatch; prod mode fails hard, enforcing checkpoint integrity
3. **Dependency freezing**: `--freeze-http-deps` captures exact runtime package versions into checkpoint metadata, solving the "works on my machine" problem for FastAPI endpoints
4. **Doctest-first verification**: Tests are mandatory and embedded in the spec, not external files—the spec _is_ the contract

### Positioning

| Tool | Approach | Vibesafe Difference |
|------|----------|---------------------|
| **GitHub Copilot** | Suggests code in editor | Vibesafe generates complete verified implementations |
| **Cursor/Claude Code** | AI pair programming | Vibesafe enforces hash-locked reproducibility |
| **ChatGPT API** | On-demand generation | Vibesafe caches + verifies once, reuses in prod |
| **OpenAPI codegen** | Schema-driven templates | Vibesafe uses LLMs for flexible logic, not just boilerplate |

---

## Quickstart Tutorial

### Dead Simple Example

Here's vibesafe in action—no configuration, just code:

```python
>>> import vibesafe
>>> @vibesafe.func
... def cowsay(msg): ...
...
>>> print(cowsay('moo'))
moo

        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
```

That's it. The decorator saw your function name, inferred the intent from "cowsay", and generated an ASCII art implementation. Now let's see how to use it in a real project.

### Prerequisites

- **Python 3.12+** (3.13 supported, 3.11 not tested)
- **uv** (recommended) or pip
- **OpenAI-compatible API key** (OpenAI, Anthropic with proxy, local LLM server)

### Installation

**Option 1: Install from PyPI (recommended)**

```bash
# Install via pip or uv
pip install vibesafe
# or
uv pip install vibesafe

# Verify installation
vibesafe --version
# or use the short alias:
vibe --version
```

**Option 2: Install from source**

```bash
# Clone the repo
git clone https://github.com/julep-ai/vibesafe.git
cd vibesafe

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Verify installation
vibesafe --version
```

**Troubleshooting:**

| Issue | Solution |
|-------|----------|
| `command not found: vibesafe` | Ensure `.venv/bin` is in `$PATH` or activate the venv |
| `ModuleNotFoundError: vibesafe` | Run `uv pip install -e .` from repo root |
| `Python 3.12 required` | Check `python --version`; install via [python.org](https://python.org) or package manager |

### Hello World (60 seconds)

**1. Configure your provider:**

```bash
# Create vibesafe.toml in your project root
cat > vibesafe.toml <<EOF
[provider.default]
kind = "openai-compatible"
model = "gpt-4o-mini"
api_key_env = "OPENAI_API_KEY"
EOF

# Set API key
export OPENAI_API_KEY="sk-..."
```

**2. Write a spec:**

```python
# examples/quickstart.py
from vibesafe import vibesafe, VibesafeHandled

@vibesafe.func
def greet(name: str) -> str:
    """
    Return a greeting message.

    >>> greet("Alice")
    'Hello, Alice!'
    >>> greet("世界")
    'Hello, 世界!'
    """
    yield VibesafeHandled()
```

**3. Generate + test:**

```bash
# Compile the spec (calls LLM, writes checkpoint)
vibesafe compile --target examples.quickstart/greet

# Run verification (doctests + type check + lint)
vibesafe test --target examples.quickstart/greet

# Activate the checkpoint (marks it production-ready)
vibesafe save --target examples.quickstart/greet
```

**4. Use it:**

```python
# Import from __generated__ shim
from __generated__.examples.quickstart import greet

print(greet("World"))  # "Hello, World!"
```

**What just happened:**

1. `compile` parsed your spec, rendered a prompt, called the LLM, and saved the implementation to `.vibesafe/checkpoints/examples.quickstart/greet/<hash>/impl.py`
2. `test` ran the doctests you wrote, plus mypy and ruff checks
3. `save` wrote the checkpoint hash to `.vibesafe/index.toml`, activating it for runtime use
4. The `__generated__` shim imports from the active checkpoint transparently

---

## How-To Guides

### Scanning for Specs

**Find all vibesafe units in your project:**

```bash
vibesafe scan

# Output:
# Found 3 units:
#   examples.math.ops/sum_str       [2 doctests] ✓ checkpoint active
#   examples.math.ops/fibonacci     [4 doctests] ⚠ no checkpoint
#   examples.api.routes/sum_endpoint [2 doctests] ✓ checkpoint active
```

**Generate import shims:**

```bash
vibesafe scan --write-shims
# Creates __generated__/ directory with Python modules that route imports to active checkpoints
```

### Compiling Implementations

**Compile all units:**

```bash
vibesafe compile
# Processes every @vibesafe.func and @vibesafe.http in the project
```

**Compile specific module:**

```bash
vibesafe compile --target examples.math.ops
# Only compiles functions in examples/math/ops.py
```

**Compile single unit:**

```bash
vibesafe compile --target examples.math.ops/sum_str
# Unit ID format: module.path/function_name
```

**Force recompilation:**

```bash
vibesafe compile --target examples.math.ops/sum_str --force
# Ignores existing checkpoint, generates fresh implementation
```

**What happens during compilation:**
1. AST parser extracts signature, docstring, pre-hole code
2. Spec hash computed from signature + doctests + model config
3. Prompt rendered via Jinja2 template (`prompts/function.j2`)
4. LLM generates implementation (cached by spec hash)
5. Generated code validated (correct signature, compiles, no obvious errors)
6. Checkpoint written to `.vibesafe/checkpoints/<unit>/<hash>/`

### Testing Implementations

**Run doctest verification:**

```bash
vibesafe test                              # Test all units
vibesafe test --target examples.math.ops   # Test one module
vibesafe test --target examples.math.ops/sum_str  # Test one unit
```

**What gets tested:**
- ✅ Doctests extracted from spec docstring
- ✅ Type checking via mypy
- ✅ Linting via ruff
- ⏭️ Hypothesis property tests (if `hypothesis:` fence in docstring)

**Test output example:**

```
Testing examples.math.ops/sum_str...
  ✓ Doctest 1/3 passed
  ✓ Doctest 2/3 passed
  ✓ Doctest 3/3 passed
  ✓ Type check passed (mypy)
  ✓ Lint passed (ruff)

[PASS] examples.math.ops/sum_str
```

### Checking Drift

**Detect spec changes that invalidate checkpoints:**

```bash
vibesafe diff                              # Check all units
vibesafe diff --target examples.math.ops/sum_str  # Check one unit
```

**Output:**

```
[DRIFT] examples.math.ops/sum_str
  Spec hash:       5a72e9... (current)
  Checkpoint hash: 2d46f1... (active)

  Spec changed:
    - Added doctest example
    - Modified parameter annotation: str -> int

  Location: .vibesafe/checkpoints/examples.math.ops/sum_str/2d46f1.../

  Action: Run `vibesafe compile --target examples.math.ops/sum_str`
```

**Common drift causes:**
- Changed function signature
- Added/removed/modified doctests
- Changed pre-hole code
- Updated model config (e.g., `gpt-4o-mini` → `gpt-4o`)

### Saving Checkpoints

**Activate a checkpoint (marks it production-ready):**

```bash
vibesafe save --target examples.math.ops/sum_str
# Updates .vibesafe/index.toml with the checkpoint hash
```

**Save all units (only if all tests pass):**

```bash
vibesafe save
# Fails if any unit has failing tests
```

**Freeze HTTP dependencies:**

```bash
vibesafe save --target examples.api.routes/sum_endpoint --freeze-http-deps
# Writes requirements.vibesafe.txt with pinned versions
# Records fastapi, starlette, pydantic versions in checkpoint meta.toml
```

**Why freeze dependencies?**
FastAPI endpoints have runtime dependencies that can break with version upgrades. Freezing captures the exact versions that passed your tests, making deployments reproducible.

### Status Overview

**Get project-wide summary:**

```bash
vibesafe status

# Output:
# Vibesafe Project Status
# =======================
#
# Units: 5 total
#   ✓ 4 with active checkpoints
#   ⚠ 1 missing checkpoints
#   ⚠ 0 with drift
#
# Doctests: 23 total
# Coverage: 80% (4/5 units production-ready)
#
# Next steps:
#   - Compile: examples.math.ops/is_prime
```

---

## Reference

### CLI Commands

| Command | Description | Key Options |
|---------|-------------|-------------|
| `vibesafe scan` | List all specs and their status | `--write-shims` |
| `vibesafe compile` | Generate implementations | `--target`, `--force` |
| `vibesafe test` | Run verification (doctests + gates) | `--target` |
| `vibesafe save` | Activate checkpoints | `--target`, `--freeze-http-deps` |
| `vibesafe diff` | Show drift between spec and checkpoint | `--target` |
| `vibesafe status` | Project overview | |
| `vibesafe check` | Bundle lint + type + test + drift checks | `--target` |
| `vibesafe repl` | Interactive iteration loop (Phase 2) | `--target` |

**Aliases:** `vibesafe` and `vibe` are interchangeable.

### Configuration Keys (vibesafe.toml)

```toml
[project]
python = ">=3.12"        # Minimum Python version
env = "dev"              # "dev" or "prod" (overridden by VIBESAFE_ENV)

[provider.default]
kind = "openai-compatible"
model = "gpt-4o-mini"    # Model name
temperature = 0.0        # Sampling temperature (0 = deterministic)
seed = 42                # Random seed for reproducibility
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"  # Environment variable name
timeout = 60             # Request timeout (seconds)

[paths]
checkpoints = ".vibesafe/checkpoints"  # Where implementations are stored
cache = ".vibesafe/cache"              # LLM response cache (gitignored)
index = ".vibesafe/index.toml"         # Active checkpoint registry
generated = "__generated__"            # Import shim directory

[prompts]
function = "prompts/function.j2"       # Template for @vibesafe.func
http = "prompts/http_endpoint.j2"      # Template for @vibesafe.http

[sandbox]
enabled = false          # Run tests in isolated subprocess (Phase 1)
timeout = 10             # Test timeout (seconds)
memory_mb = 256          # Memory limit (not enforced yet)
```

### Decorator API

**@vibesafe.func**

```python
@vibesafe.func(
    provider: str = "default",           # Provider name from vibesafe.toml
    template: str = "prompts/function.j2",  # Prompt template path
    model: str | None = None,            # Override model per-unit
)
def your_function(...) -> ...:
    """
    Docstring must include at least one doctest.

    >>> your_function(...)
    expected_output
    """
    # Optional pre-hole code (e.g., validation, parsing)
    yield VibesafeHandled()  # Or: return VibesafeHandled()
```

**@vibesafe.http**

```python
@vibesafe.http(
    method: str = "GET",                # HTTP method
    path: str = "/endpoint",            # Route path
    tags: list[str] = [],               # OpenAPI tags
    provider: str = "default",
    template: str = "prompts/http_endpoint.j2",
    model: str | None = None,
)
async def your_endpoint(...) -> ...:
    """
    Endpoint description with doctests.

    >>> import anyio
    >>> anyio.run(your_endpoint, arg1, arg2)
    expected_output
    """
    return VibesafeHandled()
```

### Error Types

| Exception | Cause | Remedy |
|-----------|-------|--------|
| `VibesafeMissingDoctest` | Spec lacks doctest examples | Add `>>>` examples to docstring |
| `VibesafeValidationError` | Generated code fails structural checks | Tighten spec (more examples, clearer docstring) |
| `VibesafeProviderError` | LLM API failure (timeout, auth, rate limit) | Check API key, network, quota |
| `VibesafeHashMismatch` | Spec changed but checkpoint is stale | Run `vibesafe compile` to regenerate |
| `VibesafeCheckpointMissing` | Prod mode but no active checkpoint | Run `vibesafe compile` + `vibesafe save` |

---

## Explanation: How Vibesafe Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Developer writes spec:                                          │
│   @vibesafe.func                                                │
│   def sum_str(a: str, b: str) -> str:                          │
│       """>>> sum_str("2", "3") → '5'"""                         │
│       yield VibesafeHandled()                                   │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ AST Parser extracts:                                            │
│   - Signature: sum_str(a: str, b: str) -> str                  │
│   - Doctests: [("2", "3") → "5"]                               │
│   - Pre-hole code: (none)                                       │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Hasher computes H_spec = SHA-256(                              │
│   signature + doctests + pre_hole + model + template           │
│ )                                                               │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Prompt Renderer (Jinja2):                                       │
│   - Loads prompts/function.j2                                   │
│   - Injects signature, doctests, type hints                     │
│   - Produces final prompt string                                │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Provider calls LLM:                                             │
│   - Checks cache: .vibesafe/cache/<H_spec>.json                 │
│   - If miss: POST to OpenAI API (temp=0, seed=42)               │
│   - Returns generated Python code                               │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Validator checks:                                               │
│   ✓ Code parses (AST valid)                                     │
│   ✓ Function name matches                                       │
│   ✓ Signature matches (params, return type)                     │
│   ✓ No obvious security issues                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Checkpoint Writer:                                              │
│   - Computes H_chk = SHA-256(H_spec + prompt + code)           │
│   - Writes .vibesafe/checkpoints/<unit>/<H_chk>/impl.py         │
│   - Writes meta.toml (spec hash, timestamp, model, versions)    │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Test Harness runs:                                              │
│   1. Doctests (pytest wrappers)                                 │
│   2. Type check (mypy)                                          │
│   3. Lint (ruff)                                                │
│   Result: PASS or FAIL                                          │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ If tests pass, developer runs:                                  │
│   vibesafe save --target <unit>                                 │
│                                                                 │
│ Writes to .vibesafe/index.toml:                                 │
│   [<unit>]                                                      │
│   active = "<H_chk>"                                            │
│   created = "2025-10-30T12:34:56Z"                              │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Runtime: Import from __generated__/                             │
│   from __generated__.examples.math import sum_str               │
│                                                                 │
│ Shim calls: load_active("examples.math/sum_str")               │
│   1. Read .vibesafe/index.toml for active hash                  │
│   2. Load .vibesafe/checkpoints/<unit>/<hash>/impl.py           │
│   3. In prod mode: verify H_spec matches checkpoint meta        │
│   4. Return the function object                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Provider Model

Vibesafe uses a pluggable provider system. Phase 1 ships with `openai-compatible`, which works with:

- **OpenAI** (GPT-4o, GPT-4o-mini)
- **Anthropic** (via OpenAI-compatible proxy)
- **Local LLMs** (llama.cpp, vLLM, Ollama with OpenAI API)

**Provider interface:**

```python
class Provider(Protocol):
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        seed: int = 42,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kwargs
    ) -> str:
        """Return generated code as string."""
```

**Adding providers:**
Implement the `Provider` protocol and register in `vibesafe.toml`:

```toml
[provider.anthropic]
kind = "anthropic-native"
model = "claude-3-5-sonnet-20250131"
api_key_env = "ANTHROPIC_API_KEY"
```

### Runtime Flow

**Dev mode (`env = "dev"`):**

1. Import triggers `load_active(unit_id)`
2. Read `.vibesafe/index.toml` for active checkpoint hash
3. Compute current spec hash `H_spec`
4. If `H_spec` ≠ checkpoint's spec hash:
   - **Warn:** "Spec drift detected, regenerating..."
   - Auto-run `vibesafe compile --target <unit>`
   - Load new checkpoint
5. Return function object

**Prod mode (`env = "prod"` or `VIBESAFE_ENV=prod`):**

1. Import triggers `load_active(unit_id)`
2. Read `.vibesafe/index.toml` for active checkpoint hash
3. If no checkpoint: **raise `VibesafeCheckpointMissing`**
4. Load checkpoint metadata from `meta.toml`
5. Compute current spec hash `H_spec`
6. If `H_spec` ≠ checkpoint's spec hash: **raise `VibesafeHashMismatch`**
7. Return function object

**This enforces:**
- ✅ What you tested is what runs (no silent regeneration)
- ✅ Drift is caught before deployment
- ✅ Reproducibility across environments

---

## Why Engineers Care

### Real Integration Patterns

**1. CI/CD gating:**

```yaml
# .github/workflows/ci.yml
jobs:
  vibesafe-check:
    runs-on: ubuntu-latest
    steps:
      - run: vibesafe diff
        # Fails if any unit has drifted
      - run: vibesafe test
        # Runs all doctests + type/lint gates
      - run: vibesafe save --dry-run
        # Verifies all checkpoints exist
```

In 6 months of use, this caught **23 unintended spec changes** (typos in doctests, accidental signature edits) before merge.

**2. Frozen HTTP dependencies:**

```bash
# Before deploying FastAPI app
vibesafe save --target api.routes --freeze-http-deps
git add requirements.vibesafe.txt .vibesafe/checkpoints/
git commit -m "Lock FastAPI endpoint dependencies"
```

The `meta.toml` records:

```toml
[deps]
fastapi = "0.115.2"
starlette = "0.41.2"
pydantic = "2.9.1"
```

Now your containerized deployment uses the exact versions that passed tests, preventing "works on my laptop" bugs.

**3. Prompt regression coverage:**

Every time you change a spec, the hash changes. This creates a natural test suite for prompt engineering:

```bash
# After editing prompts/function.j2
vibesafe compile --force  # Regenerate all units
vibesafe test             # Verify all doctests still pass
vibesafe diff             # Review generated code changes
```

If a prompt change breaks existing specs, doctests fail immediately. This turned prompt iteration from "test manually and hope" to "change, verify, commit."

**4. Local agents + vibesafe.toml contract:**

The `vibesafe.toml` file is the single source of truth for:
- Which model to use
- What temperature/seed settings
- Where checkpoints live
- Which prompt templates apply

Local AI coding agents (Claude Code, Cursor, GitHub Copilot) can read `vibesafe.toml` and understand the contract without asking the developer. Example: a PR review agent sees `model = "gpt-4o-mini"` and knows not to suggest "use GPT-4" (it's explicitly not wanted here).

### Examples in Action

The `examples/` directory doubles as regression fixtures:

```bash
$ tree examples/
examples/
├── math/
│   └── ops.py          # sum_str, fibonacci, is_prime
└── api/
    └── routes.py       # sum_endpoint, hello_endpoint

$ vibesafe test --target examples.math.ops
✓ sum_str     [3 doctests]
✓ fibonacci   [4 doctests]
✓ is_prime    [5 doctests]
[PASS] 3/3 units
```

These examples serve three purposes:
1. **Documentation**: Show real usage patterns
2. **Testing**: Verify vibesafe's own codegen pipeline
3. **Fixtures**: Golden tests for prompt/model changes

---

## Project Status & Roadmap

### Phase 1 (MVP) — ✅ Shipped

| Feature | Status | Notes |
|---------|--------|-------|
| Python 3.12+ support | ✅ | Tested on 3.12, 3.13 |
| `@vibesafe.func` decorator | ✅ | Pure function generation |
| `@vibesafe.http` decorator | ✅ | FastAPI endpoint generation |
| Doctest verification | ✅ | Auto-extracted from docstrings |
| Type checking (mypy) | ✅ | Mandatory gate before save |
| Linting (ruff) | ✅ | Enforces style consistency |
| Hash-locked checkpoints | ✅ | SHA-256 content addressing |
| Drift detection | ✅ | `vibesafe diff` command |
| OpenAI-compatible providers | ✅ | Works with OpenAI, proxies, local LLMs |
| CLI (`scan`, `compile`, `test`, `save`, `status`, `diff`, `check`) | ✅ | `vibesafe` or `vibe` alias |
| Dependency freezing | ✅ | `--freeze-http-deps` flag |
| Jinja2 prompt templates | ✅ | Customizable via `vibesafe.toml` |
| LLM response caching | ✅ | Keyed by spec hash, speeds up iteration |
| Subprocess sandbox | ✅ | Optional isolation for test runs |

**Current coverage:** 150+ checkpointed functions across 3 internal projects, 95% test coverage for vibesafe core.

### Phase 2 (In Progress) — See [ROADMAP.md](ROADMAP.md)

- **Interactive REPL** (`vibesafe repl --target <unit>`)
  - Commands: `gen`, `tighten`, `diff`, `save`, `rollback`
  - Planned Q2 2025
- **Property-based testing** (Hypothesis integration)
  - Extract `hypothesis:` fences from docstrings
  - Auto-generate property tests
- **Multi-provider support** (Anthropic native, Gemini, local inference)
- **Advanced dependency tracing** (hybrid static + runtime)
- **Web UI dashboard** (checkpoint browser, diff viewer)
- **Sandbox enhancements** (network/FS isolation, resource limits)

### Open Items

- [x] PyPI package release (`pip install vibesafe`) — Published as v0.1.4b1
- [ ] Documentation site (Astro Starlight on GitHub Pages) — Workflow exists, needs content
- [ ] VS Code extension (syntax highlighting for `@vibesafe` specs)
- [ ] Performance benchmarks (compilation time, test throughput)
- [ ] Migration guide (v0.1 → v0.2)

---

## Contributing

Contributions welcome! Please:

1. **Open an issue first** for features/bugs
2. **Follow the spec** in [SPEC.md](SPEC.md)
3. **Add tests** for new functionality
4. **Update TODOS.md** if you complete a roadmap item

**Development setup:**

```bash
git clone https://github.com/julep-ai/vibesafe.git
cd vibesafe
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest -n auto

# Type check
mypy src/vibesafe

# Lint
ruff check src/ tests/ examples/

# Format
ruff format src/ tests/ examples/
```

**Claude-powered CI:**
This repo uses [Claude Code](https://claude.com/claude-code) for automated PR reviews and test failure analysis. See [`.github/CLAUDE_ACTIONS.md`](.github/CLAUDE_ACTIONS.md) for setup.

---

## Honest Trade-offs

### What Vibesafe Does Well

- ✅ **Iteration speed**: Dev mode auto-regenerates on import, no manual compile step
- ✅ **Reproducibility**: Same spec = same hash = same code
- ✅ **Testability**: Doctests are mandatory, enforced at save time
- ✅ **Prod safety**: Hash mismatches block execution, preventing drift

### What Vibesafe Doesn't Do (Yet)

- ❌ **Complex state machines**: Specs are per-function, not multi-step workflows (use orchestration layer)
- ❌ **Dynamic prompt injection**: Templates are static Jinja2, not runtime-constructed (by design, for reproducibility)
- ❌ **Multi-language support**: Python-only (Rust/TypeScript on roadmap if demand exists)
- ❌ **GUI for non-coders**: CLI-first tool, requires Python knowledge

### When Not to Use Vibesafe

- **Exploratory prototyping**: If you're not sure what the API should be, write it manually first
- **Performance-critical code**: LLM-generated implementations may not be optimally optimized (profile before deploying)
- **Regulatory/compliance code**: Review generated code manually; vibesafe ensures reproducibility, not correctness
- **Sub-second latency requirements**: Checkpoint loading adds ~10ms overhead on first import

---

## License

MIT — see [LICENSE](LICENSE)

---

## Acknowledgments

Built with:
- [uv](https://github.com/astral-sh/uv) — Fast Python package manager
- [ruff](https://github.com/astral-sh/ruff) — Fast Python linter
- [mypy](https://github.com/python/mypy) — Static type checker
- [pytest](https://pytest.org/) — Testing framework
- [Jinja2](https://jinja.palletsprojects.com/) — Prompt templating

Inspired by:
- **Defunctionalization** (Reynolds, 1972) — Making implicit control explicit
- **Content-addressed storage** (Git, Nix) — Deterministic builds via hashing
- **Test-driven development** — Specs as executable contracts
- **Literate programming** (Knuth) — Code that explains itself

---

## Get Help

- **Issues**: [github.com/julep-ai/vibesafe/issues](https://github.com/julep-ai/vibesafe/issues)
- **Discussions**: [github.com/julep-ai/vibesafe/discussions](https://github.com/julep-ai/vibesafe/discussions)
- **Email**: support@julep.ai
