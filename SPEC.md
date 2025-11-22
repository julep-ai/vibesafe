# Vibesafe — Extended Developer Guide (v0.1)

> **Tagline:** *Human intent, verified.*
> **Scope:** Python 3.12+, targets pure/utility functions and FastAPI HTTP endpoints.
> **Philosophy:** You write small, typed, example-driven specs; Vibesafe generates code, tests it, and checkpoints the result under a cryptographic hash. Dev is fast and iterative; prod is deterministic and safe.

---

## 0) Quick start (for users)

```bash
pip install vibesafe  # (name TBD on PyPI)
export OPENAI_API_KEY=...      # Provider API key (OpenAI-compatible)

vibe scan
vibe compile
vibe test
vibe save
```

`app/math/ops.py`

```python
from vibesafe import vibesafe, VibeCoded

@vibesafe
def sum_str(a: str, b: str) -> str:
    """
    Add two ints represented as strings.

    >>> sum_str("2", "3")
    '5'
    """
    a, b = int(a), int(b)
    raise VibeCoded()  # the "hole" Vibesafe fills
```

Import generated implementation (post-compile/save):

```python
from app.math.ops import sum_str
```

---

# Part I — Concepts & Architecture

## 1) Mental model

* **Spec as code**: A normal Python function with **strict types** + **doctest examples**, whose body contains a **hole** (`yield/return VibeHandled()`).
* **Generation**: Vibesafe compiles the spec into an implementation via an LLM (OpenAI-compatible), then runs tests.
* **Checkpointing**: Passing code is stored under a **hash**; the decorator transparently loads from active checkpoints.
* **Modes**:

  * **dev**: regenerate on the fly; hash mismatch → warn + auto-regenerate.
  * **prod**: generation disabled; only checkpointed code runs; hash mismatch → hard error.

## 2) Directory layout

```
your_pkg/
  app/
    math/
      ops.py                      # specs
  .vibesafe/
  checkpoints/
    app.math.ops/sum_str/
      2d46.../
        impl.py
        meta.toml
  index.toml                      # unit -> active sha
  cache/                          # provider cache (gitignored)
vibesafe.toml                     # project config
tests/
  vibesafe/                        # doctest + property tests emitted here
```

> **Unit ID** = `<module.path>/<object_name>`, e.g. `app.math.ops/sum_str`.

## 3) Components

* **Decorators** (`@vibesafe` with optional `kind` parameter) mark specs and provide per-unit config.
* **Codegen** renders a **Jinja** prompt, calls provider, validates code, writes checkpoint.
* **Hasher** computes `H_spec` and `H_chk` (see §10).
* **CLI** (`vibe`) runs `scan`, `compile`, `test`, `save`, etc.
* **Provider** is pluggable; first backend is **OpenAI-compatible**.
* **Test harness** runs doctests, optional Hypothesis props, type-check, and lint.

---

# Part II — User-Facing API

## 4) Decorators & sentinel

```python
from typing import Any
from vibesafe import vibesafe, VibeHandled

@vibesafe.func(
    prompt: str | None = None,          # override template if desired
    model: str | None = None,           # override per-unit
    template_id: str | None = None,     # select alt template
)
def your_func(...) -> ...:
    """Docstring must include at least 1 doctest."""
    # your pre/post “glue” is allowed
    yield VibeHandled()  # or: return VibeHandled()
```

FastAPI endpoint:

```python
from fastapi import APIRouter
from vibesafe import vibesafe, VibeHandled

router = APIRouter()

@vibesafe.http(
    method="POST",
    path="/sum",
    tags=["calc"],
    prompt=None,
    model=None,
)
async def sum_endpoint(a: int, b: int) -> dict[str, int]:
    """
    Returns {"sum": a+b}

    >>> import anyio
    >>> anyio.run(lambda: sum_endpoint(2, 3))
    {'sum': 5}
    """
    return VibeHandled()
```

**Rules**

