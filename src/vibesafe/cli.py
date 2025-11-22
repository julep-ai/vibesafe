"""CLI commands for vibesafe."""

import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import cast

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from vibesafe import __version__
from vibesafe.ast_parser import extract_spec
from vibesafe.codegen import generate_for_unit
from vibesafe.config import get_config, resolve_template_id
from vibesafe.core import get_registry, get_unit
from vibesafe.hashing import compute_dependency_digest, compute_spec_hash
from vibesafe.mcp import MCPServer
from vibesafe.runtime import update_index
from vibesafe.testing import run_all_tests, test_unit

console = Console()


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Vibesafe - AI-powered code generation with verifiable specs."""
    pass


@main.command()
def scan() -> None:
    """
    Scan project for vibesafe-decorated functions.

    Lists all decorated defs with their completeness and status.
    """
    # Import all Python files to register decorators
    _import_project_modules()

    registry = get_registry()

    if not registry:
        console.print("[yellow]No vibesafe units found in project.[/yellow]")
        return

    # Build table
    table = Table(title="Vibesafe Units")
    table.add_column("Unit ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Doctests", justify="right")
    table.add_column("Status", style="magenta")

    config = get_config()
    index_path = config.resolve_path(config.paths.index)

    active_index: dict[str, dict[str, str]] = {}
    if index_path.exists():
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        with open(index_path, "rb") as f:
            active_index = tomllib.load(f)

    for unit_id, unit_meta in sorted(registry.items()):
        unit_type = (
            unit_meta.get("kind")
            or unit_meta.get("type")
            or ("http" if "method" in unit_meta else "function")
        )

        spec = extract_spec(unit_meta["func"])
        doctest_count = len(spec["doctests"])

        # Compute drift vs active checkpoint if present
        provider_name = unit_meta.get("provider") or "default"
        provider_cfg = config.get_provider(provider_name)
        dependency_digest = compute_dependency_digest(spec["dependencies"])
        provider_params = _build_provider_params(provider_cfg)
        template_id = resolve_template_id(unit_meta, config, spec.get("type"))
        current_hash = compute_spec_hash(
            signature=spec["signature"],
            docstring=spec["docstring"],
            body_before_handled=spec["body_before_handled"],
            template_id=template_id,
            provider_model=provider_cfg.model,
            provider_params=provider_params,
            dependency_digest=dependency_digest,
        )

        unit_index = active_index.get(unit_id, {})
        active_hash = unit_index.get("active")

        if not active_hash:
            status = "⚠️  inactive"
        elif active_hash == current_hash:
            status = "✅ in sync"
        else:
            status = "⚠️  drift"

        table.add_row(unit_id, str(unit_type), str(doctest_count), status)

    console.print(table)
    console.print(f"\n[bold]Total units:[/bold] {len(registry)}")


@main.command()
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite an existing vibesafe.toml if present.",
)
def init(force: bool) -> None:
    """
    Initialize a project with a minimal vibesafe.toml and local folders.
    """

    config_path = Path("vibesafe.toml")
    if config_path.exists() and not force:
        console.print("[red]vibesafe.toml already exists; rerun with --force to overwrite.[/red]")
        sys.exit(1)

    # Minimal, temperature-free defaults
    config_content = """\
[project]
python = ">=3.12"
env = "dev"

[provider.default]
kind = "openai-compatible"
model = "gpt-5-mini"
seed = 42
reasoning_effort = "medium"
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
timeout = 60

[paths]
checkpoints = ".vibesafe/checkpoints"
cache = ".vibesafe/cache"
index = ".vibesafe/index.toml"
generated = "__generated__"

