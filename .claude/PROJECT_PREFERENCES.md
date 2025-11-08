# Vibesafe Project Preferences

This document records key technical decisions and preferences for the Vibesafe project. It serves as a reference for AI assistants, contributors, and maintainers.

## Documentation Framework

**Decision:** Astro Starlight (NOT Docusaurus)

**Rationale:**
- **Performance**: Near-zero JavaScript, lightning-fast page loads
- **Accessibility**: WCAG 2.2 compliant out-of-the-box
- **Modern**: Built on Astro's island architecture
- **DX**: File-based routing, instant HMR, TypeScript support
- **GitHub Pages**: Excellent integration with our deployment workflow
- **Cost**: Free, no vendor lock-in

**Documentation Site:**
- URL: https://julep-ai.github.io/vibesafe/ (redirects to vibesafe.memory.store)
- Deployment: GitHub Actions workflow at `.github/workflows/deploy-docs.yml`
- Content: `docs/` directory (to be populated with Starlight setup)

**References:**
- Documentation planning: `README_PLAN.md`
- Framework guide: `.claude/skills/documentation-2025.md`
- Status: `README.md` - Open Items section

## Package Distribution

**PyPI Package:** Published as `vibesafe`
- Current version: v0.1.4b1
- Install: `pip install vibesafe` or `uv pip install vibesafe`
- PyPI publishing: Automated via `.github/workflows/pypi-publish.yml`

## Development Tools

**Build System:**
- Package manager: `uv` (recommended)
- Build backend: `uv_build`
- Python versions: 3.12+ (3.13 supported, 3.11 not tested)

**Code Quality:**
- Linter: `ruff`
- Type checkers: `mypy` and `pyright`
- Formatter: `ruff format`
- Testing: `pytest` with parallel execution (`pytest-xdist`)

## Architectural Preferences

**Checkpoint Storage:**
- Directory: `.vibesafe/checkpoints/`
- Hashing: SHA-256 content addressing
- Format: Per SPEC.md §10

**Prompts:**
- Template engine: Jinja2
- Default location: `prompts/`
- Customization: Via `vibesafe.toml` or decorator `template=` parameter

**Providers:**
- Primary: OpenAI-compatible API
- Configuration: `vibesafe.toml` under `[provider.*]`
- Phase 2: Anthropic native, Gemini, local inference

## Documentation Structure

Following Diátaxis framework:
1. **Getting Started**: Installation, first spec, quickstart
2. **Core Concepts**: Architecture, hashing, runtime modes
3. **How-To Guides**: Task-oriented recipes
4. **Reference**: CLI commands, config schema, exceptions
5. **Explanation**: Why it exists, design decisions, trade-offs

## Writing Style

**Tone:** Technical, honest, conversational (Hacker News style)
- Ground claims with concrete data/benchmarks
- Admit limitations and trade-offs
- Use second person ("you")
- Code-first examples
- Clear next steps on every page

**References:**
- Style guide: `.claude/skills/hackernews-writing.md`
- README approach: `README_PLAN.md`

## Phase Status (as of Nov 2025)

**Phase 1 (MVP):** ✅ All core features shipped
- Open items: Docs site content, VS Code extension, benchmarks, migration guide
- See: `README.md` - Project Status & Roadmap section

**Phase 2:** In planning
- See: `ROADMAP.md` for detailed backlog
- Key items: Interactive REPL, property testing, multi-provider support

## Maintenance

**Issue Tracking:** GitHub Issues
**Discussions:** GitHub Discussions
**Email:** support@julep.ai

**Version Convention:**
- v0.1.x: Phase 1 iterations
- v0.2.x: Phase 2 features
- Migration guide needed for v0.1 → v0.2

---

*Last updated: 2025-11-08*
*Maintainer: Julep AI team*
