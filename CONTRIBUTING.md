# Contributing to Vibesafe

Thanks for helping improve Vibesafe! These quick notes cover the essentials for getting your environment ready and landing a solid change.

## Environment Setup
- Install Python 3.12 (recommended via `asdf` or `pyenv`).
- Create an isolated environment: `uv venv && source .venv/bin/activate`.
- Install the project with dev tooling: `uv pip install -e ".[dev]"`.

## Workflow Checklist
- Run `vibesafe scan` to verify specs register, `vibesafe status` for an overview of active checkpoints, `vibesafe diff --target <unit>` to inspect drift, `vibesafe compile --target <unit>` to regenerate implementations, and `vibesafe test` to re-run doctest-backed and lint/type gates.
- Execute `pytest` (or `pytest -m "not slow"` for tight loops) before pushing.
- Need to freeze dependencies for an HTTP surface? Include `vibesafe save --target <unit> --freeze-http-deps` (or run without `--target` to freeze all) after tests pass.
- Lint and format with `ruff check src tests examples` and `ruff format src tests examples`.
- Type-check with `mypy src/vibesafe` and `pyright src/vibesafe`.

## Pull Requests
- Keep commits focused; prefer sentence-case summaries.
- In PR descriptions, note the impacted modules, verification commands run, and any follow-up tasks.
- Link related issues and attach CLI snippets or screenshots when tweaking UX.

That’s it—thanks again for contributing! Feel free to open a draft PR early if you’d like feedback. 