[sandbox]
enabled = false
timeout = 10
memory_mb = 256
"""

    config_path.write_text(config_content)
    Path(".vibesafe/checkpoints").mkdir(parents=True, exist_ok=True)
    Path(".vibesafe/cache").mkdir(parents=True, exist_ok=True)

    console.print(f"[green]✓ Created {config_path}[/green]")
    console.print("[green]✓ Prepared .vibesafe/ directories[/green]")
    console.print(
        "Next: set OPENAI_API_KEY and run `vibe scan` / `vibe compile` to generate implementations."
    )


@main.command()
@click.option("--target", help="Specific unit ID or module to compile")
@click.option("--force", is_flag=True, help="Force recompilation even if checkpoint exists")
@click.option(
    "--workers",
    type=click.IntRange(1, None),
    default=None,
    show_default=False,
    help="Number of parallel workers (default: CPU cores - 2, minimum 1).",
)
@click.option(
    "--max-iterations",
    type=click.IntRange(1, 10),
    default=4,
    show_default=True,
    help="Max LLM regeneration attempts per unit when tests/gates fail.",
)
def compile(target: str | None, force: bool, workers: int | None, max_iterations: int) -> None:
    """
    Generate code for vibesafe units.

    Renders prompts, calls LLM, and writes checkpoints.
    """
    _import_project_modules()

    registry = get_registry()
    if not registry:
        console.print("[red]No vibesafe units found.[/red]")
        sys.exit(1)

    # Filter units if target specified
    units_to_compile = []
    if target:
        if target in registry:
            units_to_compile = [target]
        else:
            # Check if target is a module prefix
            units_to_compile = [uid for uid in registry if uid.startswith(target.replace(".", "/"))]

        if not units_to_compile:
            console.print(f"[red]No units found matching: {target}[/red]")
            sys.exit(1)
    else:
        units_to_compile = list(registry.keys())

    auto_workers = max(((os.cpu_count() or 4) - 2), 1)
    worker_count = min(workers or auto_workers, len(units_to_compile))

    console.print(
        f"[bold]Compiling {len(units_to_compile)} unit(s) with {worker_count} worker(s)...[/bold]\n"
    )

    had_failures = False

    from vibesafe.testing import test_checkpoint

    registry_snapshot = registry  # local ref for worker closure

    def _compile_unit(
        unit_id: str, progress: Progress | None, task_id: int | None
    ) -> tuple[str, dict | None, object | None, list[str]]:
        """Return (unit_id, checkpoint_info, test_result, errors)."""
        unit_meta = registry_snapshot[unit_id]

        checkpoint_info: dict[str, object] | None = None
        test_result: object | None = None
        errors: list[str] = []
        previous_response_id: str | None = None
        previous_reasoning_details: dict | None = None

        for attempt in range(1, max_iterations + 1):
            try:
                if progress and task_id is not None:
                    progress.update(
                        task_id,
                        description=f"[cyan]{unit_id}[/cyan] gen (try {attempt}/{max_iterations})",
                    )
                checkpoint_info = generate_for_unit(
                    unit_id,
                    force=(force or attempt > 1),
                    feedback="\n".join(errors) if errors else None,
                    previous_response_id=previous_response_id,
                    previous_reasoning_details=previous_reasoning_details,
                )
                previous_response_id = (
                    checkpoint_info.get("response_id") if checkpoint_info else None
                )
                previous_reasoning_details = (
                    checkpoint_info.get("reasoning_details") if checkpoint_info else None
                )
                if progress and task_id is not None:
                    progress.update(
                        task_id,
                        description=f"[cyan]{unit_id}[/cyan] test (try {attempt}/{max_iterations})",
                    )

                test_result = test_checkpoint(checkpoint_info["checkpoint_dir"], unit_meta)
                errors = []
                if not test_result.passed:
                    errors = test_result.errors
                    continue  # retry

                # success
                if progress and task_id is not None:
                    progress.update(
                        task_id, description=f"[green]{unit_id}[/green] ✓", completed=True
                    )
                return unit_id, checkpoint_info, test_result, errors

            except Exception as exc:  # pragma: no cover - provider/environment failures
                errors = [str(exc)]
                # Retry if attempts remain; otherwise exit loop
                if attempt == max_iterations:
                    if progress and task_id is not None:
                        progress.update(
                            task_id, description=f"[red]{unit_id}[/red] error", completed=True
                        )
                    return unit_id, None, None, errors

        # Exhausted attempts with errors
        if progress and task_id is not None:
            progress.update(task_id, description=f"[red]{unit_id}[/red] failed", completed=True)
        return unit_id, checkpoint_info, test_result, errors

    results: list[tuple[str, dict | None, object | None, list[str]]] = []

    use_progress = isinstance(console, Console)
    progress: Progress | None = None

    if use_progress:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        )

    def _run_compile() -> None:
        if progress is None:
            # Fallback without rich progress (e.g., in tests)
            for uid in units_to_compile:
                results.append(_compile_unit(uid, None, None))
            return

        with progress:
            task_ids = {
                uid: progress.add_task(f"[cyan]{uid}[/cyan]: queued", total=None)
                for uid in units_to_compile
            }

            if worker_count == 1 or len(units_to_compile) == 1:
                for uid in units_to_compile:
                    results.append(_compile_unit(uid, progress, task_ids[uid]))
                    progress.update(task_ids[uid], completed=True)
                    progress.stop_task(task_ids[uid])
            else:
                with ThreadPoolExecutor(max_workers=worker_count) as executor:
                    future_map = {
                        executor.submit(_compile_unit, uid, progress, task_ids[uid]): uid
                        for uid in units_to_compile
                    }
                    for future in as_completed(future_map):
                        uid = future_map[future]
                        results.append(future.result())
                        progress.update(task_ids[uid], completed=True)
                        progress.stop_task(task_ids[uid])

    _run_compile()

    # Process results in submission order to keep output deterministic for the user.
    order = {uid: idx for idx, uid in enumerate(units_to_compile)}
    results.sort(key=lambda r: order[r[0]])

    for unit_id, checkpoint_info, test_result, errors in results:
        console.print(f"[cyan]→ {unit_id}[/cyan]")

        if checkpoint_info is None:
            had_failures = True
            console.print(f"  [red]✗ Error:[/red] {errors[0] if errors else 'unknown error'}")
            continue

        console.print(f"  ✓ Generated checkpoint: {checkpoint_info['spec_hash'][:8]}")

        update_index(
            unit_id,
            checkpoint_info["spec_hash"],
            created=checkpoint_info.get("created_at"),
        )
        console.print("  ✓ Updated index")

        if test_result and getattr(test_result, "passed", False):
            console.print(f"  ✓ Tests passed ({getattr(test_result, 'total', '?')} total)")
        else:
            had_failures = True
            total = getattr(test_result, "total", "?") if test_result else "?"
            failures = getattr(test_result, "failures", "?") if test_result else "?"
            console.print(f"  [red]✗ Tests failed ({failures}/{total})[/red]")
            for err in errors:
                console.print(f"    • {err}")

    if had_failures:
        console.print("\n[bold red]Compilation finished with errors.[/bold red]")
        sys.exit(1)

    console.print("\n[bold green]Compilation complete![/bold green]")


@main.command()
@click.option("--target", help="Specific unit ID to test")
def test(target: str | None) -> None:
    """
    Run tests for generated implementations.

    Runs doctests against active checkpoints.
    """
    _import_project_modules()

    if target:
        console.print(f"[bold]Testing {target}...[/bold]\n")
        result = test_unit(target)

        if result:
            console.print(f"[green]✓ {result.total} tests passed[/green]")
        else:
            console.print(f"[red]✗ {result.failures}/{result.total} tests failed[/red]")
            for error in result.errors:
                console.print(f"  {error}")
            sys.exit(1)
    else:
        console.print("[bold]Testing all units...[/bold]\n")
        results = run_all_tests()

        passed = sum(1 for r in results.values() if r.passed)
        failed = len(results) - passed

        for unit_id, result in sorted(results.items()):
            if result:
                console.print(f"[green]✓ {unit_id}[/green] ({result.total} tests)")
            else:
                console.print(f"[red]✗ {unit_id}[/red] ({result.failures}/{result.total} failed)")

        console.print(f"\n[bold]Results:[/bold] {passed} passed, {failed} failed")

        if failed > 0:
            sys.exit(1)


@main.command()
@click.option("--target", help="Specific unit ID to save")
@click.option(
    "--freeze-http-deps",
    is_flag=True,
    help="Capture HTTP dependency versions into requirements.vibesafe.txt",
)
def save(target: str | None, freeze_http_deps: bool) -> None:
    """
    Save (activate) checkpoints after tests pass.

    Updates index.toml to mark checkpoints as active.
    """
    _import_project_modules()

    registry = get_registry()
    if target:
        console.print(f"[bold]Saving {target}...[/bold]\n")
        result = test_unit(target)

        if not result:
            console.print("[red]✗ Tests failed, cannot save[/red]")
            for error in result.errors:
                console.print(f"  {error}")
            sys.exit(1)

        console.print("[green]✓ Tests passed, checkpoint is active[/green]")
        if freeze_http_deps:
            _freeze_http_dependencies([target], get_config())
    else:
        console.print("[bold]Testing all units before save...[/bold]\n")
        results = run_all_tests()

        failed_units = [uid for uid, r in results.items() if not r.passed]

        if failed_units:
            console.print("[red]✗ Some tests failed, cannot save:[/red]")
            for uid in failed_units:
                console.print(f"  - {uid}")
            sys.exit(1)

        console.print("[green]✓ All tests passed, all checkpoints are active[/green]")
        if freeze_http_deps:
            _freeze_http_dependencies(list(registry.keys()), get_config())


@main.command()
def status() -> None:
    """Summarize registry state and checkpoint drift."""
    _import_project_modules()

    registry = get_registry()
    if not registry:
        console.print("[yellow]No vibesafe units found in project.[/yellow]")
        return

    config = get_config()
    index_path = config.resolve_path(config.paths.index)

    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover
        import tomli as tomllib  # type: ignore[misc]

    index: dict[str, dict[str, str]] = {}
    if index_path.exists():
        with open(index_path, "rb") as fh:
            index = tomllib.load(fh)

    table = Table(title="Vibesafe Status")
    table.add_column("Unit ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Active", overflow="fold")
    table.add_column("Spec Hash", overflow="fold")
    table.add_column("Status", style="magenta")

    drift_count = 0

    for unit_id, unit_meta in sorted(registry.items()):
        provider_name = unit_meta.get("provider") or "default"
        provider_cfg = config.get_provider(provider_name)
        spec = extract_spec(unit_meta["func"])
        dependency_digest = compute_dependency_digest(spec["dependencies"])
        provider_params = _build_provider_params(provider_cfg)
        template_id = resolve_template_id(unit_meta, config, spec.get("type"))
        current_hash = compute_spec_hash(
            signature=spec["signature"],
            docstring=spec["docstring"],
            body_before_handled=spec["body_before_handled"],
            template_id=template_id,
            provider_model=provider_cfg.model,
            provider_params=provider_params,
            dependency_digest=dependency_digest,
        )

        unit_index = index.get(unit_id, {})
        active_hash = unit_index.get("active", "—")

        if not active_hash or active_hash == "—":
            status = "⚠️  inactive"
        elif active_hash == current_hash:
            status = "✅ in sync"
        else:
            status = "⚠️  drift"
            drift_count += 1

        table.add_row(unit_id, unit_meta.get("type", "function"), active_hash, current_hash, status)

    console.print(table)
    console.print(
        f"\n[bold]Units:[/bold] {len(registry)} • [bold yellow]drift[/bold yellow]: {drift_count}"
    )


@main.command()
@click.option("--target", help="Specific unit ID to diff")
def diff(target: str | None) -> None:
    """Show spec hash drift compared to active checkpoints."""

    _import_project_modules()
    registry = get_registry()
    if not registry:
        console.print("[yellow]No vibesafe units found in project.[/yellow]")
        return

    config = get_config()
    index_path = config.resolve_path(config.paths.index)

    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover
        import tomli as tomllib  # type: ignore[misc]

    index: dict[str, dict[str, str]] = {}
    if index_path.exists():
        with open(index_path, "rb") as fh:
            index = tomllib.load(fh)

    if target:
        units = [uid for uid in registry if uid == target]
        if not units:
            console.print(f"[red]No unit found matching: {target}[/red]")
            sys.exit(1)
    else:
        units = list(registry.keys())

    drift_found = False
    for unit_id in units:
        unit_meta = registry[unit_id]
        provider_name = unit_meta.get("provider") or "default"
        provider_cfg = config.get_provider(provider_name)
        spec = extract_spec(unit_meta["func"])
        dependency_digest = compute_dependency_digest(spec["dependencies"])
        provider_params = _build_provider_params(provider_cfg)
        template_id = resolve_template_id(unit_meta, config, spec.get("type"))
        current_hash = compute_spec_hash(
            signature=spec["signature"],
            docstring=spec["docstring"],
            body_before_handled=spec["body_before_handled"],
            template_id=template_id,
            provider_model=provider_cfg.model,
            provider_params=provider_params,
            dependency_digest=dependency_digest,
        )

        unit_index = index.get(unit_id, {})
        active_hash = unit_index.get("active")
        created_at = unit_index.get("created", "—")

        if not active_hash:
            console.print(f"[yellow]{unit_id}[/yellow]: no active checkpoint")
            continue

        if active_hash == current_hash:
            console.print(f"[green]{unit_id}[/green]: hashes match ({active_hash[:8]})")
            continue

        drift_found = True
        console.print(
            f"[red]{unit_id}[/red]: drift detected\n"
            f"  active:   {active_hash}\n"
            f"  current:  {current_hash}\n"
            f"  created:  {created_at}\n"
            f"  checkpoint: {(config.resolve_path(config.paths.checkpoints) / unit_id.replace('.', '/') / active_hash[:16])}"
        )

    if not drift_found:
        console.print("\n[green]No drift detected.[/green]")


@main.command()
def check() -> None:
    """Run lint, type-check, doctests, and drift detection."""

    _import_project_modules()

    overall_success = True

    console.print("[bold]Running lint (ruff)...[/bold]")
    lint_targets = [Path("src"), Path("tests"), Path("examples")]
    available_lint_targets = [str(target) for target in lint_targets if target.exists()]
    if available_lint_targets:
        ruff_cmd = ["ruff", "check", "--fix", "--unsafe-fixes", *available_lint_targets]
        if not _run_command(ruff_cmd):
            overall_success = False
    else:
        console.print("  [yellow]No lint targets found; skipping.[/yellow]")

    console.print("[bold]Running type checks (mypy)...[/bold]")
    mypy_target = Path("src") / "vibesafe"
    if mypy_target.exists():
        if not _run_command(["mypy", str(mypy_target)]):
            overall_success = False
    else:
        console.print(f"  [yellow]No mypy target found at {mypy_target}; skipping.[/yellow]")

    console.print("[bold]Running doctests...[/bold]")
    test_results = run_all_tests()
    failed_units = [uid for uid, result in test_results.items() if not result.passed]
    if failed_units:
        overall_success = False
        for uid in failed_units:
            result = test_results[uid]
            console.print(f"[red]✗ {uid}[/red] ({result.failures}/{result.total} failed)")
    else:
        total_tests = sum(result.total for result in test_results.values())
        console.print(f"[green]✓ All doctests passed ({total_tests} total)[/green]")

    console.print("[bold]Checking for drift...[/bold]")
    drift_count, missing_index = _detect_drift()
    if missing_index:
        overall_success = False
        console.print("[red]✗ No index found – run 'vibesafe compile' and 'vibesafe save'.[/red]")
    elif drift_count:
        overall_success = False
        console.print(f"[red]✗ Drift detected in {drift_count} unit(s).[/red]")
    else:
        console.print("[green]✓ No drift detected.[/green]")

    if overall_success:
        console.print("\n[bold green]Check complete – all gates passed.[/bold green]")
    else:
        console.print("\n[bold red]Check failed – see messages above.[/bold red]")
        sys.exit(1)


@main.command()
def mcp() -> None:
    """Run the Vibesafe MCP server over stdio (editor integration)."""
    server = MCPServer()
    server.run()


@main.command(name="install-claude-plugin")
def install_claude_plugin() -> None:
    """
    Install the Vibesafe Claude plugin via the Claude CLI.

    This prints manual steps because programmatic /plugin invocations can be flaky.
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        console.print("[red]Claude CLI not found in PATH. Install it first.[/red]")
        sys.exit(1)

    console.print("[bold]Manual install steps for Claude plugin:[/bold]")
    console.print("1) Add marketplace: /plugin marketplace add julep-ai/vibesafe")
    console.print("2) Install plugin:   /plugin install vibesafe@Vibesafe")
    console.print("3) Verify:           /plugin list (should show vibesafe)")
    console.print("\nRun these in Claude. Claude CLI located at:")
    console.print(f"  {claude_path}")


