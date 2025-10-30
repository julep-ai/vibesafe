# Repository Guidelines

## Project Structure & Module Organization
The Python package lives in `src/vibesafe`, with CLI entrypoints in `cli.py`, orchestration code in `core.py` and `runtime.py`, provider adapters in `providers.py`, and configuration helpers in `config.py`. Tests mirror this layout inside `tests/` using `test_<module>.py` modules. Prompt templates for LLM calls live in `prompts/`, while `examples/` hosts reference specs that double as regression fixtures. Repository-level defaults and provider wiring are declared in `vibesafe.toml`; treat it as the contract for local agents and CI.

## Build, Test, and Development Commands
Spin up a local env with `uv venv && source .venv/bin/activate`, then install tooling via `uv pip install -e ".[dev]"`. Use the CLI to stay in sync with specs: `vibesafe scan` inventories targets, `vibesafe compile --target module.path/id` generates implementations, `vibesafe status` reports coverage vs. checkpoints, and `vibesafe diff [--target unit]` highlights drift. Run `vibesafe test` or `python -m pytest` for verification; CI invokes `pytest -v --cov=src/vibesafe`. Need a dependency snapshot before promoting HTTP endpoints? run `vibesafe save --target unit --freeze-http-deps` (or omit `--target` to freeze all) to write `requirements.vibesafe.txt` and annotate checkpoint metadata. Lint and format with `ruff check src tests examples` and `ruff format src tests examples`. Type-check with `mypy src/vibesafe` and `pyright src/vibesafe` before raising PRs.

## Coding Style & Naming Conventions
Code follows four-space indentation, 100-character lines, and aggressive type hinting. Modules and functions stay `snake_case`, classes use `CamelCase`, and constants remain `UPPER_SNAKE`. Keep specs small and deterministic; isolate side effects inside runtime/provider layers. Prefer dataclass-style DTOs for payloads and embrace rich exceptions (`VibesafeMissingDoctest`, `VibesafeValidationError`, etc.) over sentinel returns.

## Testing Guidelines
Author unit tests alongside code, mirroring the module names (`test_<module>.py`). Use `pytest.mark.unit`, `pytest.mark.integration`, and `pytest.mark.slow` thoughtfully so contributors can run `pytest -m "not slow"` locally. Target high coverage for touched files—the default config emits HTML and XML reports, so attach the HTML delta when investigating regressions. Provide representative prompts in `examples/` when adding new surfaces; they double as golden tests via `vibesafe test`.

## Commit & Pull Request Guidelines
Commits favor descriptive sentence-case summaries (e.g., `Rebrand library from defless to vibesafe`) and should bundle logical units only. Rebase before opening PRs, link relevant issues, and include a short checklist covering CLI, lint, type-check, and test runs. PR descriptions should capture the affected modules, user impact, and any follow-up work; attach screenshots or terminal snippets when altering CLI UX.

## Security & Configuration Tips
Never commit API keys; rely on `OPENAI_API_KEY` and other secrets injected at runtime. Update `vibesafe.toml` only when schema changes are required, and call out migration steps in your PR so downstream agents can rotate credentials safely.