* Python (or Pydantic) **types required** for params and return.
* Doctest **examples required** (at least one) for MVP; dev mode warns if underspecified.
* Body code **before** the hole is allowed (e.g., input parsing, preconditions). It’s hashed.

## 5) Config — `vibesafe.toml`

```toml
[project]
python = ">=3.12"
env = "dev"                      # dev | prod

[provider.default]
kind = "openai-compatible"
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
model = "gpt-4o-mini"
seed = 42
max_tokens = 4096

[paths]
checkpoints = ".vibesafe/checkpoints"
cache = ".vibesafe/cache"

[prompts]
function = "vibesafe/templates/function.j2"
http = "vibesafe/templates/http_endpoint.j2"
cli = "vibesafe/templates/cli_command.j2"
```

Per-unit overrides (decorator kwargs) take precedence over file config.

## 6) CLI

```
vibe scan            # list units and status
vibe compile [--target UNIT|MODULE] [--force]
vibe test    [--target UNIT|MODULE] [--all]
vibe save    [--target UNIT|MODULE] [--freeze-http-deps]
vibe diff    [--target UNIT]
vibe status
vibe repl    [--target UNIT]
```

> **Implementation note:** The CLI is exposed as both `vibe` (alias) and `vibesafe`. You can run either `vibe scan` or `vibesafe scan`; both map to the same entrypoint in this repository.

* `scan`: finds specs, reports doctest count, drift.
* `compile`: generates code + tests; writes checkpoint.
* `test`: runs doctests (+ props if present), type-check (pyright/mypy), lint (ruff). `--all` can delegate to your full test suite.
* `save`: activates a checkpoint (updates `.vibesafe/index.toml`). `--freeze-http-deps` writes `requirements.vibesafe.txt` and records runtime versions in `meta.toml`.
* `diff`: shows prompt/code diffs vs active checkpoint.
* `repl`: interactive iteration loop (regenerate, tighten, test, split, save).

**Env var**: `VIBESAFE_ENV=dev|prod` (overrides `vibesafe.toml`).

---

# Part II.5 — Phase 1 Implementation Status

## Phase 1 Implementation (COMPLETED)

### Decorator System

**Implemented as:** Module-level registry with decorator functions

```python
# Global registry (module-level)
_registry: dict[str, dict[str, Any]] = {}

def get_registry() -> dict[str, dict[str, Any]]:
    """Access global registry"""
    return _registry

def get_unit(unit_id: str) -> dict[str, Any] | None:
    """Retrieve specific unit by ID"""
    return _registry.get(unit_id)

def resolve_template_id(unit_id: str) -> str:
    """Resolve template ID for a unit"""
    unit = get_unit(unit_id)
    return unit.get("template_id", "function") if unit else "function"
```

**Decision:** Chose module-level approach over class-based `VibesafeDecorator` for simplicity and to avoid singleton patterns. The registry is populated at import time when decorators are applied.

### Import Shims (DEPRECATED v0.2)

~~`__generated__/` directory with import shims~~

**Status:** Deprecated. Direct runtime loading is now preferred.

**Reason:** Shims added complexity without clear benefit. Runtime loading via decorator or explicit `load_active()` is simpler and more direct.

**Migration:** Change imports from:
```python
from app.__generated__.math.ops import sum_str  # OLD
```
to:
```python
from app.math.ops import sum_str  # NEW
```

### CLI Commands

#### `vibesafe scan`
- Lists all registered units
- ~~`--write-shims` flag (deprecated v0.2)~~
- Shows checkpoint status and doctest coverage

#### `vibesafe compile`
- ~~No longer writes shims automatically~~
- Generates code and writes checkpoints
- `--force` flag to override existing checkpoints

### Template Resolution

**Added:** `resolve_template_id()` helper function for programmatic template resolution, complementing the existing decorator-based template selection.

---

# Part III — Implementation Blueprint

> This is the “how to build it” section for the core maintainers.

