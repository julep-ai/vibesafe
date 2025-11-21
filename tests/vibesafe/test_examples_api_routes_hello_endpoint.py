"""Auto-generated doctest harness for examples.api.routes/hello_endpoint."""

import doctest
from vibesafe.runtime import load_checkpoint

UNIT_ID = 'examples.api.routes/hello_endpoint'
FUNC_NAME = 'hello_endpoint'
DOCSTRING = "Greet a user by name.\n\n>>> import anyio\n>>> anyio.run(hello_endpoint, \"Alice\")\n{'message': 'Hello, Alice!'}\n>>> anyio.run(hello_endpoint, \"Bob\")\n{'message': 'Hello, Bob!'}"
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


def test_doctests() -> None:
    func = load_checkpoint(UNIT_ID)
    _run_doctests(func)
    _exec_properties(func)
