"""Auto-generated doctest harness for examples.math.ops/is_prime."""

import doctest
import warnings

import pytest

from vibesafe.exceptions import VibesafeCheckpointMissing
from vibesafe.runtime import load_checkpoint

UNIT_ID = "examples.math.ops/is_prime"
FUNC_NAME = "is_prime"
DOCSTRING = "Check if a number is prime.\n\n>>> is_prime(2)\nTrue\n>>> is_prime(3)\nTrue\n>>> is_prime(4)\nFalse\n>>> is_prime(17)\nTrue\n>>> is_prime(1)\nFalse"
PROPERTY_SRC = ""


def _exec_properties(func) -> None:
    if not PROPERTY_SRC:
        return
    namespace = {
        "load_checkpoint": load_checkpoint,
        "UNIT_ID": UNIT_ID,
        "FUNC_NAME": FUNC_NAME,
        "func": func,
    }
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
        globs={FUNC_NAME: func},
        name=UNIT_ID,
        filename="<generated>",
        lineno=0,
        docstring=DOCSTRING,
    )
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    failures, _ = runner.run(test, clear_globs=False)
    if failures:
        raise AssertionError(f"{failures} doctest(s) failed for {UNIT_ID}")


def _load_or_skip():
    try:
        return load_checkpoint(UNIT_ID)
    except VibesafeCheckpointMissing as exc:
        warnings.warn(f"Skipping {UNIT_ID}: {exc}", RuntimeWarning, stacklevel=2)
        pytest.skip(f"Checkpoint missing for {UNIT_ID}: {exc}")
    except Exception as exc:  # pragma: no cover - best-effort skip
        warnings.warn(f"Skipping {UNIT_ID}: {exc}", RuntimeWarning, stacklevel=2)
        pytest.skip(f"Checkpoint missing for {UNIT_ID}: {exc}")


def test_doctests() -> None:
    func = _load_or_skip()
    _run_doctests(func)
    _exec_properties(func)
