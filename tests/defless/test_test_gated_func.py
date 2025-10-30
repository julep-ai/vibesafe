"""Auto-generated doctest harness for test/gated_func."""

import doctest
from vibesafe.runtime import load_active

UNIT_ID = 'test/gated_func'
FUNC_NAME = 'gated_func'
DOCSTRING = "Example with doctest.\n\n>>> gated_func(1)\n1"
PROPERTY_SRC = ""


def _exec_properties(func) -> None:
    if not PROPERTY_SRC:
        return
    namespace = {
        "load_active": load_active,
        "UNIT_ID": UNIT_ID,
        "FUNC_NAME": FUNC_NAME,
        "func": func,
    }
    exec(PROPERTY_SRC, namespace)
    for value in list(namespace.values()):
        if callable(value) and hasattr(value, "hypothesis"):
            value()


def test_doctests() -> None:
    func = load_active(UNIT_ID)
    if DOCSTRING:
        globs = {FUNC_NAME: func}
        doctest.run_docstring_examples(
            func,
            DOCSTRING,
            name=UNIT_ID,
            optionflags=doctest.ELLIPSIS,
            globs=globs,
        )
    _exec_properties(func)
