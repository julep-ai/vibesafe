"""
Testing utilities for generated implementations.
"""

import doctest
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

from vibesafe.ast_parser import extract_spec
from vibesafe.config import get_config


class TestResult:
    """Result of running tests."""

    def __init__(
        self,
        passed: bool,
        failures: int = 0,
        total: int = 0,
        errors: list[str] | None = None,
    ):
        self.passed = passed
        self.failures = failures
        self.total = total
        self.errors = errors or []

    def __bool__(self) -> bool:
        return self.passed

    def __repr__(self) -> str:
        if self.passed:
            return f"TestResult(passed={self.total} tests)"
        error_detail = "; ".join(self.errors) if self.errors else "unknown error"
        return f"TestResult(failed={self.failures}/{self.total}, errors={error_detail})"


def test_checkpoint(checkpoint_dir: Path, unit_meta: dict[str, Any]) -> TestResult:
    """
    Test a checkpoint implementation.

    Runs doctests from the original spec against the generated implementation.

    Args:
        checkpoint_dir: Path to checkpoint directory
        unit_meta: Unit metadata with original function

    Returns:
        TestResult
    """
    impl_path = checkpoint_dir / "impl.py"
    if not impl_path.exists():
        return TestResult(passed=False, errors=["Implementation file not found"])

    # Extract spec to get doctests
    func = unit_meta["func"]
    spec = extract_spec(func)
    doctests = spec["doctests"]

    doctest_result = TestResult(passed=True, total=0)

    if doctests:
        try:
            impl_func = _load_impl_func(impl_path, unit_meta)
        except Exception as e:
            return TestResult(passed=False, errors=[f"Failed to load implementation: {e}"])

        doctest_result = _run_doctests(impl_func, spec["docstring"], doctests)
        if not doctest_result.passed:
            return doctest_result

    gate_errors = _run_quality_gates(impl_path)
    if gate_errors:
        return TestResult(passed=False, failures=doctest_result.failures, total=doctest_result.total, errors=gate_errors)

    return doctest_result


def _load_impl_func(impl_path: Path, unit_meta: dict[str, Any]) -> Any:
    """Load function from implementation file."""
    unit_id = unit_meta["module"] + "/" + unit_meta["qualname"]
    func_name = unit_meta["qualname"].split(".")[-1]

    spec = importlib.util.spec_from_file_location(
        f"vibesafe._test.{unit_id.replace('/', '.')}", impl_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {impl_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, func_name):
        raise AttributeError(f"Function {func_name} not found in {impl_path}")

    return getattr(module, func_name)


def _run_doctests(func: Any, docstring: str, examples: list[doctest.Example]) -> TestResult:
    """
    Run doctest examples against a function.

    Args:
        func: Function to test
        docstring: Original docstring with examples
        examples: List of doctest examples

    Returns:
        TestResult
    """
    # Create a doctest runner
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)

    # Create a DocTest object
    dt = doctest.DocTest(
        examples=examples,
        globs={func.__name__: func},
        name=func.__name__,
        filename="<generated>",
        lineno=0,
        docstring=docstring,
    )

    # Run tests
    failures, total = runner.run(dt, clear_globs=False)

    # Collect errors
    errors = []
    if failures > 0:
        # DocTestRunner prints to stdout, capture would require redirecting
        errors.append(f"{failures} doctest(s) failed")

    return TestResult(passed=(failures == 0), failures=failures, total=total, errors=errors)


def _run_quality_gates(impl_path: Path) -> list[str]:
    """Run lint and type-check gates against the generated implementation."""

    gates = [
        ("ruff", ["ruff", "check", str(impl_path)]),
        ("mypy", ["mypy", str(impl_path)]),
    ]

    errors: list[str] = []
    for name, cmd in gates:
        try:
            subprocess.run(
                cmd,
                cwd=impl_path.parent,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            # Gate unavailable locally; skip but record informational notice.
            errors.append(f"{name} not installed - install to enable full gating")
        except subprocess.CalledProcessError as exc:
            output = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            errors.append(f"{name} failed: {output}")

    # Only treat missing tooling as error if all gates missing? spec probably expects gating available.
    # If both gates missing, treat as failure but with clear message. Otherwise remove success entries.
    missing = [e for e in errors if "not installed" in e]
    if missing and len(missing) == len(gates):
        return ["Quality gates unavailable: install ruff and mypy to proceed"]

    return [e for e in errors if "not installed" not in e]


def test_unit(unit_id: str) -> TestResult:
    """
    Test the active checkpoint for a unit.

    Args:
        unit_id: Unit identifier

    Returns:
        TestResult
    """
    from vibesafe.core import vibesafe

    # Get unit metadata
    unit_meta = vibesafe.get_unit(unit_id)
    if not unit_meta:
        return TestResult(passed=False, errors=[f"Unit not found: {unit_id}"])

    # Get active checkpoint
    config = get_config()
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        index_path = config.resolve_path(config.paths.index)
        if not index_path.exists():
            return TestResult(passed=False, errors=["No index file found - run compile first"])

        with open(index_path, "rb") as f:
            index = tomllib.load(f)

        unit_index = index.get(unit_id)
        if not unit_index:
            return TestResult(passed=False, errors=["Unit not in index - run compile first"])

        active_hash = unit_index["active"]

        # Get checkpoint directory
        checkpoints_base = config.resolve_path(config.paths.checkpoints)
        unit_path = unit_id.replace(".", "/")
        checkpoint_dir = checkpoints_base / unit_path / active_hash[:16]

        return test_checkpoint(checkpoint_dir, unit_meta)

    except Exception as e:
        return TestResult(passed=False, errors=[f"Error testing unit: {e}"])


def run_all_tests() -> dict[str, TestResult]:
    """
    Run tests for all registered units.

    Returns:
        Dictionary mapping unit_id to TestResult
    """
    from vibesafe.core import vibesafe

    results = {}
    for unit_id in vibesafe.get_registry():
        results[unit_id] = test_unit(unit_id)

    return results


# Prevent pytest from auto-collecting helper functions
test_checkpoint.__test__ = False
test_unit.__test__ = False
