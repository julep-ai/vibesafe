"""
Core decorators and sentinel types for vibesafe.
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

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
            self._registry[unit_id] = {
                "type": "function",
                "func": func,
                "provider": provider,
                "template": template or "function.j2",
                "module": module,
                "qualname": qualname,
            }

            # Mark the function
            func.__vibesafe_unit_id__ = unit_id  # type: ignore
            func.__vibesafe_type__ = "function"  # type: ignore
            func.__vibesafe_provider__ = provider  # type: ignore
            func.__vibesafe_template__ = template or "function.j2"  # type: ignore

            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                # Import here to avoid circular dependency
                from vibesafe.runtime import load_active

                # Try to load generated implementation
                try:
                    impl = load_active(unit_id)
                    return impl(*args, **kwargs)
                except Exception as e:
                    # Fall back to original function (which should yield VibesafeHandled)
                    result = func(*args, **kwargs)
                    # Check if it's a generator that yielded VibesafeHandled
                    if inspect.isgenerator(result):
                        for item in result:
                            if isinstance(item, VibesafeHandled):
                                raise RuntimeError(
                                    f"Function {unit_id} has not been compiled yet. "
                                    f"Run 'vibesafe compile --target {unit_id}' first."
                                ) from e
                    return result

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
            self._registry[unit_id] = {
                "type": "http",
                "func": func,
                "method": method,
                "path": path,
                "provider": provider,
                "template": template or "http_endpoint.j2",
                "module": module,
                "qualname": qualname,
            }

            # Mark the function
            func.__vibesafe_unit_id__ = unit_id  # type: ignore
            func.__vibesafe_type__ = "http"  # type: ignore
            func.__vibesafe_method__ = method  # type: ignore
            func.__vibesafe_path__ = path  # type: ignore
            func.__vibesafe_provider__ = provider  # type: ignore
            func.__vibesafe_template__ = template or "http_endpoint.j2"  # type: ignore

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
                    # Fall back to original function
                    result = func(*args, **kwargs)
                    # Await if it's a coroutine
                    if inspect.iscoroutine(result):
                        result = await result
                    # Check if result is VibesafeHandled marker
                    if isinstance(result, VibesafeHandled):
                        raise RuntimeError(
                            f"HTTP endpoint {unit_id} has not been compiled yet. "
                            f"Run 'vibesafe compile --target {unit_id}' first."
                        ) from e
                    return result

            return wrapper  # type: ignore

        return decorator

    def get_registry(self) -> dict[str, dict[str, Any]]:
        """Get all registered vibesafe units."""
        return self._registry.copy()

    def get_unit(self, unit_id: str) -> dict[str, Any] | None:
        """Get metadata for a specific unit."""
        return self._registry.get(unit_id)


# Global instance
vibesafe = VibesafeDecorator()