## 7) Package structure *(Aspirational)*

> **Status:** The following module layout is a Phase 1 refactor plan and does not yet match the live repository. Treat it as a roadmap rather than current state.

```
vibesafe/
  __init__.py                 # exports: vibesafe, VibeHandled
  api/
    decorators.py             # @vibesafe.func, @vibesafe.http
    sentinel.py               # class VibeHandled
  core/
    spec.py                   # AST extraction, doctest parsing
    hashing.py                # H_spec, H_chk
    tracer.py                 # static dependency tracer (Phase 1), hybrid (Phase 2)
    prompts.py                # Jinja loader, template registry
    codegen.py                # render prompt, provider call, validate, write checkpoint
    validate.py               # AST/name/signature checks, sanity checks
  runtime/
    loader.py                 # load_active(unit_id)
    checkpoints.py            # index read/write, meta schema
  testkit/
    doctest_gen.py            # extract -> pytest wrappers
    props_gen.py              # optional Hypothesis support
    gates.py                  # ruff + type-check integration
  cli/
    main.py                   # click/typer entrypoint
    scan.py compile.py test.py save.py diff.py repl.py status.py
  providers/
    base.py                   # Provider protocol
    openai_compat.py          # default implementation
  conf/
    config.py                 # TOML loader, env merging
  mcp/
    server.py                 # mirrors CLI actions (Phase 1: read-only; Phase 2: full)
```

## 8) Data models

### 8.1 Unit identifier

```
unit_id = f"{module_path}/{object_name}"
# e.g., "app.math.ops/sum_str"
```

### 8.2 Index file — `.vibesafe/index.toml`

```toml
[app.math.ops/sum_str]
active = "2d46..."
created = "2025-10-29T09:43:12Z"
```

### 8.3 Checkpoint meta — `meta.toml`

```toml
spec_sha = "5a72..."
chk_sha  = "2d46..."
vibesafe_compat = "0.1"                # internal schema version if needed
vibesafe_version = "0.1.0"
provider = "openai-compatible:gpt-4o-mini"
prompt_template = "function.j2"
python = "3.12.3"
env = "dev"

[hash_inputs]
signature = "def sum_str(a: str, b: str) -> str"
docstring_sha = "..."
pre_hole_sha = "..."
template_id = "function"
model = "gpt-4o-mini"
seed = 42
dependency_digest = "..."

[deps]                                   # filled when --freeze-http-deps
fastapi = "0.115.2"
starlette = "0.41.2"
pydantic = "2.9.1"
```

## 9) Prompting & templates

* **Jinja** templates live at `vibesafe/templates/function.j2`, `vibesafe/templates/http_endpoint.j2`, `vibesafe/templates/cli_command.j2`.
* Context available to templates:

  ```python
  {
    "unit_id": ...,
    "signature": ...,
    "return_annotation": ...,
    "params": [...],
    "docstring": ...,
    "doctests": [...],                 # normalized examples
    "pre_hole_src": ...,
    "imports": [...],                  # inferred required imports
    "constraints": {...},              # types, error modes
    "style": {"ruff": "...", "typing": "..."},
  }
  ```
* **Determinism:** `temperature=0`, `seed=42`, provider-level caching keyed by `H_spec`.

## 10) Hashing & dependency tracing

### 10.1 `H_spec` (spec hash)

Compute SHA-256 of the concatenation (with clear separators):

1. **Signature**: name + params (names, annotations, defaults) + return type.
2. **Docstring**: normalized text (strip indent, standardize newlines).
3. **Pre-hole body**: source slice up to first `VibeHandled`.
4. **Version & params**: vibesafe version, template id, provider model, temperature, seed, max tokens.
5. **Dependency digest** *(static)*: for each referenced global/import **used in the pre-hole slice**:

   * Resolve to module/file.
   * Include `(abs_path, file_sha)` or a stable path+content hash.

> Phase 2: add optional runtime trace (hybrid) to capture dynamic imports.

