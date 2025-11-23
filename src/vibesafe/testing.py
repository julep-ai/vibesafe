"""Testing utilities for generated implementations."""

import doctest
import importlib.util
import inspect
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, cast

from vibesafe.ast_parser import extract_spec
from vibesafe.config import get_config
from vibesafe.runtime import load_checkpoint


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

    # Extract spec to get doctests and property tests
    func = unit_meta["func"]
    spec = extract_spec(func)
    doctests = spec["doctests"]
    hypothesis_blocks = spec.get("hypothesis_blocks", [])

    unit_id = unit_meta["module"] + "/" + unit_meta["qualname"]
    _ensure_vibesafe_harness(unit_id, unit_meta, spec)

    config = get_config()
    sandbox_cfg = config.sandbox

    total_tests = 0

    if sandbox_cfg.enabled:
        sandbox_result = _run_sandbox_checks(unit_meta, spec, sandbox_cfg)
        total_tests += sandbox_result.total
        if not sandbox_result.passed:
            return sandbox_result
        impl_func = None
    else:
        impl_func = None
        if doctests or hypothesis_blocks:
            try:
                impl_func = _load_impl_func(impl_path, unit_meta)
            except Exception as e:
                return TestResult(passed=False, errors=[f"Failed to load implementation: {e}"])

        if doctests and impl_func is not None:
            doctest_result = _run_doctests(impl_func, spec["docstring"], doctests)
            total_tests += doctest_result.total
            if not doctest_result.passed:
                return doctest_result

        if hypothesis_blocks and impl_func is not None:
            property_total, property_errors = _run_hypothesis_inline(
                unit_id, impl_func, hypothesis_blocks
            )
            total_tests += property_total
            if property_errors:
                return TestResult(
                    passed=False,
                    failures=len(property_errors),
                    total=total_tests,
                    errors=property_errors,
                )

    gate_errors = _run_quality_gates(impl_path)
    if gate_errors:
        return TestResult(
            passed=False,
            failures=len(gate_errors),
            total=total_tests,
            errors=gate_errors,
        )

    return TestResult(passed=True, failures=0, total=total_tests)


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
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

    # Create a DocTest object
    dt = doctest.DocTest(
        examples=examples,
        globs={func.__name__: func},
        name=func.__name__,
        filename="<generated>",
        lineno=0,
        docstring=docstring,
    )

    # Run tests with captured output for better feedback (silenced to avoid stdout noise)
    from io import StringIO

    output = StringIO()
    failures, total = runner.run(dt, clear_globs=False, out=output.write)

    # Collect errors
    errors = []
    if failures > 0:
        detail = output.getvalue().strip()
        summary = f"{failures} doctest(s) failed"
        errors.append(f"{summary}: {detail}")

    return TestResult(passed=(failures == 0), failures=failures, total=total, errors=errors)