@main.command()
@click.option(
    "--value",
    type=click.Choice(["dev", "prod"]),
    help="Set the vibesafe mode (persists to .vibesafe/mode).",
)
@click.option(
    "--clear",
    is_flag=True,
    default=False,
    help="Remove persisted mode file (.vibesafe/mode).",
)
def mode(value: str | None, clear: bool) -> None:
    """
    View or set the vibesafe mode.

    Precedence: VIBESAFE_ENV > .vibesafe/mode > vibesafe.toml default.
    """
    mode_file = Path(".vibesafe") / "mode"

    if clear:
        try:
            mode_file.unlink()
            console.print("[green]Cleared persisted mode (.vibesafe/mode).[/green]")
        except FileNotFoundError:
            console.print("[yellow].vibesafe/mode not found; nothing to clear.[/yellow]")

    if value:
        mode_file.parent.mkdir(parents=True, exist_ok=True)
        mode_file.write_text(value)
        console.print(f"[green]Persisted mode set to '{value}' in .vibesafe/mode.[/green]")

    cfg = get_config(reload=True)

    env_var = os.getenv("VIBESAFE_ENV")
    persisted = None
    if mode_file.exists():
        try:
            persisted = mode_file.read_text().strip() or None
        except OSError:
            persisted = None

    console.print(f"VIBESAFE_ENV: {env_var or '<unset>'}")
    console.print(f".vibesafe/mode: {persisted or '<missing>'}")
    console.print(f"Effective mode: {cfg.project.env}")