### 10.2 `H_chk` (checkpoint hash)

```
H_chk = sha256( H_spec || prompt_render_sha || generated_code_sha )
```

**Enforcement**

* **dev**: mismatch ⇒ warn + try regenerate; continue if successful.
* **prod**: mismatch ⇒ raise `VibesafeHashMismatch`.

## 11) Generation pipeline

1. **Parse spec** with `ast`:

   * locate decorated def
   * extract signature, docstring, pre-hole slice
   * validate strict typing
2. **Collect doctests**:

   * parse docstring, extract `>>>` blocks
   * require ≥ 1 example (dev warns; save blocks)
3. **Render prompt** (Jinja) with context
4. **Provider call** (OpenAI-compatible):

   * enforce token + latency limits
   * cache by `H_spec`
5. **Validate impl**:

   * parse to AST
   * check same name/signature
   * ensure imports compile
   * (optional) basic safety scan
 6. **Write checkpoint**:

    * `.vibesafe/checkpoints/<unit>/<H_chk>/impl.py`
    * `meta.toml`
 7. **Run tests**:

   * build pytest doctest wrappers in `tests/vibesafe/`
   * run pyright/mypy + ruff
9. **Activate**:

   * on `vibe save`, set `.vibesafe/index.toml[unit].active = H_chk`

## 12) Tests & verification

### 12.1 Doctests → pytest conversion

* Generate a file per unit: `tests/vibesafe/test_app_math_ops_sum_str.py`.
* Harness can run these in isolation (`vibe test`) or with the full suite (`--all`).

### 12.2 Property-based (Phase 2)

* If the docstring contains a `hypothesis:` fenced block, extract verbatim Python and include it in the test file.

### 12.3 Gates

* **Ruff** (style) and **pyright/mypy** (type-check) on the generated impl.
* All gates must pass to allow `save`.

## 13) FastAPI integration

* The `@vibesafe.http` decorator yields an async callable matching the annotated signature.
* Use the helper to validate at startup and mount health probes (Phase 2):

```python
from vibesafe.fastapi import mount
mount(router)  # registers /_vibesafe/health and /_vibesafe/version
```

* **Dependency pins**: leave unpinned in dev; `vibe save --freeze-http-deps` writes `requirements.vibesafe.txt` and records versions in `meta.toml`.

## 14) Interactive loop (Phase 2)

`vibe repl --target app.math.ops/sum_str`

Features:

* **show** summary (types, examples, dependency digest)
* **gen** regenerate with optional hint
* **tighten** propose/insert additional doctests
* **test** re-run gates
* **diff** prompt/code vs active checkpoint
* **split** promote inner helpers into new units (writes new spec stubs + shims)
* **save** activate checkpoint
* **rollback** pick previous SHA

## 15) Error model

* `VibesafeMissingDoctest`: spec lacks doctest coverage.
* `VibesafeTypeError`: missing/loose type annotations (future work; currently advisory).
* `VibesafeValidationError`: generated code fails structural checks.
* `VibesafeProviderError`: upstream API failure from the LLM provider.
* `VibesafeHashMismatch`: spec/impl mismatch detected in prod.
* `VibesafeCheckpointMissing`: prod mode but no active checkpoint.

**UX pattern**: catch → show actionable remediation (e.g., “add at least one doctest and rerun `vibe compile`”).

---

# Part IV — Usage Patterns & Examples

## 16) Patterns

### 16.1 Glue before the hole

Use the pre-hole slice for **safe, human-reviewed** logic:

```python
@vibesafe.func
def sanitize_and_parse(payload: str) -> dict[str, int]:
    """
    >>> sanitize_and_parse('{"a": 2, "b": 3}')
    {'a': 2, 'b': 3}
    """
    payload = payload.strip()
    yield VibeHandled()
```

This ensures parsing rules are part of the hash.

### 16.2 HTTP with Pydantic

