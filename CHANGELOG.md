# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Renamed `VibesafeHandled` to `VibeCoded` for clearer semantics
- **BREAKING**: Changed usage pattern from `yield VibesafeHandled()` to `raise VibeCoded()`
- **BREAKING**: Simplified decorator API: `@vibesafe.func` → `@vibesafe`, `@vibesafe.http` → `@vibesafe(kind="http")`
- **BREAKING**: Added new CLI command template support: `@vibesafe(kind="cli")`
- **BREAKING**: Deprecated the `__generated__/` shim system in favor of direct module-level imports
- **BREAKING**: Removed automatic shim generation from `vibesafe compile` command
- **BREAKING**: Removed `--write-shims` CLI flag
- Moved template files from `prompts/` to `vibesafe/templates/` for better package organization
- Updated import patterns from `from app.__generated__.math.ops import sum_str` to `from app.math.ops import sum_str`

### Migration Guide
For users upgrading from v0.1:
1. Replace all `VibesafeHandled` imports with `VibeCoded`
2. Change `yield VibesafeHandled()` to `raise VibeCoded()`
3. Update decorators: `@vibesafe.func` → `@vibesafe`
4. Update decorators: `@vibesafe.http` → `@vibesafe(kind="http")`
5. Update imports: remove `__generated__` from import paths
6. Update `vibesafe.toml`: change template paths from `prompts/` to `vibesafe/templates/`

### Documentation
- Updated README.md to reflect new API patterns and deprecation notices
- Overhauled API reference documentation with comprehensive function documentation
- Added migration guide for transitioning from shim-based to direct imports
- Updated CLI reference with deprecation warnings for legacy flags
- Removed shim references from architecture and core concepts documentation

### Development
- All tests pass (195/195) with no functional regressions from documentation changes
- Maintained backward compatibility for existing compiled checkpoints
- Updated examples and specifications to use new import patterns

## [0.1.4b1] - 2025-01-20

### Added
- Initial beta release with core functionality
- Function and HTTP endpoint specification via docstrings
- LLM-powered code generation with checkpointing
- CLI tools for scanning, compiling, and testing specs
- FastAPI integration for HTTP endpoints
- MCP (Model Context Protocol) server support
- Comprehensive test suite with 195 tests

### Changed
- Migrated from "vibesafe" to "vibesafe" branding

### Technical Details
- Python 3.12+ requirement
- OpenAI-compatible provider support
- Jinja2 templating for code generation
- Rich CLI interface with progress indicators
- Hypothesis integration for property-based testing