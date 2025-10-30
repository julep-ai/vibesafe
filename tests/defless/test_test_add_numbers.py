"""Auto-generated doctest harness for test/add_numbers."""

import doctest
from vibesafe.runtime import load_active

UNIT_ID = 'test/add_numbers'
FUNC_NAME = 'add_numbers'
DOCSTRING = "Add two numbers.\n\n>>> add_numbers(2, 3)\n5"
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
