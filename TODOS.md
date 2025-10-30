# Vibesafe TODOs

- [x] Update SPEC.md Part II CLI section to mention both `vibesafe` and the new `vibe` alias, and audit the doc for other command-name drift before release.
- [x] Implement the CLI `repl` workflow described in SPEC §14, including regen, tighten, diff, and save actions. *(current implementation covers generate/test/diff/summary; tighten/save remain to be layered on top)*
- [x] Generate doctest harness files under `tests/defless/` and integrate them into `vibesafe testing` flow per SPEC §12. *(now auto-written during test runs)*
- [x] Add optional Hypothesis/property-test support when docstrings include a `hypothesis:` fence (SPEC §12.2).
- [x] Expand hashing/tracing to cover dependency digests beyond the current simple implementation (SPEC §10, Phase 2 hybrid tracer).
- [x] Provide FastAPI `mount` helper and health/version routes promised in SPEC §13.
- [x] Implement sandboxed execution path controlled by `vibesafe.toml` `[sandbox]` settings (SPEC §22).
- [x] Add `vibe check` command to bundle lint/type/test/drift checks as referenced in SPEC §18.
- [x] Document shipping strategy for including checkpoint `impl.py` files (SPEC §17) once policy is decided.
- [x] Review remaining Phase 2 roadmap items in SPEC Appendix A and file granular issues for each milestone. *(tracked in ROADMAP.md)*