@main.command()
@click.option("--target", help="Unit ID to open in the REPL")
def repl(target: str | None) -> None:
    """Interactive compile/test loop for a vibesafe unit."""

    _import_project_modules()
    registry = get_registry()

    if not registry:
        console.print("[yellow]No vibesafe units found in project.[/yellow]")
        sys.exit(1)

    if not target:
        console.print("[red]Specify --target <unit_id> to open the REPL.[/red]")
        console.print("Known units:")
        for uid in sorted(registry):
            console.print(f"  - {uid}")
        sys.exit(1)

    target_id = cast(str, target)

    if target_id not in registry:
        console.print(f"[red]Unknown unit: {target_id}[/red]")
        console.print("Known units:")
        for uid in sorted(registry):
            console.print(f"  - {uid}")
        sys.exit(1)

    unit_meta = registry[target_id]

    def _unit_hash_state() -> tuple[str, str, str]:
        config = get_config()
        provider_name = unit_meta.get("provider") or "default"
        provider_cfg = config.get_provider(provider_name)
        spec = extract_spec(unit_meta["func"])
        dependency_digest = compute_dependency_digest(spec["dependencies"])
        provider_params = _build_provider_params(provider_cfg)
        template_id = resolve_template_id(unit_meta, config, spec.get("type"))
        current_hash = compute_spec_hash(
            signature=spec["signature"],
            docstring=spec["docstring"],
            body_before_handled=spec["body_before_handled"],
            template_id=template_id,
            provider_model=provider_cfg.model,
            provider_params=provider_params,
            dependency_digest=dependency_digest,
        )

        config = get_config()
        index_path = config.resolve_path(config.paths.index)
        active_hash = "—"
        created_at = "—"
        if index_path.exists():
            if sys.version_info >= (3, 11):
                import tomllib
            else:  # pragma: no cover
                import tomli as tomllib  # type: ignore[misc]

            with open(index_path, "rb") as fh:
                index = tomllib.load(fh)
                unit_entry = index.get(target_id, {})
                active_hash = unit_entry.get("active", "—")
                created_at = unit_entry.get("created", "—")

        return current_hash, active_hash, created_at

    def _show_summary() -> None:
        spec = extract_spec(unit_meta["func"])
        current_hash, active_hash, created_at = _unit_hash_state()

        console.rule(f"Vibesafe REPL — {target_id}")
        console.print(
            f"[bold]Docstring lines:[/bold] {len(spec['docstring'].splitlines())} • "
            f"[bold]Doctests:[/bold] {len(spec['doctests'])}"
        )
        first_doc_line = spec["docstring"].splitlines()[0] if spec["docstring"] else ""
        if first_doc_line:
            console.print(f"[italic]{first_doc_line}[/italic]")
        console.print(
            f"[bold]Current hash:[/bold] {current_hash}\n"
            f"[bold]Active hash:[/bold] {active_hash}\n"
            f"[bold]Last activated:[/bold] {created_at}"
        )

    def _generate(force: bool = False) -> None:
        nonlocal unit_meta
        console.print("\n[bold]Generating implementation...[/bold]")
        try:
            checkpoint_info = generate_for_unit(target_id, force=force)
            update_index(
                target_id,
                checkpoint_info["spec_hash"],
                created=checkpoint_info.get("created_at"),
            )
            console.print(f"  ✓ spec hash {checkpoint_info['spec_hash'][:8]}")
        except Exception as exc:  # pragma: no cover - surfaced to CLI user
            console.print(f"[red]✗ Generation failed: {exc}[/red]")
            return

        unit_meta = get_unit(target_id) or unit_meta
        _run_tests()

    def _run_tests() -> None:
        console.print("\n[bold]Running tests...[/bold]")
        result = test_unit(target_id)
        if result:
            console.print(f"[green]✓ {result.total} test(s) passed[/green]")
        else:
            console.print(f"[red]✗ {result.failures}/{result.total} failed[/red]")
            for error in result.errors:
                console.print(f"  • {error}")

    def _show_diff() -> None:
        current_hash, active_hash, created_at = _unit_hash_state()
        if active_hash == "—":
            console.print("[yellow]No active checkpoint yet.[/yellow]")
            return
        if active_hash == current_hash:
            console.print(
                f"[green]Hashes match.[/green] active={active_hash[:8]} (created {created_at})"
            )
        else:
            console.print("[red]Drift detected.[/red]")
            console.print(f"  active:  {active_hash}")
            console.print(f"  current: {current_hash}")
            console.print(f"  created: {created_at}")

    def _print_help() -> None:
        console.print(
            "Commands: [bold]g[/bold]=generate, [bold]g![/bold]=force generate, "
            "[bold]t[/bold]=test, [bold]s[/bold]=show, [bold]d[/bold]=diff, "
            "[bold]q[/bold]=quit"
        )

    _show_summary()
    _print_help()

    prompt = "\n[bold cyan]repl>[/bold cyan] "
    plain_prompt = "\nrepl> "

    while True:
        try:
            raw = console.input(prompt) if isinstance(console, Console) else input(plain_prompt)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold]Exiting REPL.[/bold]")
            break

        if raw is None:
            continue

        cmd = raw.strip().lower()
        if not cmd:
            continue

        if cmd in {"q", "quit", "exit"}:
            console.print("[bold]Bye![/bold]")
            break

        force = cmd.endswith("!")
        if force:
            cmd = cmd[:-1]

        if cmd == "g":
            _generate(force=force)
        elif cmd == "t":
            _run_tests()
        elif cmd == "s":
            _show_summary()
        elif cmd == "d":
            _show_diff()
        elif cmd in {"?", "help", "h"}:
            _print_help()
        else:
            console.print("[yellow]Unknown command. Type 'h' for help.[/yellow]")


