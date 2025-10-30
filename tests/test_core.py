"""
Tests for defless.core module.
"""

import inspect
from typing import Any

import pytest

from defless import DeflessHandled, defless
from defless.core import DeflessDecorator


class TestDeflessHandled:
    """Tests for DeflessHandled sentinel."""

    def test_defless_handled_repr(self):
        """Test DeflessHandled representation."""
        handled = DeflessHandled()
        assert repr(handled) == "DeflessHandled()"

    def test_defless_handled_is_unique_instance(self):
        """Test that each DeflessHandled is a separate instance."""
        h1 = DeflessHandled()
        h2 = DeflessHandled()
        assert type(h1) == type(h2)
        assert h1 is not h2


class TestDeflessDecorator:
    """Tests for DeflessDecorator class."""

    def test_decorator_initialization(self):
        """Test that decorator initializes with empty registry."""
        decorator = DeflessDecorator()
        assert decorator._registry == {}

    def test_func_decorator_basic(self, clear_defless_registry):
        """Test basic function decoration."""

        @defless.func
        def test_func(x: int) -> int:
            """Test function."""
            yield DeflessHandled()

        assert hasattr(test_func, "__defless_unit_id__")
        assert hasattr(test_func, "__defless_type__")
        assert test_func.__defless_type__ == "function"

    def test_func_decorator_registers_unit(self, clear_defless_registry):
        """Test that decoration registers the unit."""

        @defless.func
        def another_func(a: str) -> str:
            """Another test."""
            yield DeflessHandled()

        registry = defless.get_registry()
        assert len(registry) >= 1
        unit_id = another_func.__defless_unit_id__
        assert unit_id in registry
        assert registry[unit_id]["type"] == "function"

    def test_func_decorator_with_params(self, clear_defless_registry):
        """Test function decorator with parameters."""

        @defless.func(provider="custom", template="custom.j2")
        def param_func(x: int) -> int:
            """With params."""
            yield DeflessHandled()

        assert param_func.__defless_provider__ == "custom"
        assert param_func.__defless_template__ == "custom.j2"

    def test_http_decorator_basic(self, clear_defless_registry):
        """Test HTTP endpoint decoration."""

        @defless.http(method="POST", path="/test")
        async def test_endpoint(x: int) -> dict[str, int]:
            """Test endpoint."""
            return DeflessHandled()

        assert hasattr(test_endpoint, "__defless_unit_id__")
        assert test_endpoint.__defless_type__ == "http"
        assert test_endpoint.__defless_method__ == "POST"
        assert test_endpoint.__defless_path__ == "/test"

    def test_http_decorator_registers_unit(self, clear_defless_registry):
        """Test HTTP decoration registers unit."""

        @defless.http(method="GET", path="/hello")
        async def hello_endpoint(name: str) -> dict[str, str]:
            """Hello endpoint."""
            return DeflessHandled()

        registry = defless.get_registry()
        unit_id = hello_endpoint.__defless_unit_id__
        assert unit_id in registry
        assert registry[unit_id]["type"] == "http"
        assert registry[unit_id]["method"] == "GET"
        assert registry[unit_id]["path"] == "/hello"

    def test_http_decorator_with_params(self, clear_defless_registry):
        """Test HTTP decorator with custom params."""

        @defless.http(
            method="PUT",
            path="/update",
            provider="custom",
            template="http_custom.j2",
        )
        async def update_endpoint(id: int, data: str) -> dict[str, Any]:
            """Update endpoint."""
            return DeflessHandled()

        assert update_endpoint.__defless_provider__ == "custom"
        assert update_endpoint.__defless_template__ == "http_custom.j2"

    def test_func_decorator_raises_on_missing_checkpoint(self, clear_defless_registry):
        """Test that calling uncompiled function raises error."""

        @defless.func
        def uncompiled_func(x: int) -> int:
            """Not compiled."""
            yield DeflessHandled()

        with pytest.raises(RuntimeError, match="has not been compiled yet"):
            uncompiled_func(5)

    @pytest.mark.asyncio
    async def test_http_decorator_raises_on_missing_checkpoint(
        self, clear_defless_registry
    ):
        """Test that calling uncompiled endpoint raises error."""

        @defless.http(method="GET", path="/test")
        async def uncompiled_endpoint(x: int) -> dict[str, int]:
            """Not compiled."""
            return DeflessHandled()

        with pytest.raises(RuntimeError, match="has not been compiled yet"):
            await uncompiled_endpoint(5)

    def test_get_registry(self, clear_defless_registry):
        """Test get_registry returns copy of registry."""

        @defless.func
        def func1(x: int) -> int:
            yield DeflessHandled()

        @defless.func
        def func2(y: str) -> str:
            yield DeflessHandled()

        registry = defless.get_registry()
        assert len(registry) == 2

        # Modifying returned registry shouldn't affect internal
        registry.clear()
        assert len(defless.get_registry()) == 2

    def test_get_unit(self, clear_defless_registry):
        """Test get_unit retrieves specific unit metadata."""

        @defless.func
        def specific_func(x: int) -> int:
            """Specific."""
            yield DeflessHandled()

        unit_id = specific_func.__defless_unit_id__
        unit_meta = defless.get_unit(unit_id)

        assert unit_meta is not None
        assert unit_meta["type"] == "function"
        assert unit_meta["qualname"] == "specific_func"

    def test_get_unit_nonexistent(self, clear_defless_registry):
        """Test get_unit returns None for nonexistent unit."""
        result = defless.get_unit("nonexistent/unit")
        assert result is None

    def test_func_preserves_function_metadata(self, clear_defless_registry):
        """Test that decorator preserves function name and docstring."""

        @defless.func
        def my_func(x: int, y: int) -> int:
            """This is my function."""
            yield DeflessHandled()

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "This is my function."

    @pytest.mark.asyncio
    async def test_http_preserves_function_metadata(self, clear_defless_registry):
        """Test HTTP decorator preserves function metadata."""

        @defless.http(method="POST", path="/endpoint")
        async def my_endpoint(data: str) -> dict[str, str]:
            """Endpoint docstring."""
            return DeflessHandled()

        assert my_endpoint.__name__ == "my_endpoint"
        assert my_endpoint.__doc__ == "Endpoint docstring."

    def test_multiple_functions_in_same_module(self, clear_defless_registry):
        """Test multiple functions can be decorated in same module."""

        @defless.func
        def func_a(x: int) -> int:
            yield DeflessHandled()

        @defless.func
        def func_b(x: str) -> str:
            yield DeflessHandled()

        @defless.func
        def func_c(x: float) -> float:
            yield DeflessHandled()

        registry = defless.get_registry()
        assert len(registry) >= 3
