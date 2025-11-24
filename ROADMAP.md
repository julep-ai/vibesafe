# Vibesafe Roadmap

## Phase 1 (MVP) — ✅ COMPLETED

| Feature | Status | Notes |
|---------|--------|-------|
| Core decorator API | ✅ | Implemented as module-level registry |
| `@vibesafe` | ✅ | Pure function generation |
| `@vibesafe(kind="http")` | ✅ | FastAPI endpoint generation |
| `@vibesafe(kind="cli")` | ✅ | CLI command generation |
| Import shims | ⚠️ DEPRECATED | Removed in v0.2, replaced with direct imports |
| Template resolution | ✅ | Added `resolve_template_id()` helper |
| CLI commands | ✅ | scan, compile, test, save, status, diff |
| Doctest harness generation | ✅ | Auto-generated under `tests/vibesafe/` |
| Hashing & dependency tracing | ✅ | Basic implementation with static analysis |
| FastAPI integration | ✅ | `mount()` helper and health routes |
| Sandbox execution | ✅ | Configurable subprocess execution |
| Hypothesis support | ✅ | Property-based testing integration |
| MCP server | ✅ | Read-only operations (Phase 1) |

## Phase 2 / Ongoing

The following backlog captures the remaining "Phase 2" items from SPEC Appendix A, plus new items for the v0.2 migration.

### ✅ Completed (v0.2)
1. **MCP server** - Full Model Context Protocol server implementation
2. **Claude Code Plugin** - Complete integration with slash commands and skills
3. **GitHub Actions** - Automated Claude Code review workflows
4. **Import system overhaul** - Removed `__generated__` shims, direct imports only
5. **API stabilization** - v0.2 API with VibeCoded exception and simplified decorators
6. **Documentation updates** - Migration guide and updated examples

### 🚧 In Progress
7. **Interactive REPL enhancements**
    - Add `tighten`, `save`, `split`, `rollback`, and drift diff commands to the REPL.
8. **Advanced dependency tracer**
    - Hybrid static/dynamic tracing with runtime sampling for dependency digests.
9. **LLM provider matrix**
    - Support additional providers (Anthropic, local inference, etc.) beyond the OpenAI-compatible backend.
10. **CLI surface**
    - `vibe diff --target unit` with prompt/code diff, `vibe status` dashboard, `vibe check` with optional HTML report.
11. **MCP expansion**
    - Promote MCP server from read-only to full invocation/compile control.
12. **Prompts & templating**
    - Template registry with overrides, prompt diff tooling.
13. **Dependency freezing**
    - Richer metadata and automation for `vibe save --freeze-http-deps` with artifact bundling.
14. **Docs & tooling**
    - Developer guide on shipping checkpoints, offline workflows, and multi-env setups.

Update this file when new milestones are added or completed.
