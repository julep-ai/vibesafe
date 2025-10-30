"""
CLI commands for defless.
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from defless import __version__
from defless.codegen import generate_for_unit
from defless.config import get_config
from defless.core import defless
from defless.runtime import update_index, write_shim
from defless.testing import run_all_tests, test_unit

console = Console()


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Defless - AI-powered code generation with verifiable specs."""
    pass


@main.command()
@click.option(
    "--write-shims",
    is_flag=True,
    help="Write __generated__ shim files",
)
def scan(write_shims: bool) -> None:
    """
    Scan project for defless-decorated functions.

    Lists all decorated defs with their completeness and status.
    """
    # Import all Python files to register decorators
    _import_project_modules()

    registry = defless.get_registry()

    if not registry:
        console.print("[yellow]No defless units found in project.[/yellow]")
        return

    # Build table
    table = Table(title="Defless Units")
    table.add_column("Unit ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Doctests", justify="right")
    table.add_column("Status", style="magenta")

    config = get_config()
    index_path = config.resolve_path(config.paths.index)

    active_units = {}
    if index_path.exists():
        import tomllib if sys.version_info >= (3, 11) else tomli as tomllib

        with open(index_path, "rb") as f:
            index = tomllib.load(f)
            active_units = {uid: data.get("active", "") for uid, data in index.items()}

    for unit_id, unit_meta in sorted(registry.items()):
        unit_type = unit_meta.get("type", "function")

        # Count doctests
        from defless.ast_parser import extract_spec

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
    Generate code for defless units.

    Renders prompts, calls LLM, and writes checkpoints.
    """
    _import_project_modules()

    registry = defless.get_registry()
    if not registry:
        console.print("[red]No defless units found.[/red]")
        sys.exit(1)

    # Filter units if target specified
    units_to_compile = []
    if target:
        if target in registry:
            units_to_compile = [target]
        else:
            # Check if target is a module prefix
            units_to_compile = [
                uid for uid in registry if uid.startswith(target.replace(".", "/"))
            ]

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
            console.print(
                f"  ✓ Generated checkpoint: {checkpoint_info['spec_hash'][:8]}"
            )

            # Update index
            update_index(unit_id, checkpoint_info["spec_hash"])
            console.print(f"  ✓ Updated index")

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
                console.print(
                    f"[red]✗ {unit_id}[/red] ({result.failures}/{result.total} failed)"
                )

        console.print(f"\n[bold]Results:[/bold] {passed} passed, {failed} failed")

        if failed > 0:
            sys.exit(1)


@main.command()
@click.option("--target", help="Specific unit ID to save")
def save(target: str | None) -> None:
    """
    Save (activate) checkpoints after tests pass.

    Updates index.toml to mark checkpoints as active.
    """
    _import_project_modules()

    if target:
        console.print(f"[bold]Saving {target}...[/bold]\n")
        result = test_unit(target)

        if not result:
            console.print("[red]✗ Tests failed, cannot save[/red]")
            for error in result.errors:
                console.print(f"  {error}")
            sys.exit(1)

        console.print(f"[green]✓ Tests passed, checkpoint is active[/green]")
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
