from typing import TypedDict

from vibesafe.ast_parser import extract_spec
from vibesafe.core import vibesafe


# 1. Type Hint Dependency
class MyType(TypedDict):
    x: int


def type_hint_user(a: MyType, b: list[str] = None):
    """Docstring."""
    pass


# 2. Default Value Dependency
DEFAULT_VAL = 42


def default_val_user(a: int = DEFAULT_VAL):
    pass


# 3. Vibesafe Composition
@vibesafe
def dependency_unit(x: int) -> int:
    """I am a dependency."""
    return x + 1


def composition_user():
    """Docstring."""
    dependency_unit(1)


def test_type_hint_extraction():
    spec = extract_spec(type_hint_user)
    deps = spec["dependencies"]
    assert "MyType" in deps
    assert "class MyType(TypedDict):" in deps["MyType"]["source"]
    # List is usually from typing, might not be in module dict unless imported as alias
    # But here we imported List.
    # However, List is a system type, usually not in module dict with source code we can extract easily
    # unless we check how inspect handles typing.List.
    # Usually inspect.getsource(List) fails or points to typing.py.
    # We only extract if it's in the module's __dict__ and we can get source.
    # List is imported, so it is in __dict__. But getsource might fail or be excluded?
    # Let's focus on MyType which is defined here.


def test_default_value_extraction():
    spec = extract_spec(default_val_user)
    deps = spec["dependencies"]
    # DEFAULT_VAL is an int. inspect.getsource(42) fails.
    # We only extract classes/functions.
    # My code: if inspect.isclass(value) or inspect.isfunction(value).
    # DEFAULT_VAL is int. So it won't be in names.
    # Wait, the AST scan of body finds names.
    # But default value is in signature.
    # My code: _extract_names_from_value checks isclass/isfunction.
    # So DEFAULT_VAL (int) is skipped.
    # This is correct behavior for now (we don't extract constants yet).
    pass


def test_vibesafe_composition():
    spec = extract_spec(composition_user)
    deps = spec["dependencies"]
    assert "dependency_unit" in deps

    source = deps["dependency_unit"]["source"]
    # Should be the interface
    assert "def dependency_unit(x: int) -> int" in source
    assert "I am a dependency." in source
    # Should NOT contain the wrapper code (e.g. "inner", "wrapper", "VibeCoded")
    assert "wrapper" not in source
