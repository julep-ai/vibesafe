# Vibesafe Roadmap

## Phase 1 (MVP) — ✅ COMPLETED

| Feature | Status | Notes |
|---------|--------|-------|
| Core decorator API | ✅ | Implemented as module-level registry |
| `@vibesafe.func` | ✅ | Pure function generation |
| `@vibesafe.http` | ✅ | FastAPI endpoint generation |
| Import shims | ⚠️ DEPRECATED | Removed in v0.2, replaced with direct imports |
| Template resolution | ✅ | Added `resolve_template_id()` helper |
| CLI commands | ✅ | scan, compile, test, save, status, diff |
| Doctest harness generation | ✅ | Auto-generated under `tests/defless/` |
| Hashing & dependency tracing | ✅ | Basic implementation with static analysis |
| FastAPI integration | ✅ | `mount()` helper and health routes |
| Sandbox execution | ✅ | Configurable subprocess execution |
| Hypothesis support | ✅ | Property-based testing integration |
| MCP server | ✅ | Read-only operations (Phase 1) |

## Phase 2 / Ongoing

The following backlog captures the remaining "Phase 2" items from SPEC Appendix A, plus new items for the v0.2 migration.

1. **Interactive REPL enhancements**
    - Add `tighten`, `save`, `split`, `rollback`, and drift diff commands to the REPL.
2. **Advanced dependency tracer**
    - Hybrid static/dynamic tracing with runtime sampling for dependency digests.
3. **LLM provider matrix**
    - Support additional providers (Anthropic, local inference, etc.) beyond the OpenAI-compatible backend.
4. **CLI surface**
    - `vibe diff --target unit` with prompt/code diff, `vibe status` dashboard, `vibe check` with optional HTML report.
5. **MCP expansion**
    - Promote MCP server from read-only to full invocation/compile control.
6. **Prompts & templating**
    - Template registry with overrides, prompt diff tooling.
7. **Dependency freezing**
    - Richer metadata and automation for `vibe save --freeze-http-deps` with artifact bundling.
8. **Docs & tooling**
    - Developer guide on shipping checkpoints, offline workflows, and multi-env setups.

### Import System Overhaul (v0.2)
9. **Import system overhaul** - Document best practices for importing generated code post-shim-deprecation
10. **Migration guide** - v0.1 → v0.2 breaking changes (shims removed, new import patterns)
11. **Deprecation warnings** - Add warnings to old docs still referencing `__generated__`
12. **Example updates** - Update all examples to use current import patterns
13. **Troubleshooting guide** - Create guide for users upgrading from v0.1

Update this file when new milestones are added or completed.
