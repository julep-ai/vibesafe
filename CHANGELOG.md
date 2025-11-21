# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Deprecated the `__generated__/` shim system in favor of direct module-level imports
- **BREAKING**: Removed automatic shim generation from `vibesafe compile` command
- **BREAKING**: Deprecated `--write-shims` CLI flag (will be removed in a future version)
- Updated import patterns from `from app.__generated__.math.ops import sum_str` to `from app.math.ops import sum_str`
- Enhanced module-level API with new functions:
  - `vibesafe.get_registry()` - Access the global unit registry
  - `vibesafe.get_unit(unit_id)` - Retrieve specific units by ID
  - `vibesafe.resolve_template_id(unit_id)` - Resolve template IDs for units

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
- Migrated from "defless" to "vibesafe" branding

### Technical Details
- Python 3.12+ requirement
- OpenAI-compatible provider support
- Jinja2 templating for code generation
- Rich CLI interface with progress indicators
- Hypothesis integration for property-based testing