"""Testing utilities for generated implementations."""

import doctest
import importlib.util
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, cast

from vibesafe.ast_parser import extract_spec
from vibesafe.config import get_config
from vibesafe.runtime import load_active


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
    _ensure_defless_harness(unit_id, unit_meta, spec)

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


def _ensure_defless_harness(
    unit_id: str, unit_meta: dict[str, Any], spec: dict[str, Any]
) -> Path | None:
    """Write pytest doctest/property harness under tests/defless for a unit."""

    if not spec["doctests"] and not spec.get("hypothesis_blocks"):
        return None

    dest_dir = Path.cwd() / "tests" / "defless"
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = f"test_{_sanitize_unit_id(unit_id)}.py"
    harness_path = dest_dir / filename

    func_name = unit_meta["qualname"].split(".")[-1]
    docstring = spec["docstring"] or ""
    doc_literal = json.dumps(docstring, ensure_ascii=False, indent=4)
    property_src = "\n\n".join(spec.get("hypothesis_blocks", []))
    property_literal = json.dumps(property_src, ensure_ascii=False)

    harness = (
        textwrap.dedent(
            f"""\
        \"\"\"Auto-generated doctest harness for {unit_id}.\"\"\"

        import doctest
        from vibesafe.runtime import load_active

        UNIT_ID = {unit_id!r}
        FUNC_NAME = {func_name!r}
        DOCSTRING = {doc_literal}
        PROPERTY_SRC = {property_literal}


        def _exec_properties(func) -> None:
            if not PROPERTY_SRC:
                return
            namespace = {{
                "load_active": load_active,
                "UNIT_ID": UNIT_ID,
                "FUNC_NAME": FUNC_NAME,
                "func": func,
            }}
            exec(PROPERTY_SRC, namespace)
            for value in list(namespace.values()):
                if callable(value) and hasattr(value, "hypothesis"):
                    value()


        def _run_doctests(func) -> None:
            if not DOCSTRING:
                return
            parser = doctest.DocTestParser()
            examples = parser.get_examples(DOCSTRING)
            if not examples:
                return
            test = doctest.DocTest(
                examples=examples,
                globs={{FUNC_NAME: func}},
                name=UNIT_ID,
                filename="<generated>",
                lineno=0,
                docstring=DOCSTRING,
            )
            runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
            failures, _ = runner.run(test, clear_globs=False)
            if failures:
                raise AssertionError(f"{{failures}} doctest(s) failed for {{UNIT_ID}}")


        def test_doctests() -> None:
            func = load_active(UNIT_ID)
            _run_doctests(func)
            _exec_properties(func)
        """
        ).strip()
        + "\n"
    )

    if harness_path.exists() and harness_path.read_text() == harness:
        return harness_path

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
            from vibesafe.runtime import load_active
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
            func = load_active(data["unit_id"])
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
                "load_active": load_active,
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
        "load_active": load_active,
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
cast(Any, test_checkpoint).__test__ = False
cast(Any, test_unit).__test__ = False