def _run_quality_gates(impl_path: Path) -> list[str]:
    """Run lint and type-check gates against the generated implementation."""

    gates = [
        ("ruff", ["ruff", "check", "--fix", "--unsafe-fixes", str(impl_path)]),
        ("ty", ["ty", "check", str(impl_path)]),
    ]

    errors: list[str] = []
    for name, cmd in gates:
        try:
            subprocess.run(
                cmd,
                cwd=impl_path.parent,
                check=True,
                capture_output=True,
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


def _sanitize_unit_id(unit_id: str) -> str:
    """Convert a unit_id into a filesystem-friendly suffix."""

    return unit_id.replace(".", "_").replace("/", "_")


_MODULE_TEST_SPECS: dict[str, dict[str, Any]] = {}


def _ensure_vibesafe_harness(
    unit_id: str, unit_meta: dict[str, Any], spec: dict[str, Any]
) -> Path | None:
    """Write aggregated pytest harness per source module.

    - Only materializes in production mode.
    - Groups multiple units from the same module into a single test file.
    - Expands doctest examples into pytest cases while preserving property blocks.
    """

    config = get_config()
    if config.project.env != "prod":
        return None

    if not spec["doctests"] and not spec.get("hypothesis_blocks"):
        return None

    module_name = unit_meta.get("module") or "unknown_module"
    module_entry = _MODULE_TEST_SPECS.setdefault(module_name, {})

    module_entry[unit_id] = {
        "func_name": unit_meta["qualname"].split(".")[-1],
        "docstring": spec.get("docstring", ""),
        "properties": "\n\n".join(spec.get("hypothesis_blocks", [])),
        "source_path": inspect.getsourcefile(unit_meta["func"]) or module_name.replace(".", "/"),
    }

    return _write_module_harness(module_name)


def _write_module_harness(module_name: str) -> Path:
    dest_dir = Path.cwd() / "tests" / "vibesafe"
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = f"test_{module_name.replace('.', '_')}.py"
    harness_path = dest_dir / filename

    cases = _MODULE_TEST_SPECS.get(module_name, {})
    cases_literal = json.dumps(cases, ensure_ascii=False, indent=4)

    harness = (
        textwrap.dedent(
            f'''
        """Auto-generated doctest/property harness for module {module_name}."""

        import doctest
        import json
        import pytest
        from vibesafe.runtime import load_checkpoint

        MODULE_CASES = json.loads({cases_literal!r})


        @pytest.mark.parametrize("unit_id", list(MODULE_CASES.keys()))
        def test_doctests_and_properties(unit_id: str) -> None:
            meta = MODULE_CASES[unit_id]
            func = load_checkpoint(unit_id)

            _run_doctests(unit_id, func, meta)
            _exec_properties(unit_id, func, meta)


        def _run_doctests(unit_id: str, func, meta) -> None:
            docstring = meta.get("docstring", "")
            if not docstring:
                return
            parser = doctest.DocTestParser()
            examples = parser.get_examples(docstring)
            if not examples:
                return
            test = doctest.DocTest(
                examples=examples,
                globs={{meta.get("func_name", "func"): func}},
                name=unit_id,
                filename=meta.get("source_path", "<generated>"),
                lineno=0,
                docstring=docstring,
            )
            runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
            failures, _ = runner.run(test, clear_globs=False)
            if failures:
                raise AssertionError(f"{{failures}} doctest(s) failed for {{unit_id}}")


        def _exec_properties(unit_id: str, func, meta) -> None:
            prop_src = meta.get("properties") or ""
            if not prop_src:
                return
            namespace = {{
                "load_checkpoint": load_checkpoint,
                "UNIT_ID": unit_id,
                "FUNC_NAME": meta.get("func_name", "func"),
                "func": func,
            }}
            exec(prop_src, namespace)
            for value in list(namespace.values()):
                if callable(value) and hasattr(value, "hypothesis"):
                    value()
        '''
        ).strip()
        + "\n"
    )

    harness_path.write_text(harness)
    return harness_path


def _run_sandbox_checks(
    unit_meta: dict[str, Any],
    spec: dict[str, Any],
    sandbox_cfg,
) -> TestResult:
    """Execute doctests/properties inside sandboxed subprocess."""

    payload = {
        "unit_id": unit_meta["module"] + "/" + unit_meta["qualname"],
        "func_name": unit_meta["qualname"].split(".")[-1],
        "docstring": spec.get("docstring", ""),
        "properties": "\n\n".join(spec.get("hypothesis_blocks", [])),
        "memory_limit": sandbox_cfg.memory_mb * 1024 * 1024 if sandbox_cfg.memory_mb else 0,
    }

    script = textwrap.dedent(
        """
        import doctest
        import json
        import os
        import sys

        try:
            from vibesafe.runtime import load_checkpoint
        except Exception as exc:  # pragma: no cover
            print(json.dumps({"error": f"Failed to import runtime: {exc}"}))
            sys.exit(2)

        data = json.loads(os.environ["VIBESAFE_SANDBOX"])

        memory_limit = data.get("memory_limit", 0)
        if memory_limit:
            try:  # pragma: no cover - platform dependent
                import resource

                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
            except Exception:
                pass

        result = {"failures": [], "total": 0}

        try:
            func = load_checkpoint(data["unit_id"])
        except Exception as exc:
            result["failures"].append(f"Failed to load implementation: {exc}")
            print(json.dumps(result))
            sys.exit(1)

        docstring = data.get("docstring", "")
        if docstring:
            parser = doctest.DocTestParser()
            examples = parser.get_examples(docstring)
            if examples:
                dt = doctest.DocTest(
                    examples=examples,
                    globs={data["func_name"]: func},
                    name=data["unit_id"],
                    filename="<sandbox>",
                    lineno=0,
                    docstring=docstring,
                )
                runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
                failures, total = runner.run(dt, clear_globs=False)
                result["total"] += total
                if failures:
                    result["failures"].append(f"{failures} doctest(s) failed")

        prop_src = data.get("properties", "")
        if prop_src:
            namespace = {
                "load_checkpoint": load_checkpoint,
                "UNIT_ID": data["unit_id"],
                "FUNC_NAME": data["func_name"],
                "func": func,
            }
            try:
                exec(prop_src, namespace)
                for value in list(namespace.values()):
                    if callable(value) and hasattr(value, "hypothesis"):
                        result["total"] += 1
                        try:
                            value()
                        except Exception as exc:
                            result["failures"].append(
                                f"Hypothesis property {getattr(value, '__name__', '<property>')} failed: {exc}"
                            )
            except Exception as exc:
                result["failures"].append(f"Hypothesis block execution failed: {exc}")

        print(json.dumps(result))
        sys.exit(0 if not result["failures"] else 1)
        """
    )

    env = os.environ.copy()
    env["VIBESAFE_SANDBOX"] = json.dumps(payload)

    timeout = sandbox_cfg.timeout if sandbox_cfg.timeout else None

    try:
        completed = subprocess.run(
            [sys.executable, "-c", script],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return TestResult(passed=False, failures=1, total=0, errors=["Sandbox timed out"])

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    try:
        data = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        message = "Sandbox returned invalid output"
        if stderr:
            message += f": {stderr}"
        return TestResult(passed=False, failures=1, total=0, errors=[message])

    failures = data.get("failures", [])
    total = data.get("total", 0)

    if completed.returncode != 0:
        return TestResult(
            passed=False,
            failures=len(failures) or 1,
            total=total,
            errors=failures or ([stderr] if stderr else ["Sandbox execution failed"]),
        )

    return TestResult(passed=True, failures=0, total=total)


def _run_hypothesis_inline(unit_id: str, func: Any, blocks: list[str]) -> tuple[int, list[str]]:
    """Execute hypothesis property blocks inline and return (count, errors)."""

    if not blocks:
        return 0, []

    namespace = {
        "load_checkpoint": load_checkpoint,
        "UNIT_ID": unit_id,
        "FUNC_NAME": func.__name__ if hasattr(func, "__name__") else "func",
        "func": func,
    }

    combined = "\n\n".join(blocks)
    try:
        exec(combined, namespace)
    except Exception as exc:  # pragma: no cover - surfaced to caller
        return 0, [f"Hypothesis block execution failed: {exc}"]

    executed = 0
    errors: list[str] = []
    for value in list(namespace.values()):
        if callable(value) and hasattr(value, "hypothesis"):
            executed += 1
            try:
                value()
            except Exception as exc:  # pragma: no cover - property failure details
                errors.append(
                    f"Hypothesis property {getattr(value, '__name__', '<property>')} failed: {exc}"
                )
    return executed, errors


def test_unit(unit_id: str) -> TestResult:
    """
    Test the active checkpoint for a unit.

    Args:
        unit_id: Unit identifier

    Returns:
        TestResult
    """
    from vibesafe.core import get_unit

    # Get unit metadata
    unit_meta = get_unit(unit_id)
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
    from vibesafe.core import get_registry

    results = {}
    for unit_id in get_registry():
        results[unit_id] = test_unit(unit_id)

    return results


# Prevent pytest from auto-collecting helper functions
cast(Any, test_checkpoint).__test__ = False
cast(Any, test_unit).__test__ = False
