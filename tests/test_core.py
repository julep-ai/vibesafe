"""Tests for vibesafe.core module."""

from pathlib import Path
from typing import Any

import pytest

from vibesafe import VibesafeHandled, vibesafe
from vibesafe.core import VibesafeDecorator
from vibesafe.testing import TestResult


class TestVibesafeHandled:
    """Tests for VibesafeHandled sentinel."""

    def test_defless_handled_repr(self):
        """Test VibesafeHandled representation."""
        handled = VibesafeHandled()
        assert repr(handled) == "VibesafeHandled()"

    def test_defless_handled_is_unique_instance(self):
        """Test that each VibesafeHandled is a separate instance."""
        h1 = VibesafeHandled()
        h2 = VibesafeHandled()
        assert type(h1) == type(h2)
        assert h1 is not h2


class TestVibesafeDecorator:
    """Tests for VibesafeDecorator class."""

    def test_decorator_initialization(self):
        """Test that decorator initializes with empty registry."""
        decorator = VibesafeDecorator()
        assert decorator._registry == {}

    def test_module_exposes_func_alias(self):
        """Importing vibesafe package exposes .func convenience alias."""
        import importlib

        vibesafe_module = importlib.import_module("vibesafe")

        assert hasattr(vibesafe_module, "func")
        assert hasattr(vibesafe_module, "http")

        @vibesafe_module.func
        def alias_spec(x: int) -> int:
            return x

        assert alias_spec.__vibesafe_type__ == "function"

    def test_func_decorator_basic(self, clear_defless_registry):
        """Test basic function decoration."""

        @vibesafe.func
        def test_func(x: int) -> int:
            """Test function."""
            yield VibesafeHandled()

        assert hasattr(test_func, "__vibesafe_unit_id__")
        assert hasattr(test_func, "__vibesafe_type__")
        assert test_func.__vibesafe_type__ == "function"

    def test_func_decorator_registers_unit(self, clear_defless_registry):
        """Test that decoration registers the unit."""

        @vibesafe.func
        def another_func(a: str) -> str:
            """Another test."""
            yield VibesafeHandled()

        registry = vibesafe.get_registry()
        assert len(registry) >= 1
        unit_id = another_func.__vibesafe_unit_id__
        assert unit_id in registry
        assert registry[unit_id]["type"] == "function"

    def test_func_decorator_with_params(self, clear_defless_registry):
        """Test function decorator with parameters."""

        @vibesafe.func(provider="custom", template="custom.j2")
        def param_func(x: int) -> int:
            """With params."""
            yield VibesafeHandled()

        assert param_func.__vibesafe_provider__ == "custom"
        assert param_func.__vibesafe_template__ == "custom.j2"

    def test_http_decorator_basic(self, clear_defless_registry):
        """Test HTTP endpoint decoration."""

        @vibesafe.http(method="POST", path="/test")
        async def test_endpoint(x: int) -> dict[str, int]:
            """Test endpoint."""
            return VibesafeHandled()

        assert hasattr(test_endpoint, "__vibesafe_unit_id__")
        assert test_endpoint.__vibesafe_type__ == "http"
        assert test_endpoint.__vibesafe_method__ == "POST"
        assert test_endpoint.__vibesafe_path__ == "/test"

    def test_http_decorator_registers_unit(self, clear_defless_registry):
        """Test HTTP decoration registers unit."""

        @vibesafe.http(method="GET", path="/hello")
        async def hello_endpoint(name: str) -> dict[str, str]:
            """Hello endpoint."""
            return VibesafeHandled()

        registry = vibesafe.get_registry()
        unit_id = hello_endpoint.__vibesafe_unit_id__
        assert unit_id in registry
        assert registry[unit_id]["type"] == "http"
        assert registry[unit_id]["method"] == "GET"
        assert registry[unit_id]["path"] == "/hello"

    def test_http_decorator_with_params(self, clear_defless_registry):
        """Test HTTP decorator with custom params."""

        @vibesafe.http(
            method="PUT",
            path="/update",
            provider="custom",
            template="http_custom.j2",
        )
        async def update_endpoint(id: int, data: str) -> dict[str, Any]:
            """Update endpoint."""
            return VibesafeHandled()

        assert update_endpoint.__vibesafe_provider__ == "custom"
        assert update_endpoint.__vibesafe_template__ == "http_custom.j2"

    def test_func_decorator_raises_on_missing_checkpoint(self, clear_defless_registry, monkeypatch):
        """Test that calling uncompiled function raises error."""

        monkeypatch.setattr(
            VibesafeDecorator,
            "_should_auto_generate",
            lambda self, exc: False,
        )

        @vibesafe.func
        def uncompiled_func(x: int) -> int:
            """Not compiled."""
            yield VibesafeHandled()

        with pytest.raises(RuntimeError, match="has not been compiled yet"):
            uncompiled_func(5)

    def test_func_decorator_missing_boundary_marker(self, clear_defless_registry, monkeypatch):
        """Test that specs without VibesafeHandled sentinel raise helpfully."""

        monkeypatch.setattr(
            VibesafeDecorator,
            "_should_auto_generate",
            lambda self, exc: False,
        )

        @vibesafe.func
        def missing_marker(msg: str) -> str:
            """Spec missing the VibesafeHandled boundary."""
            return msg.upper()

        with pytest.raises(RuntimeError, match="VibesafeHandled"):
            missing_marker("moo")

    def test_pass_treated_as_boundary(self, clear_defless_registry, monkeypatch):
        """`pass` placeholders are treated like VibesafeHandled."""

        monkeypatch.setattr(
            VibesafeDecorator,
            "_should_auto_generate",
            lambda self, exc: False,
        )

        @vibesafe.func
        def pass_spec(msg: str) -> str:
            """Placeholder using pass."""
            pass

        with pytest.raises(RuntimeError) as exc_info:
            pass_spec("moo")

        assert "Specs must yield" not in str(exc_info.value)

    def test_ellipsis_treated_as_boundary(self, clear_defless_registry, monkeypatch):
        """`return ...` placeholders are treated like VibesafeHandled."""

        monkeypatch.setattr(
            VibesafeDecorator,
            "_should_auto_generate",
            lambda self, exc: False,
        )

        @vibesafe.func
        def ellipsis_spec(msg: str) -> str:
            """Placeholder using ellipsis."""
            return ...

        with pytest.raises(RuntimeError) as exc_info:
            ellipsis_spec("moo")

        assert "Specs must yield" not in str(exc_info.value)

    def test_auto_generate_invoked_in_dev_mode(self, clear_defless_registry, monkeypatch):
        """Dev mode triggers auto-generation before raising."""

        calls: dict[str, int] = {"count": 0}

        def fake_auto(self, unit_id: str, spec_meta: dict[str, Any]):
            calls["count"] += 1

            def impl(msg: str) -> str:
                return f"generated:{msg}"

            return impl

        monkeypatch.setattr(VibesafeDecorator, "_auto_generate_and_load", fake_auto)

        @vibesafe.func
        def auto_spec(msg: str) -> str:
            """Docstring with doctest.

            >>> auto_spec("x")
            'X'
            """

            return VibesafeHandled()

        result = auto_spec("moo")
        assert result == "generated:moo"
        assert calls["count"] == 1

    @pytest.mark.asyncio
    async def test_http_auto_generate_invoked(self, clear_defless_registry, monkeypatch):
        """Auto-generation also applies to HTTP endpoints."""

        async def fake_http_impl(name: str) -> dict[str, str]:
            return {"message": f"hi {name}"}

        async def fake_auto_http(self, unit_id: str, spec_meta: dict[str, Any]):
            return fake_http_impl

        monkeypatch.setattr(VibesafeDecorator, "_auto_generate_http", fake_auto_http)

        @vibesafe.http(method="GET", path="/hi")
        async def http_spec(name: str) -> dict[str, str]:
            """Docstring with doctest.

            >>> import anyio
            >>> anyio.run(lambda: http_spec("d"))
            {'message': 'HI D'}
            """

            return VibesafeHandled()

        response = await http_spec("moo")
        assert response == {"message": "hi moo"}

    def test_spec_extractor_handles_missing_source(self, clear_defless_registry, monkeypatch):
        """Specs defined in REPL-like contexts fall back to synthesized source."""

        def _raise_getsource(func):  # pragma: no cover - exercised via test
            raise OSError("no source")

        monkeypatch.setattr("vibesafe.ast_parser.inspect.getsource", _raise_getsource)

        @vibesafe.func
        def interactive_spec(x: int) -> int:
            """Docstring required for REPL specs.

            >>> interactive_spec(1)
            1
            """

            yield VibesafeHandled()

        from vibesafe.ast_parser import extract_spec

        unit_id = interactive_spec.__vibesafe_unit_id__
        stored_func = vibesafe.get_unit(unit_id)["func"]
        spec = extract_spec(stored_func)
        assert spec["signature"].startswith("def interactive_spec")
        assert spec["docstring"].startswith("Docstring required")
        assert spec["body_before_handled"] == ""

    def test_auto_generate_allows_missing_doctest(self, clear_defless_registry, monkeypatch):
        """Interactive auto-generation bypasses doctest requirement."""

        from vibesafe.exceptions import VibesafeCheckpointMissing
        from vibesafe.testing import TestResult

        generate_calls: list[tuple[bool, str | None]] = []

        def fake_generate(
            unit_id: str,
            force: bool = False,
            allow_missing_doctest: bool = False,
            feedback: str | None = None,
        ):
            generate_calls.append((allow_missing_doctest, feedback))
            if not allow_missing_doctest:
                from vibesafe.exceptions import VibesafeMissingDoctest

                raise VibesafeMissingDoctest("needs doctest")
            return {
                "spec_hash": "abc123",
                "chk_hash": "def456",
                "prompt_hash": "ghi789",
                "checkpoint_dir": Path("/tmp"),
                "impl_path": Path("/tmp/impl.py"),
                "meta_path": Path("/tmp/meta.toml"),
                "created_at": "now",
            }

        monkeypatch.setattr("vibesafe.codegen.generate_for_unit", fake_generate)
        monkeypatch.setattr("vibesafe.runtime.update_index", lambda *a, **k: None)
        monkeypatch.setattr("vibesafe.runtime.write_shim", lambda unit_id: Path("/tmp/shim.py"))

        def fake_load_active(unit_id: str, verify_hash: bool = True, **kwargs):
            if not generate_calls:
                raise VibesafeCheckpointMissing("missing")
            return lambda msg: f"generated:{msg}"

        monkeypatch.setattr("vibesafe.runtime.load_active", fake_load_active)
        monkeypatch.setattr(
            "vibesafe.testing.test_unit",
            lambda unit_id: TestResult(passed=True, total=0),
        )
        monkeypatch.setattr(VibesafeDecorator, "_should_auto_generate", lambda self, exc: True)
        monkeypatch.setattr(VibesafeDecorator, "_in_interactive_session", lambda self: True)

        @vibesafe.func
        def repl_func(msg: str) -> str:
            return VibesafeHandled()

        result = repl_func("moo")
        assert result == "generated:moo"
        assert generate_calls == [(False, None), (True, None)]

    def test_auto_generate_on_hash_mismatch(self, clear_defless_registry, monkeypatch):
        """Hash mismatches should trigger auto-generation in interactive mode."""

        from vibesafe.exceptions import VibesafeHashMismatch
        from vibesafe.testing import TestResult

        generate_calls: list[tuple[bool, str | None]] = []

        def fake_generate(
            unit_id: str,
            force: bool = False,
            allow_missing_doctest: bool = False,
            feedback: str | None = None,
        ):
            generate_calls.append((force, feedback))
            return {
                "spec_hash": "freshhash",
                "chk_hash": "def456",
                "prompt_hash": "ghi789",
                "checkpoint_dir": Path("/tmp"),
                "impl_path": Path("/tmp/impl.py"),
                "meta_path": Path("/tmp/meta.toml"),
                "created_at": "now",
            }

        monkeypatch.setattr("vibesafe.codegen.generate_for_unit", fake_generate)
        monkeypatch.setattr("vibesafe.runtime.update_index", lambda *a, **k: None)
        monkeypatch.setattr("vibesafe.runtime.write_shim", lambda unit_id: Path("/tmp/shim.py"))

        def fake_load_active(unit_id: str, verify_hash: bool = True, **kwargs):
            # First call raises mismatch to trigger auto-generate, second returns shim.
            if not generate_calls:
                raise VibesafeHashMismatch("mismatch")
            return lambda msg: f"regen:{msg}"

        monkeypatch.setattr("vibesafe.runtime.load_active", fake_load_active)
        monkeypatch.setattr(
            "vibesafe.testing.test_unit",
            lambda unit_id: TestResult(passed=True, total=0),
        )
        monkeypatch.setattr(VibesafeDecorator, "_should_auto_generate", lambda self, exc: True)
        monkeypatch.setattr(VibesafeDecorator, "_in_interactive_session", lambda self: True)

        @vibesafe.func
        def repl_func(msg: str) -> str:
            return VibesafeHandled()

        result = repl_func("boo")
        assert result == "regen:boo"
        assert generate_calls == [(False, None)]

    def test_auto_generate_retries_with_feedback(self, clear_defless_registry, monkeypatch):
        """Quality gate failures feed back into a second generation attempt."""

        from vibesafe.exceptions import VibesafeCheckpointMissing
        from vibesafe.testing import TestResult

        generate_log: list[tuple[bool, bool, str | None]] = []

        def fake_generate(
            unit_id: str,
            force: bool = False,
            allow_missing_doctest: bool = False,
            feedback: str | None = None,
        ) -> dict[str, Any]:
            generate_log.append((force, allow_missing_doctest, feedback))
            return {
                "spec_hash": "spec123" if not force else "spec456",
                "chk_hash": "chk124",
                "prompt_hash": "prompt",
                "checkpoint_dir": Path("/tmp"),
                "impl_path": Path("/tmp/impl.py"),
                "meta_path": Path("/tmp/meta.toml"),
                "created_at": "now",
            }

        test_runs: list[str] = []

        def fake_test_unit(unit_id: str) -> TestResult:
            test_runs.append(unit_id)
            if len(test_runs) == 1:
                return TestResult(
                    passed=False,
                    failures=1,
                    total=1,
                    errors=["ruff failed: ARG001 Unused function argument: `msg`"],
                )
            return TestResult(passed=True, total=1)

        load_calls: list[tuple[str, str | None]] = []

        def fake_load_active(
            unit_id: str,
            *,
            expected_spec_hash: str | None = None,
            verify_hash: bool = True,
        ):
            load_calls.append((unit_id, expected_spec_hash))
            if len(load_calls) == 1:
                raise VibesafeCheckpointMissing("missing")
            return lambda msg: f"ok:{msg}"

        monkeypatch.setattr("vibesafe.codegen.generate_for_unit", fake_generate)
        monkeypatch.setattr("vibesafe.runtime.load_active", fake_load_active)
        monkeypatch.setattr("vibesafe.runtime.update_index", lambda *a, **k: None)
        monkeypatch.setattr("vibesafe.runtime.write_shim", lambda unit_id: Path("/tmp/shim.py"))
        monkeypatch.setattr("vibesafe.testing.test_unit", fake_test_unit)
        monkeypatch.setattr(VibesafeDecorator, "_should_auto_generate", lambda self, exc: True)
        monkeypatch.setattr(VibesafeDecorator, "_in_interactive_session", lambda self: True)

        @vibesafe.func
        def flaky(msg: str) -> str:
            """Has doctest.

            >>> flaky("hi")
            'ok:hi'
            """

            yield VibesafeHandled()

        assert flaky("hi") == "ok:hi"
        assert generate_log == [
            (False, False, None),
            (True, False, "ruff failed: ARG001 Unused function argument: `msg`"),
        ]
        assert len(test_runs) == 2
        assert len(load_calls) == 2

    def test_cowsay_fallback_without_api_key(self, clear_defless_registry, monkeypatch):
        """Missing API key falls back to inline cowsay implementation."""

        def raise_no_key(*args, **kwargs):
            raise ValueError("API key not found in environment variable: OPENAI_API_KEY")

        monkeypatch.setattr("vibesafe.codegen.generate_for_unit", raise_no_key)
        monkeypatch.setattr("vibesafe.runtime.update_index", lambda *a, **k: None)
        monkeypatch.setattr("vibesafe.runtime.write_shim", lambda unit_id: None)
        monkeypatch.setattr(
            "vibesafe.testing.test_unit", lambda unit_id: TestResult(passed=True, total=0)
        )
        monkeypatch.setattr(VibesafeDecorator, "_should_auto_generate", lambda self, exc: True)
        monkeypatch.setattr(VibesafeDecorator, "_in_interactive_session", lambda self: True)

        @vibesafe.func
        def cowsayonlyboo(msg: str) -> str:
            """A variant of cowsay that only says boo and ignores the input"""

            return VibesafeHandled()

        art = cowsayonlyboo("moo")
        assert "^__^" in art
        assert "(oo)\\_______" in art

    def test_missing_doctest_hint_in_error(self, clear_defless_registry, monkeypatch):
        """Runtime error mentions missing doctest when auto generation fails."""

        monkeypatch.setattr(
            VibesafeDecorator,
            "_should_auto_generate",
            lambda self, exc: False,
        )

        @vibesafe.func
        def missing_doc(msg: str) -> str:
            """No doctest present."""
            return VibesafeHandled()

        with pytest.raises(RuntimeError) as exc_info:
            missing_doc("moo")

        assert "does not declare any doctests" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_decorator_raises_on_missing_checkpoint(
        self, clear_defless_registry, monkeypatch
    ):
        """Test that calling uncompiled endpoint raises error."""

        monkeypatch.setattr(
            VibesafeDecorator,
            "_should_auto_generate",
            lambda self, exc: False,
        )

        @vibesafe.http(method="GET", path="/test")
        async def uncompiled_endpoint(x: int) -> dict[str, int]:
            """Not compiled."""
            return VibesafeHandled()

        with pytest.raises(RuntimeError, match="has not been compiled yet"):
            await uncompiled_endpoint(5)

    def test_get_registry(self, clear_defless_registry):
        """Test get_registry returns copy of registry."""

        @vibesafe.func
        def func1(x: int) -> int:
            yield VibesafeHandled()

        @vibesafe.func
        def func2(y: str) -> str:
            yield VibesafeHandled()

        registry = vibesafe.get_registry()
        assert len(registry) == 2

        # Modifying returned registry shouldn't affect internal
        registry.clear()
        assert len(vibesafe.get_registry()) == 2

    def test_get_unit(self, clear_defless_registry):
        """Test get_unit retrieves specific unit metadata."""

        @vibesafe.func
        def specific_func(x: int) -> int:
            """Specific."""
            yield VibesafeHandled()

        unit_id = specific_func.__vibesafe_unit_id__
        unit_meta = vibesafe.get_unit(unit_id)

        assert unit_meta is not None
        assert unit_meta["type"] == "function"
        # qualname includes full path for nested functions
        assert unit_meta["qualname"].endswith("specific_func")

    def test_get_unit_nonexistent(self, clear_defless_registry):
        """Test get_unit returns None for nonexistent unit."""
        result = vibesafe.get_unit("nonexistent/unit")
        assert result is None

    def test_func_preserves_function_metadata(self, clear_defless_registry):
        """Test that decorator preserves function name and docstring."""

        @vibesafe.func
        def my_func(x: int, y: int) -> int:
            """This is my function."""
            yield VibesafeHandled()

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "This is my function."

    @pytest.mark.asyncio
    async def test_http_preserves_function_metadata(self, clear_defless_registry):
        """Test HTTP decorator preserves function metadata."""

        @vibesafe.http(method="POST", path="/endpoint")
        async def my_endpoint(data: str) -> dict[str, str]:
            """Endpoint docstring."""
            return VibesafeHandled()

        assert my_endpoint.__name__ == "my_endpoint"
        assert my_endpoint.__doc__ == "Endpoint docstring."

    def test_multiple_functions_in_same_module(self, clear_defless_registry):
        """Test multiple functions can be decorated in same module."""

        @vibesafe.func
        def func_a(x: int) -> int:
            yield VibesafeHandled()

        @vibesafe.func
        def func_b(x: str) -> str:
            yield VibesafeHandled()

        @vibesafe.func
        def func_c(x: float) -> float:
            yield VibesafeHandled()

        registry = vibesafe.get_registry()
        assert len(registry) >= 3
