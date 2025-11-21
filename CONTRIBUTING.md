# Contributing to Vibesafe

Thanks for helping improve Vibesafe! These quick notes cover the essentials for getting your environment ready and landing a solid change.

## Environment Setup
- Install Python 3.12 (recommended via `asdf` or `pyenv`).
- Create an isolated environment: `uv venv && source .venv/bin/activate`.
- Install the project with dev tooling: `uv pip install -e ".[dev]"`.
- Ensure your environment exports `OPENAI_API_KEY`; the default provider is OpenAI-compatible `gpt-5-mini` (see `vibesafe.toml`).

## Workflow Checklist
- The `vibesafe` command has a short alias `vibe` for convenience. Run `vibesafe scan` (or `vibe scan`) to verify specs register, `vibesafe status` for an overview of active checkpoints, `vibesafe diff --target <unit>` to inspect drift, `vibesafe compile --target <unit>` to regenerate implementations using the configured prompts under `prompts/`, and `vibesafe test` to re-run doctest-backed and lint/type gates.
- Execute `pytest` (or `pytest -m "not slow"` for tight loops) before pushing.
- Need to freeze dependencies for an HTTP surface? Include `vibesafe save --target <unit> --freeze-http-deps` (or run without `--target` to freeze all) after tests pass; this writes `requirements.vibesafe.txt` and updates checkpoint metadata.
- Lint and format with `ruff check src tests examples` and `ruff format src tests examples`.
- Type-check with `mypy src/vibesafe` and `pyright src/vibesafe`.

## API Patterns (v0.2+)

### Basic Function Spec
```python
from vibesafe import vibesafe, VibeCoded

@vibesafe
def greet(name: str) -> str:
    """
    >>> greet("World")
    'Hello, World!'
    """
    raise VibeCoded()
```

### HTTP Endpoint Spec
```python
@vibesafe(kind="http")
def get_user(user_id: str) -> dict:
    """
    >>> get_user("123")
    {'id': '123', 'name': 'Alice'}
    """
    raise VibeCoded()
```

### CLI Command Spec
```python
@vibesafe(kind="cli")
def process_file(input_path: str, output_path: str) -> None:
    """
    >>> process_file("input.txt", "output.txt")
    # Process file from input to output
    """
    raise VibeCoded()
```

## Deprecated Features
- `--write-shims` flag on `vibesafe scan` is deprecated as of v0.2. Direct imports are now preferred over generated shim files.

## Pull Requests
- Keep commits focused; prefer sentence-case summaries.
- In PR descriptions, note the impacted modules, verification commands run, and any follow-up tasks.
- Link related issues and attach CLI snippets or screenshots when tweaking UX.

That’s it—thanks again for contributing! Feel free to open a draft PR early if you’d like feedback. 