def _freeze_http_dependencies(units: list[str], config) -> None:
    """Capture dependency versions and update checkpoint metadata."""

    if not units:
        return

    try:
        freeze_proc = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        output = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        console.print(f"[red]✗ Failed to freeze dependencies: {output}[/red]")
        return

    requirements_path = Path.cwd() / "requirements.vibesafe.txt"
    requirements_path.write_text(freeze_proc.stdout)
    console.print(f"  ✓ Wrote dependency snapshot to {requirements_path}")

    deps_of_interest: dict[str, str] = {}
    for line in freeze_proc.stdout.splitlines():
        if "==" not in line:
            continue
        name, version = line.split("==", 1)
        normalized = name.lower()
        if normalized in {"fastapi", "starlette", "pydantic", "httpx"}:
            deps_of_interest[name] = version

    if not deps_of_interest:
        deps_of_interest["note"] = "dependencies captured in requirements.vibesafe.txt"

    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover
        import tomli as tomllib  # type: ignore[misc]

    index_path = config.resolve_path(config.paths.index)
    if not index_path.exists():
        console.print("[yellow]No index found; skipping meta updates.[/yellow]")
        return

    with open(index_path, "rb") as fh:
        index = tomllib.load(fh)

    checkpoints_base = config.resolve_path(config.paths.checkpoints)
    for unit_id in units:
        unit_index = index.get(unit_id)
        if not unit_index:
            continue
        active_hash = unit_index.get("active")
        if not active_hash:
            continue
        checkpoint_dir = checkpoints_base / unit_id.replace(".", "/") / active_hash[:16]
        meta_path = checkpoint_dir / "meta.toml"
        if not meta_path.exists():
            continue

        _write_deps_to_meta(meta_path, deps_of_interest)
        console.print(f"  ✓ Updated dependencies in {meta_path}")


