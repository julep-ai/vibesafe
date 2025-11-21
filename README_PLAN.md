# README Refresh Plan (UPDATED: Phase 1 Complete)
- Lead with a concise, factual headline and subhead that state exactly what Vibesafe does, why it exists, and what is novel, followed by a tight TL;DR that surfaces the hardest technical problem Vibesafe solves and the measurable impact.
- Re-architect the body around a Diátaxis-inspired flow: `Overview`, `Quickstart Tutorial`, `How-To Guides`, `Reference`, and `Explanation`, ensuring each section answers a distinct user need and links to supporting resources.
- Ground every major section with concrete production anecdotes or benchmarks (scan throughput, drift detection rate, outage recoveries) and include honest trade-offs or limitations to match the expected Hacker News tone.
- Expand installation and environment setup into an actionable checklist with verified commands, supported Python versions, optional tooling (ruff, mypy, pyright), and a troubleshooting matrix for first-run issues; ensure code blocks use precise language tags.
- Add a `Why Engineers Care` section highlighting real integration patterns (CI hooks, frozen HTTP deps, prompt regression coverage), link to `examples/` fixtures, and call out how the contract in `vibesafe.toml` keeps local agents aligned.
- **NEW:** Include migration guide for v0.1 → v0.2 breaking changes (deprecated `__generated__/` shims, new import patterns)
- **NEW:** Highlight module-level registry API (`get_registry()`, `get_unit()`, `resolve_template_id()`)
- Close with a roadmap or status card that surfaces current coverage metrics, open checkpoints, and contribution guide links; provide accessible assets (diagram alt text, dark/light-friendly visuals) and invite discussion channels in a direct, utilitarian tone.

## Documentation Overhaul Plan

### Goals
- Deliver user-centric docs that are discoverable, actionable, and indexed cleanly by AI tooling.
- Align repo-level README, docs site, and CLI help so terminology, flows, and guarantees stay consistent.
- Capture integration playbooks and operational runbooks that highlight Vibesafe's differentiators.
- Standardize on Astro Starlight for the documentation site to maximize performance, accessibility, and component reuse.

### Structure
- **Getting Started**: Installation matrix, environment bootstrap, first `vibesafe scan` walkthrough, troubleshooting FAQ.
- **Core Concepts**: Diagrams and explanations for runtime, providers, orchestration flow, `vibesafe.toml` contract.
- **How-To Guides**: Task-oriented recipes (compile targets, diff drift, freeze HTTP deps, wire into CI).
- **Reference**: CLI command index, configuration schema, prompt template conventions, exceptions catalog.
- **Operations**: Monitoring hooks, regression workflows with `examples/`, upgrade playbooks, support cadence.
- **Appendices**: Glossary, compatibility table, changelog highlights, roadmap snapshot.

### Phases (UPDATED: Phase 1 Implementation Complete)
- **Phase 0 – Audit (COMPLETED)**: Inventory existing docs, README, prompts, and CLI help; map gaps against Diátaxis; capture user pain via issue tracker review.
- **Phase 1 – README Refresh (COMPLETED)**: Implemented the plan above, added quickstart assets, ensured tone and structure meet Hacker News expectations, secured internal review.
- **Phase 1.5 – API Migration (CURRENT)**: Document v0.1→v0.2 breaking changes, update import examples, add deprecation notices for shim system.
- **Phase 2 – Framework Setup (Week 3)**: Stand up the Astro Starlight documentation site, configure navigation, search, accessibility checks, and deployment automation.
- **Phase 3 – Content Drafting (Weeks 4-5)**: Populate Getting Started, Core Concepts, and How-To sections with tested workflows; include code samples verified via CI.
- **Phase 4 – Reference & Operations (Week 6)**: Generate CLI and config references, document operational runbooks, add diagrams and benchmarks, validate with SMEs.
- **Phase 5 – QA & Launch (Week 7)**: Run link and style validators, cross-check with README, pilot with select users, incorporate feedback, announce release, and define maintenance cadence.

### Key Updates for v0.2
- **Breaking Changes**: Document deprecated `__generated__/` shim system and migration to direct imports
- **New API**: Highlight module-level registry functions (`get_registry()`, `get_unit()`, `resolve_template_id()`)
- **CLI Updates**: Note removal of `--write-shims` flag and changes to `compile` command behavior
- **Examples**: Update all code samples to use current import patterns