```python
from pydantic import BaseModel

class SumIn(BaseModel):
    a: int
    b: int

class SumOut(BaseModel):
    sum: int

@vibesafe.http(method="POST", path="/sum")
async def sum_endpoint(inp: SumIn) -> SumOut:
    """
    >>> import anyio
    >>> out = anyio.run(lambda: sum_endpoint(SumIn(a=2,b=3)))
    >>> out.sum
    5
    """
    return VibeHandled()
```

### 16.3 Regeneration on dev call

In dev mode, simply calling a spec function will trigger generation if missing or drifted.

---

# Part V — CI/CD, Tooling & Ops

## 17) Git hygiene

**.gitignore**

```
.vibesafe/cache/
```

**Commit these**

* `.vibesafe/index.toml` (diff-friendly)
* `.vibesafe/checkpoints/**/meta.toml`
* Optionally: **include** `impl.py` files for fully offline prod deploys (recommended). If your
  production artifacts need to run without access to checkpoint storage, copy the
  checkpoint directory (`.vibesafe/checkpoints/.../impl.py`) into your release bundle.
  Otherwise leave the generated code out of version control and rely on `vibesafe save`
  to refresh checkpoints during deployment.

## 18) CI

* `vibe test` must pass.
* `vibe save --dry-run` to verify all units have active checkpoints.
* Optionally: `vibe check` (Phase 2) → ensures no drift, all hashes match, active checkpoints exist.

## 19) Deployment

* Set `VIBESAFE_ENV=prod`.
* Do **not** ship provider credentials (prod doesn’t generate).
* Ensure `.vibesafe/checkpoints` are present in the artifact.

---

# Part VI — Extensibility

## 20) Provider interface

```python
class Provider(Protocol):
    def complete(
        self,
        *,
        prompt: str,
        system: str | None = None,
        seed: int = 42,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kw
    ) -> str: ...
```

* First backend: `OpenAICompatibleProvider`.
* Future: Anthropic, local inference servers, etc.

## 21) Template overrides

* Put custom Jinja under `vibesafe/templates/` (or point `prompts.*` to your own path).
* Set paths in `vibesafe.toml` or pass `prompt=` to a decorator for one-off overrides.

## 22) Sandbox (optional, Phase 2)

Opt-in subprocess execution for generated code during tests:

```toml
[sandbox]
enabled = true
timeout_s = 10
memory_mb = 256
```

---

# Part VII — Reference

## 23) Common commands

* `vibe scan`
* `vibe compile --target app.math.ops`
* `vibe test --target app.math.ops/sum_str`
* `vibe save --freeze-http-deps`
* `vibe diff --target app.math.ops/sum_str`
* `VIBESAFE_ENV=prod python -m your_pkg.app`

## 24) FAQ

* **Q:** Can I edit generated files?
  **A:** Prefer not. Edit the spec or prompt and regenerate. In emergencies, edits won’t be preserved across regenerations unless you lock that checkpoint and never rotate it.

* **Q:** Do I have to use Pydantic?
  **A:** No—stdlib types are fine. Pydantic models are great for HTTP schemas.

* **Q:** Can generated code access the network/DB?
  **A:** Yes (v0.1). If you need isolation, enable sandbox in Phase 2.

* **Q:** How do I pin FastAPI deps?
  **A:** `vibe save --freeze-http-deps` writes `requirements.vibesafe.txt` and records versions in `meta.toml`.

---

# Appendix A — Minimal scaffolding plan (implementation order)

1. `api.decorators`, `api.sentinel`
2. `core.spec`, `core.prompts`, `providers.openai_compat`
3. `core.codegen`, `runtime.checkpoints`, `runtime.loader`
4. `testkit.doctest_gen`, `testkit.gates`
5. `cli.*` (`scan`, `compile`, `test`, `save`)
6. Hashing + tracer MVP
7. Docs + examples

Then Phase 2:

* `repl`, `diff`, `status`, props, hybrid tracer, sandbox, MCP full bridge, pinning.