def _write_deps_to_meta(meta_path: Path, deps: dict[str, str]) -> None:
    """Ensure meta.toml contains a [deps] section with provided entries."""

    lines = meta_path.read_text().splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("[deps]"):
            start_idx = idx
            break

    if start_idx is not None:
        lines = lines[:start_idx]
    if lines and lines[-1].strip():
        lines.append("")

    lines.append("[deps]")
    for name, version in sorted(deps.items()):
        lines.append(f'{name} = "{version}"')
    lines.append("")

    meta_path.write_text("\n".join(lines))


def _import_project_modules() -> None:
    """
    Import all Python modules in the project to register decorators.

    This is a simple implementation that imports from current directory.
    """
    cwd = Path.cwd()

    if str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))

    ignore_dirnames = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".cache",
        "node_modules",
        "dist",
        "build",
    }

    def _should_skip(path: Path) -> bool:
        return any(part in ignore_dirnames or part.startswith(".") for part in path.parts)

    for py_file in cwd.rglob("*.py"):
        if _should_skip(py_file) or "__generated__" in str(py_file):
            continue

        rel_path = py_file.relative_to(cwd)
        module_parts = rel_path.with_suffix("").parts

        # Skip modules with invalid python identifiers in path
        if any("-" in part for part in module_parts):
            continue

        module_name = ".".join(module_parts)

        try:
            __import__(module_name)
        except Exception:
            # Best-effort import; failures are ignored to keep scan resilient.
            continue


