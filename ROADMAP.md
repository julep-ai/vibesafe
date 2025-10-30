# Vibesafe Roadmap (Phase 2)

The following backlog captures the "Phase 2" items called out in SPEC Appendix A. Track
progress by opening issues referencing the bullet IDs below.

1. **Interactive REPL enhancements**
   - Add `tighten`, `save`, `split`, `rollback`, and drift diff commands to the REPL.
2. **Advanced dependency tracer**
   - Hybrid static/dynamic tracing with runtime sampling for dependency digests.
3. **LLM provider matrix**
   - Support additional providers (Anthropic, local inference, etc.) beyond the OpenAI-compatible backend.
4. **Sandbox execution**
   - Extend current doctest sandbox to run generated implementations under configurable resource limits (network/FS guards, timeouts). *(initial subprocess sandbox shipped; extend to full isolation and CLI toggles).* 
5. **Property-based testing UX**
   - Tighten Hypothesis integration (reporting, targeted replays).
6. **CLI surface**
   - `vibe diff --target unit` with prompt/code diff, `vibe status` dashboard, `vibe check` with optional HTML report.
7. **MCP expansion**
   - Promote MCP server from read-only to full invocation/compile control.
8. **Prompts & templating**
   - Template registry with overrides, prompt diff tooling.
9. **Dependency freezing**
   - Richer metadata and automation for `vibe save --freeze-http-deps` with artifact bundling.
10. **Docs & tooling**
    - Developer guide on shipping checkpoints, offline workflows, and multi-env setups.

Update this file when new milestones are added or completed.
