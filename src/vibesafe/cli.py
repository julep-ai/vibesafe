"""CLI commands for vibesafe."""

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from vibesafe import __version__
from vibesafe.ast_parser import extract_spec
from vibesafe.codegen import generate_for_unit
from vibesafe.config import get_config
from vibesafe.core import vibesafe
from vibesafe.hashing import compute_dependency_digest, compute_spec_hash
from vibesafe.runtime import update_index, write_shim
from vibesafe.testing import run_all_tests, test_unit

console = Console()


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Vibesafe - AI-powered code generation with verifiable specs."""
    pass


@main.command()
@click.option(
    "--write-shims",
    is_flag=True,
    help="Write __generated__ shim files",
)
def scan(write_shims: bool) -> None:
    """
    Scan project for vibesafe-decorated functions.

    Lists all decorated defs with their completeness and status.
    """
    # Import all Python files to register decorators
    _import_project_modules()

    registry = vibesafe.get_registry()

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

    active_units = {}
    if index_path.exists():
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        with open(index_path, "rb") as f:
            index = tomllib.load(f)
            active_units = {uid: data.get("active", "") for uid, data in index.items()}

    for unit_id, unit_meta in sorted(registry.items()):
        unit_type = unit_meta.get("type", "function")

        # Count doctests
        from vibesafe.ast_parser import extract_spec

        spec = extract_spec(unit_meta["func"])
        doctest_count = len(spec["doctests"])

        # Check status
        status = "⚠️  Not compiled" if unit_id not in active_units else "✅ Active"

        table.add_row(unit_id, unit_type, str(doctest_count), status)

    console.print(table)
    console.print(f"\n[bold]Total units:[/bold] {len(registry)}")

    if write_shims:
        console.print("\n[bold]Writing shims...[/bold]")
        for unit_id in active_units:
            shim_path = write_shim(unit_id)
            console.print(f"  ✓ {shim_path}")


@main.command()
@click.option("--target", help="Specific unit ID or module to compile")
@click.option("--force", is_flag=True, help="Force recompilation even if checkpoint exists")
def compile(target: str | None, force: bool) -> None:
    """
    Generate code for vibesafe units.

    Renders prompts, calls LLM, and writes checkpoints.
    """
    _import_project_modules()

    registry = vibesafe.get_registry()
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

    console.print(f"[bold]Compiling {len(units_to_compile)} unit(s)...[/bold]\n")

    for unit_id in units_to_compile:
        console.print(f"[cyan]→ {unit_id}[/cyan]")

        try:
            checkpoint_info = generate_for_unit(unit_id, force=force)
            console.print(f"  ✓ Generated checkpoint: {checkpoint_info['spec_hash'][:8]}")

            # Update index
            update_index(
                unit_id,
                checkpoint_info["spec_hash"],
                created=checkpoint_info.get("created_at"),
            )
            console.print("  ✓ Updated index")

            # Write shim
            shim_path = write_shim(unit_id)
            console.print(f"  ✓ Wrote shim: {shim_path}")

        except Exception as e:
            console.print(f"  [red]✗ Error: {e}[/red]")
            if "--verbose" in sys.argv:
                import traceback

                traceback.print_exc()

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

    registry = vibesafe.get_registry()
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

    registry = vibesafe.get_registry()
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
        provider_params = {
            "temperature": provider_cfg.temperature,
            "seed": provider_cfg.seed,
            "timeout": provider_cfg.timeout,
        }
        template_id = unit_meta.get("template", "prompts/function.j2")
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
    registry = vibesafe.get_registry()
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
        provider_params = {
            "temperature": provider_cfg.temperature,
            "seed": provider_cfg.seed,
            "timeout": provider_cfg.timeout,
        }
        template_id = unit_meta.get("template", "prompts/function.j2")
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
@click.option("--target", help="Unit ID to open in the REPL")
def repl(target: str | None) -> None:
    """Interactive compile/test loop for a vibesafe unit."""

    _import_project_modules()
    registry = vibesafe.get_registry()

    if not registry:
        console.print("[yellow]No vibesafe units found in project.[/yellow]")
        sys.exit(1)

    if not target:
        console.print("[red]Specify --target <unit_id> to open the REPL.[/red]")
        console.print("Known units:")
        for uid in sorted(registry):
            console.print(f"  - {uid}")
        sys.exit(1)

    if target not in registry:
        console.print(f"[red]Unknown unit: {target}[/red]")
        console.print("Known units:")
        for uid in sorted(registry):
            console.print(f"  - {uid}")
        sys.exit(1)

    unit_meta = registry[target]

    def _unit_hash_state() -> tuple[str, str, str]:
        config = get_config()
        provider_name = unit_meta.get("provider") or "default"
        provider_cfg = config.get_provider(provider_name)
        spec = extract_spec(unit_meta["func"])
        dependency_digest = compute_dependency_digest(spec["dependencies"])
        provider_params = {
            "temperature": provider_cfg.temperature,
            "seed": provider_cfg.seed,
            "timeout": provider_cfg.timeout,
        }
        template_id = unit_meta.get("template", "prompts/function.j2")
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
                unit_entry = index.get(target, {})
                active_hash = unit_entry.get("active", "—")
                created_at = unit_entry.get("created", "—")

        return current_hash, active_hash, created_at

    def _show_summary() -> None:
        spec = extract_spec(unit_meta["func"])
        current_hash, active_hash, created_at = _unit_hash_state()

        console.rule(f"Vibesafe REPL — {target}")
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
            checkpoint_info = generate_for_unit(target, force=force)
            update_index(
                target,
                checkpoint_info["spec_hash"],
                created=checkpoint_info.get("created_at"),
            )
            shim_path = write_shim(target)
            console.print(f"  ✓ spec hash {checkpoint_info['spec_hash'][:8]} • shim {shim_path}")
        except Exception as exc:  # pragma: no cover - surfaced to CLI user
            console.print(f"[red]✗ Generation failed: {exc}[/red]")
            return

        unit_meta = vibesafe.get_unit(target) or unit_meta
        _run_tests()

    def _run_tests() -> None:
        console.print("\n[bold]Running tests...[/bold]")
        result = test_unit(target)
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

    while True:
        try:
            raw = console.input("\n[bold cyan]repl>[/bold cyan] ")
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
    # Try to import common app directories
    cwd = Path.cwd()

    # Add cwd to path if not already there
    if str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))

    # Try common patterns
    patterns = ["app/**/*.py", "src/**/*.py", "*.py"]

    for pattern in patterns:
        for py_file in cwd.glob(pattern):
            if py_file.name.startswith("_") or "__generated__" in str(py_file):
                continue

            # Convert path to module name
            rel_path = py_file.relative_to(cwd)
            module_parts = list(rel_path.with_suffix("").parts)
            module_name = ".".join(module_parts)

            try:
                __import__(module_name)
            except Exception:
                # Skip files that can't be imported
                pass


if __name__ == "__main__":
    main()
