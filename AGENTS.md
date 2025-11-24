# Repository Guidelines

## Project Structure & Module Organization
The Python package lives in `src/vibesafe`, with CLI entrypoints in `cli.py`, orchestration code in `core.py` and `runtime.py`, provider adapters in `providers.py`, and configuration helpers in `config.py`. Tests mirror this layout inside `tests/` using `test_<module>.py` modules. Prompt templates for LLM calls live in the top-level `prompts/` directory (configurable via `[prompts]` in `vibesafe.toml`) with support for function, HTTP endpoint, and CLI command generation, while `examples/` hosts reference specs that double as regression fixtures. Packaged fallbacks remain under `src/vibesafe/templates/` so installs still work if `prompts/` isn’t present. Repository-level defaults—including the `.vibesafe/` paths for checkpoints/cache/index and the default `gpt-5-mini` provider wiring—are declared in `vibesafe.toml`; treat it as the contract for local agents and CI.

## Build, Test, and Development Commands
Spin up a local env with `uv venv && source .venv/bin/activate`, then install tooling via `uv pip install -e ".[dev]"`. Use the CLI to stay in sync with specs: `vibesafe scan` inventories targets, `vibesafe compile --target module.path/id` generates implementations using the configured prompts under `vibesafe/templates/` and provider (default OpenAI-compatible `gpt-5-mini` with `OPENAI_API_KEY`), `vibesafe status` reports coverage vs. checkpoints, and `vibesafe diff [--target unit]` highlights drift. Run `vibesafe test` or `python -m pytest` for verification; CI invokes `pytest -v --cov=src/vibesafe`. Need a dependency snapshot before promoting HTTP endpoints? run `vibesafe save --target unit --freeze-http-deps` (or omit `--target` to freeze all) to write `requirements.vibesafe.txt` and annotate checkpoint metadata. Lint and format with `ruff check src tests examples` and `ruff format src tests examples`. Type-check with `mypy src/vibesafe` and `pyright src/vibesafe` before raising PRs.

## Coding Style & Naming Conventions
Code follows four-space indentation, 100-character lines, and aggressive type hinting. Modules and functions stay `snake_case`, classes use `CamelCase`, and constants remain `UPPER_SNAKE`. Keep specs small and deterministic; isolate side effects inside runtime/provider layers. Prefer dataclass-style DTOs for payloads and embrace rich exceptions (`VibesafeMissingDoctest`, `VibesafeValidationError`, etc.) over sentinel returns.

## Testing Guidelines
Author unit tests alongside code, mirroring the module names (`test_<module>.py`). Use `pytest.mark.unit`, `pytest.mark.integration`, and `pytest.mark.slow` thoughtfully so contributors can run `pytest -m "not slow"` locally. Target high coverage for touched files—the default config emits HTML and XML reports, so attach the HTML delta when investigating regressions. Provide representative prompts in `examples/` when adding new surfaces; they double as golden tests via `vibesafe test`.

## Commit & Pull Request Guidelines
Commits favor descriptive sentence-case summaries (e.g., `Rebrand library from vibesafe to vibesafe`) and should bundle logical units only. Rebase before opening PRs, link relevant issues, and include a short checklist covering CLI, lint, type-check, and test runs. PR descriptions should capture the affected modules, user impact, and any follow-up work; attach screenshots or terminal snippets when altering CLI UX.

## Claude Code Integration
This repository includes a full Claude Code plugin in `.claude-plugin/` with:
- **MCP Server**: Model Context Protocol server for seamless vibesafe operations
- **Slash Commands**: `/vibe`, `/vibe-init`, `/vibe-mode`, `/vibe-status` for quick access
- **Skills**: AI-assisted development workflows for vibesafe-specific tasks
- **GitHub Actions**: Automated PR reviews and test failure analysis using Claude Code

### Plugin Configuration
- Plugin manifest: `.claude-plugin/plugin.json`
- Marketplace config: `.claude-plugin/marketplace.json`
- Skills definition: `.claude-plugin/skills/vibesafe/SKILL.md`
- Commands: `.claude-plugin/commands/*.md`

### MCP Server Tools
- `scan` — List all registered units with metadata
- `compile` — Generate implementations (supports `target`, `force`)
- `test` — Run doctests/quality gates
- `save` — Activate checkpoints
- `status` — Report version, unit counts, environment

### Agent Guidelines
When building AI agents that interact with this repository:
1. Read `vibesafe.toml` to understand project configuration
2. Use MCP server for vibesafe operations when available
3. Follow v0.2 API patterns (VibeCoded exception, simplified decorators)
4. Check `.claude-plugin/skills/vibesafe/SKILL.md` for available capabilities
5. Respect the direct import system (no `__generated__` directory)

## Security & Configuration Tips
Never commit API keys; rely on `OPENAI_API_KEY` and other secrets injected at runtime. Update `vibesafe.toml` only when schema changes are required, and call out migration steps in your PR so downstream agents can rotate credentials safely.
