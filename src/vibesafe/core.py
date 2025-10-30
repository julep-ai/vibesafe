"""Core decorators and sentinel types for vibesafe."""

import contextlib
import functools
import inspect
import os
import sys
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from vibesafe.ast_parser import extract_spec
from vibesafe.exceptions import VibesafeMissingDoctest

P = ParamSpec("P")
R = TypeVar("R")


class VibesafeHandled:
    """
    Sentinel type marking where the spec ends and AI-generated code should begin.

    Usage:
        @vibesafe.func
        def my_func(x: int) -> int:
            '''Add 1 to x'''
            yield VibesafeHandled()
    """

    def __repr__(self) -> str:
        return "VibesafeHandled()"


VibeHandled = VibesafeHandled


class VibesafeDecorator:
    """
    Main decorator class for marking functions and endpoints for code generation.
    """

    def __init__(self):
        self._registry: dict[str, dict[str, Any]] = {}

    def func(
        self,
        fn: Callable[P, R] | None = None,
        *,
        provider: str | None = None,
        template: str | None = None,
    ) -> Callable[P, R]:
        """
        Decorator for pure/utility functions.

        Args:
            fn: The function to decorate
            provider: Override provider from config
            template: Override template path

        Example:
            @vibesafe.func
            def sum_str(a: str, b: str) -> str:
                '''Add two ints represented as strings.

                >>> sum_str("2", "3")
                '5'
                '''
                a, b = int(a), int(b)
                yield VibesafeHandled()
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            # Get module and qualname
            module = func.__module__
            qualname = func.__qualname__
            unit_id = f"{module}/{qualname}"

            # Store metadata
            default_template = "prompts/function.j2"
            self._registry[unit_id] = {
                "type": "function",
                "func": func,
                "provider": provider,
                "template": template or default_template,
                "module": module,
                "qualname": qualname,
            }

            # Mark the function
            func.__vibesafe_unit_id__ = unit_id  # type: ignore
            func.__vibesafe_type__ = "function"  # type: ignore
            func.__vibesafe_provider__ = provider  # type: ignore
            func.__vibesafe_template__ = template or default_template  # type: ignore

            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                # Import here to avoid circular dependency
                from vibesafe.runtime import load_active

                # Try to load generated implementation
                try:
                    impl = load_active(unit_id)
                    return impl(*args, **kwargs)
                except Exception as e:
                    generation_error: Exception | None = e

                    if self._should_auto_generate(e):
                        try:
                            impl = self._auto_generate_and_load(unit_id)
                            return impl(*args, **kwargs)
                        except Exception as auto_exc:  # pragma: no cover - surfaced to caller
                            generation_error = auto_exc

                    # Fall back to original function (which should yield VibesafeHandled)
                    result = func(*args, **kwargs)

                    error = generation_error
                    doctest_hint = None
                    if isinstance(error, VibesafeMissingDoctest):
                        doctest_hint = str(error)
                    else:
                        with contextlib.suppress(Exception):
                            spec_meta = extract_spec(func)
                            if not spec_meta["doctests"]:
                                doctest_hint = f"Spec {unit_id} does not declare any doctests; add at least one example."

                    def _raise_uncompiled(extra_hint: str | None = None) -> None:
                        base_message = (
                            f"Function {unit_id} has not been compiled yet. "
                            f"Run 'vibesafe compile --target {unit_id}' first."
                        )
                        hints = [extra_hint, doctest_hint]
                        merged = ". ".join(h for h in hints if h)
                        if merged:
                            base_message = f"{base_message} {merged}"
                        raise RuntimeError(base_message) from error

                    boundary_hint = (
                        "Specs must yield or return `VibesafeHandled()` to mark the AI boundary."
                    )

                    # Check if it's a generator that yielded VibesafeHandled
                    if inspect.isgenerator(result):
                        marker_seen = False
                        try:
                            for item in result:
                                if isinstance(item, VibesafeHandled):
                                    marker_seen = True
                                    break
                        finally:
                            with contextlib.suppress(Exception):
                                result.close()  # type: ignore[attr-defined]

                        if marker_seen:
                            _raise_uncompiled()

                        _raise_uncompiled(boundary_hint)

                    if isinstance(result, VibesafeHandled) or result is Ellipsis or result is None:
                        _raise_uncompiled()

                    _raise_uncompiled(boundary_hint)

            return wrapper  # type: ignore

        if fn is None:
            return decorator  # type: ignore
        return decorator(fn)

    def http(
        self,
        *,
        method: str = "GET",
        path: str = "/",
        provider: str | None = None,
        template: str | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Decorator for HTTP endpoints (FastAPI).

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path
            provider: Override provider from config
            template: Override template path

        Example:
            @vibesafe.http(method="POST", path="/sum")
            async def sum_endpoint(a: int, b: int) -> dict[str, int]:
                '''Returns {"sum": a+b}

                >>> import anyio
                >>> anyio.run(lambda: sum_endpoint(2, 3))
                {'sum': 5}
                '''
                return VibesafeHandled()
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            # Get module and qualname
            module = func.__module__
            qualname = func.__qualname__
            unit_id = f"{module}/{qualname}"

            # Store metadata
            default_template = "prompts/http_endpoint.j2"
            self._registry[unit_id] = {
                "type": "http",
                "func": func,
                "method": method,
                "path": path,
                "provider": provider,
                "template": template or default_template,
                "module": module,
                "qualname": qualname,
            }

            # Mark the function
            func.__vibesafe_unit_id__ = unit_id  # type: ignore
            func.__vibesafe_type__ = "http"  # type: ignore
            func.__vibesafe_method__ = method  # type: ignore
            func.__vibesafe_path__ = path  # type: ignore
            func.__vibesafe_provider__ = provider  # type: ignore
            func.__vibesafe_template__ = template or default_template  # type: ignore

            @functools.wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                # Import here to avoid circular dependency
                from vibesafe.runtime import load_active

                # Try to load generated implementation
                try:
                    impl = load_active(unit_id)
                    if inspect.iscoroutinefunction(impl):
                        return await impl(*args, **kwargs)
                    return impl(*args, **kwargs)
                except Exception as e:
                    generation_error: Exception | None = e

                    if self._should_auto_generate(e):
                        try:
                            impl = await self._auto_generate_http(unit_id)
                            if inspect.iscoroutinefunction(impl):
                                return await impl(*args, **kwargs)
                            return impl(*args, **kwargs)
                        except Exception as auto_exc:  # pragma: no cover - surfaced to caller
                            generation_error = auto_exc

                    result = func(*args, **kwargs)
                    if inspect.iscoroutine(result):
                        result = await result

                    doctest_hint = None
                    if isinstance(generation_error, VibesafeMissingDoctest):
                        doctest_hint = str(generation_error)
                    else:
                        with contextlib.suppress(Exception):
                            spec_meta = extract_spec(func)
                            if not spec_meta["doctests"]:
                                doctest_hint = f"Spec {unit_id} does not declare any doctests; add at least one example."

                    def _raise_http_uncompiled() -> None:
                        base_message = (
                            f"HTTP endpoint {unit_id} has not been compiled yet. "
                            f"Run 'vibesafe compile --target {unit_id}' first."
                        )
                        if doctest_hint:
                            base_message = f"{base_message} {doctest_hint}"
                        raise RuntimeError(base_message) from generation_error

                    if isinstance(result, VibesafeHandled) or result is Ellipsis or result is None:
                        _raise_http_uncompiled()

                    return result

            return wrapper  # type: ignore

        return decorator

    def get_registry(self) -> dict[str, dict[str, Any]]:
        """Get all registered vibesafe units."""
        return self._registry.copy()

    def get_unit(self, unit_id: str) -> dict[str, Any] | None:
        """Get metadata for a specific unit."""
        return self._registry.get(unit_id)

    @staticmethod
    def _in_interactive_session() -> bool:
        """Detect whether Python is running in an interactive REPL."""

        if hasattr(sys, "ps1"):
            return True
        flags = getattr(sys, "flags", None)
        if flags and getattr(flags, "interactive", 0):
            return True
        return os.environ.get("PYTHONINSPECT") == "1"

    def _should_auto_generate(self, exc: Exception) -> bool:
        """Return True if we should attempt on-the-fly generation."""

        from vibesafe.config import get_config
        from vibesafe.exceptions import VibesafeCheckpointMissing

        if not isinstance(exc, VibesafeCheckpointMissing):
            return False

        config = get_config()
        if self._in_interactive_session() and config.project.env != "dev":
            config.project = config.project.model_copy(update={"env": "dev"})

        return config.project.env != "prod" or self._in_interactive_session()

    def _auto_generate_and_load(self, unit_id: str) -> Callable[..., Any]:
        """Generate, test, and load an implementation for the unit."""

        from vibesafe.codegen import generate_for_unit
        from vibesafe.runtime import load_active, update_index, write_shim
        from vibesafe.testing import test_unit

        try:
            checkpoint_info = generate_for_unit(unit_id, force=False)
        except VibesafeMissingDoctest:
            checkpoint_info = generate_for_unit(
                unit_id,
                force=False,
                allow_missing_doctest=True,
            )
        update_index(
            unit_id,
            checkpoint_info["spec_hash"],
            created=checkpoint_info.get("created_at"),
        )
        write_shim(unit_id)

        test_result = test_unit(unit_id)
        if not test_result:
            errors = "; ".join(test_result.errors) if test_result.errors else "tests failed"
            raise RuntimeError(
                f"Generated implementation for {unit_id} failed verification: {errors}"
            )

        return load_active(unit_id)

    async def _auto_generate_http(self, unit_id: str) -> Callable[..., Any]:
        """Auto-generate helper for HTTP endpoints (async aware)."""

        impl = self._auto_generate_and_load(unit_id)
        if inspect.iscoroutinefunction(impl):
            return impl

        async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return impl(*args, **kwargs)

        return _async_wrapper


# Global instance
vibesafe = VibesafeDecorator()