def _run_command(cmd: list[str]) -> bool:
    """Execute a shell command, returning True on success."""

    try:
        subprocess.run(cmd, check=True, text=True)
        console.print("  [green]✓ success[/green]")
        return True
    except FileNotFoundError:
        console.print(f"  [red]✗ Command not found:[/red] {' '.join(cmd)}")
    except subprocess.CalledProcessError as exc:
        output = ""
        if exc.stderr:
            output = exc.stderr.strip()
        elif exc.stdout:
            output = exc.stdout.strip()
        detail = f" ({output})" if output else ""
        console.print(f"  [red]✗ Command failed ({exc.returncode})[/red]{detail}")
    return False


def _build_provider_params(provider_cfg) -> dict[str, str | int | float]:
    """Return provider parameters (temperature is intentionally omitted)."""

    params: dict[str, str | int | float] = {
        "seed": provider_cfg.seed,
        "timeout": provider_cfg.timeout,
    }
    if provider_cfg.reasoning_effort:
        params["reasoning_effort"] = provider_cfg.reasoning_effort
    return params


def _detect_drift() -> tuple[int, bool]:
    """Return (drift_count, missing_index)."""

    registry = get_registry()
    if not registry:
        return 0, False

    config = get_config()
    index_path = config.resolve_path(config.paths.index)

    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover
        import tomli as tomllib  # type: ignore[misc]

    if not index_path.exists():
        return 0, True

    with open(index_path, "rb") as fh:
        index = tomllib.load(fh)

    drift_count = 0
    for unit_id, unit_meta in registry.items():
        provider_name = unit_meta.get("provider") or "default"
        provider_cfg = config.get_provider(provider_name)
        spec = extract_spec(unit_meta["func"])
        dependency_digest = compute_dependency_digest(spec["dependencies"])
        provider_params = _build_provider_params(provider_cfg)
        template_id = resolve_template_id(unit_meta, config, spec.get("type"))
        current_hash = compute_spec_hash(
            signature=spec["signature"],
            docstring=spec["docstring"],
            body_before_handled=spec["body_before_handled"],
            template_id=template_id,
            provider_model=provider_cfg.model,
            provider_params=provider_params,
            dependency_digest=dependency_digest,
        )

        unit_index = index.get(unit_id, {})
        active_hash = unit_index.get("active", "—")

        if active_hash != "—" and active_hash != current_hash:
            drift_count += 1

    return drift_count, False
