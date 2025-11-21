"""Core decorators and sentinel types for vibesafe."""

import contextlib
import functools
import inspect
import os
import sys
import warnings
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast, overload

from vibesafe.ast_parser import extract_spec
from vibesafe.config import get_config, resolve_template_id
from vibesafe.exceptions import VibesafeMissingDoctest

P = ParamSpec("P")
R = TypeVar("R")


class VibeCoded(BaseException):
    """
    Sentinel exception marking where the spec ends and AI-generated code should begin.

    Usage:
        @vibesafe
        def my_func(x: int) -> int:
            '''Add 1 to x'''
            raise VibeCoded()
    """

    def __repr__(self) -> str:
        return "VibeCoded()"


# Global registry
_registry: dict[str, dict[str, Any]] = {}


@overload
def vibesafe[**P, R](
    fn: Callable[P, R],
    *,
    kind: str | None = None,
    provider: str | None = None,
    template: str | None = None,
    **kwargs: Any,
) -> Callable[P, R]: ...


@overload
def vibesafe(
    fn: None = None,
    *,
    kind: str | None = None,
    provider: str | None = None,
    template: str | None = None,
    **kwargs: Any,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def vibesafe[**P, R](
    fn: Callable[P, R] | None = None,
    *,
    kind: str | None = None,
    provider: str | None = None,
    template: str | None = None,
    **kwargs: Any,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Unified decorator for Vibesafe specs.

    Can be used as:
        @vibesafe
        def foo(): ...

    Or with args:
        @vibesafe(kind="http")
        def foo(): ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # Get module and qualname
        func_obj = cast(Any, func)
        module = func_obj.__module__
        qualname = func_obj.__qualname__
        unit_id = f"{module}/{qualname}"

        # Store metadata
        _registry[unit_id] = {
            "func": func,
            "kind": kind,
            "provider": provider,
            "template": template,
            "module": module,
            "qualname": qualname,
            **kwargs,
        }

        # Mark the function
        func.__vibesafe_unit_id__ = unit_id  # type: ignore
        func.__vibesafe_kind__ = kind  # type: ignore
        func.__vibesafe_provider__ = provider  # type: ignore
        func.__vibesafe_template__ = template  # type: ignore
        for key, value in kwargs.items():
            setattr(func, f"__vibesafe_{key}__", value)

        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                return await _handle_execution(unit_id, func, args, kwargs, is_async=True)

            return cast(Callable[P, R], async_wrapper)
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                return _handle_execution(unit_id, func, args, kwargs, is_async=False)

            return cast(Callable[P, R], sync_wrapper)

    if fn is None:
        return decorator
    return decorator(fn)


def get_registry() -> dict[str, dict[str, Any]]:
    """Get all registered vibesafe units."""
    return _registry.copy()


def get_unit(unit_id: str) -> dict[str, Any] | None:
    """Get metadata for a specific unit."""
    return _registry.get(unit_id)


def _handle_execution(
    unit_id: str,
    original_func: Callable,
    args: tuple,
    kwargs: dict,
    is_async: bool,
) -> Any:
    """
    Common execution logic for loading/generating/running implementations.
    Returns Awaitable if is_async=True, else returns result directly.
    """
    from vibesafe.runtime import load_checkpoint

    spec_meta = extract_spec(original_func)
    expected_spec_hash = _compute_spec_hash(unit_id, spec_meta)

    async def _run_async_impl(impl: Callable) -> Any:
        if inspect.iscoroutinefunction(impl):
            return await impl(*args, **kwargs)
        return impl(*args, **kwargs)

    def _run_sync_impl(impl: Callable) -> Any:
        if inspect.iscoroutinefunction(impl):
            raise RuntimeError(f"Unit {unit_id} is sync, but generated implementation is async.")
        return impl(*args, **kwargs)

    # 1. Try to load and run
    try:
        impl = load_checkpoint(unit_id, expected_spec_hash=expected_spec_hash)
        if is_async:
            return _run_async_impl(impl)
        return _run_sync_impl(impl)
    except Exception as e:
        generation_error: Exception | None = e

        # 2. Auto-generate if allowed
        if _should_auto_generate(e):
            try:
                impl = _auto_generate_and_load(unit_id, spec_meta)
                if is_async:
                    return _run_async_impl(impl)
                return _run_sync_impl(impl)
            except Exception as auto_exc:
                generation_error = auto_exc

        # 3. Fallback to original function (which should raise VibeCoded)
        if is_async:
            return _handle_fallback_async(
                original_func, args, kwargs, unit_id, spec_meta, generation_error
            )
        return _handle_fallback_sync(
            original_func, args, kwargs, unit_id, spec_meta, generation_error
        )


async def _handle_fallback_async(func, args, kwargs, unit_id, spec_meta, error):
    try:
        await func(*args, **kwargs)
    except VibeCoded:
        _raise_uncompiled(unit_id, spec_meta, error)

    # If we get here, the function didn't raise VibeCoded
    _raise_uncompiled(unit_id, spec_meta, error, "Specs must raise `VibeCoded()`")


def _handle_fallback_sync(func, args, kwargs, unit_id, spec_meta, error):
    try:
        func(*args, **kwargs)
    except VibeCoded:
        _raise_uncompiled(unit_id, spec_meta, error)

    # If we get here, the function didn't raise VibeCoded
    _raise_uncompiled(unit_id, spec_meta, error, "Specs must raise `VibeCoded()`")


def _raise_uncompiled(unit_id, spec_meta, error, extra_hint=None):
    doctest_hint = None
    if isinstance(error, VibesafeMissingDoctest):
        doctest_hint = str(error)
    else:
        with contextlib.suppress(Exception):
            if not spec_meta["doctests"]:
                doctest_hint = (
                    f"Spec {unit_id} does not declare any doctests; add at least one example."
                )

    error_message = str(error) if error else None
    config_env = get_config().project.env
    doctest_notice = doctest_hint

    if doctest_hint and config_env != "prod":
        warnings.warn(doctest_hint, RuntimeWarning, stacklevel=3)

    base_message = (
        f"Function {unit_id} has not been compiled yet. "
        f"Run 'vibesafe compile --target {unit_id}' first."
    )
    hints = [extra_hint, doctest_notice, error_message]
    merged = ". ".join(h for h in hints if h)
    if merged:
        base_message = f"{base_message} {merged}"

    raise RuntimeError(base_message) from error


def _in_interactive_session() -> bool:
    """Detect whether Python is running in an interactive REPL."""
    if hasattr(sys, "ps1"):
        return True
    flags = getattr(sys, "flags", None)
    if flags and getattr(flags, "interactive", 0):
        return True
    return os.environ.get("PYTHONINSPECT") == "1"


def _should_auto_generate(exc: Exception) -> bool:
    """Return True if we should attempt on-the-fly generation."""
    from vibesafe.exceptions import VibesafeCheckpointMissing, VibesafeHashMismatch

    if not isinstance(exc, (VibesafeCheckpointMissing, VibesafeHashMismatch)):
        return False

    config = get_config()
    if _in_interactive_session() and config.project.env != "dev":
        config.project = config.project.model_copy(update={"env": "dev"})

    return config.project.env != "prod" or _in_interactive_session()


def _compute_spec_hash(unit_id: str, spec_meta: dict[str, Any]) -> str:
    """Compute the current spec hash for a registered unit."""
    from vibesafe.hashing import compute_dependency_digest, compute_spec_hash

    unit_meta = _registry.get(unit_id)
    if unit_meta is None:
        raise RuntimeError(f"Unit not registered: {unit_id}")

    config = get_config()
    provider_name = unit_meta.get("provider") or "default"
    provider_config = config.get_provider(provider_name)
    template_id = resolve_template_id(unit_meta, config, spec_meta.get("type"))

    dependency_digest = compute_dependency_digest(spec_meta.get("dependencies", {}))
    provider_params = {
        "temperature": provider_config.temperature,
        "seed": provider_config.seed,
        "timeout": provider_config.timeout,
    }

    return compute_spec_hash(
        signature=spec_meta.get("signature", ""),
        docstring=spec_meta.get("docstring", ""),
        body_before_handled=spec_meta.get("body_before_handled", ""),
        template_id=template_id,
        provider_model=provider_config.model,
        provider_params=provider_params,
        dependency_digest=dependency_digest,
    )


def _auto_generate_and_load(unit_id: str, spec_meta: dict[str, Any]) -> Callable[..., Any]:
    """Generate, test, and load an implementation for the unit."""
    from vibesafe.codegen import generate_for_unit
    from vibesafe.runtime import load_checkpoint, update_index
    from vibesafe.testing import test_unit

    def _generate(force: bool, feedback: str | None = None) -> dict[str, Any]:
        return generate_for_unit(
            unit_id,
            force=force,
            allow_missing_doctest=False,
            feedback=feedback,
        )

    try:
        checkpoint_info = _generate(force=False)
    except VibesafeMissingDoctest:
        # Fallback logic for cowsay/boo example if needed, or just raise
        # For now, let's simplify and just raise unless interactive
        if _in_interactive_session():
            checkpoint_info = generate_for_unit(unit_id, force=False, allow_missing_doctest=True)
        else:
            raise
    except ValueError as exc:
        if "API key not found" in str(exc):
            warnings.warn(str(exc), RuntimeWarning, stacklevel=2)
            raise
        raise

    update_index(
        unit_id,
        checkpoint_info["spec_hash"],
        created=checkpoint_info.get("created_at"),
    )
    # No more write_shim(unit_id)

    test_result = test_unit(unit_id)
    if test_result:
        return load_checkpoint(unit_id)

    errors = test_result.errors or []

    if _in_interactive_session() and errors:
        feedback = "\n".join(errors)
        checkpoint_info = _generate(force=True, feedback=feedback)
        update_index(
            unit_id,
            checkpoint_info["spec_hash"],
            created=checkpoint_info.get("created_at"),
        )

        retry_result = test_unit(unit_id)
        if retry_result:
            return load_checkpoint(unit_id)
        errors = retry_result.errors or errors

    merged_errors = "; ".join(errors) if errors else "tests failed"
    raise RuntimeError(
        f"Generated implementation for {unit_id} failed verification: {merged_errors}"
    )
