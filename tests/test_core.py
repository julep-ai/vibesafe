"""Tests for vibesafe.core module."""

from pathlib import Path
from typing import Any

import pytest

import vibesafe.core as vibesafe_core
from vibesafe import VibeCoded, get_registry, get_unit, vibesafe
from vibesafe.testing import TestResult


class TestVibeCoded:
    """Tests for VibeCoded sentinel."""

    def test_vibesafe_handled_repr(self):
        """Test VibeCoded representation."""
        handled = VibeCoded()
        assert repr(handled) == "VibeCoded()"

    def test_vibesafe_handled_is_unique_instance(self):
        """Test that each VibeCoded is a separate instance."""
        h1 = VibeCoded()
        h2 = VibeCoded()
        assert type(h1) == type(h2)
        assert h1 is not h2


class TestVibesafeCore:
    """Tests for vibesafe core functionality."""

    def test_registry_initialization(self):
        """Test that registry starts empty (or we can clear it)."""
        # We can't easily assert it's empty globally, but we can check type
        registry = get_registry()
        assert isinstance(registry, dict)

    def test_module_exposes_aliases(self):
        """Importing vibesafe package exposes convenience aliases."""
        import importlib

        vibesafe_module = importlib.import_module("vibesafe")

        assert hasattr(vibesafe_module, "func")
        assert hasattr(vibesafe_module, "http")
        assert hasattr(vibesafe_module, "get_registry")
        assert hasattr(vibesafe_module, "get_unit")
        assert vibesafe_module.func is vibesafe_module.vibesafe
        assert vibesafe_module.http is vibesafe_module.vibesafe

    def test_func_decorator_basic(self, clear_vibesafe_registry):
        """Test basic function decoration."""

        @vibesafe
        def test_func(x: int) -> int:
            """Test function."""
            raise VibeCoded()

        assert hasattr(test_func, "__vibesafe_unit_id__")
        # kind is None by default for now until inference
        assert hasattr(test_func, "__vibesafe_kind__")

    def test_func_decorator_registers_unit(self, clear_vibesafe_registry):
        """Test that decoration registers the unit."""

        @vibesafe
        def another_func(a: str) -> str:
            """Another test."""
            raise VibeCoded()

        registry = get_registry()
        unit_id = another_func.__vibesafe_unit_id__
        assert unit_id in registry
        # The registry stores the original function, the decorator returns a wrapper
        assert registry[unit_id]["func"] is another_func.__wrapped__

    def test_func_decorator_with_params(self, clear_vibesafe_registry):
        """Test function decorator with parameters."""

        @vibesafe(provider="custom", template="custom.j2")
        def param_func(x: int) -> int:
            """With params."""
            raise VibeCoded()

        assert param_func.__vibesafe_provider__ == "custom"
        assert param_func.__vibesafe_template__ == "custom.j2"

    @pytest.mark.asyncio
    async def test_http_decorator_basic(self, clear_vibesafe_registry):
        """Test HTTP endpoint decoration (using explicit kind for now)."""

        @vibesafe(kind="http")
        async def test_endpoint(x: int) -> dict[str, int]:
            """Test endpoint."""
            return VibeCoded()

        assert hasattr(test_endpoint, "__vibesafe_unit_id__")
        assert test_endpoint.__vibesafe_kind__ == "http"

    def test_func_decorator_raises_on_missing_checkpoint(
        self, clear_vibesafe_registry, monkeypatch
    ):
        """Test that calling uncompiled function raises error."""

        monkeypatch.setattr(
            vibesafe_core,
            "_should_auto_generate",
            lambda exc: False,
        )

        @vibesafe
        def uncompiled_func(x: int) -> int:
            """Not compiled."""
            raise VibeCoded()

        with pytest.raises(RuntimeError, match="has not been compiled yet"):
            uncompiled_func(5)

    def test_func_decorator_missing_boundary_marker(self, clear_vibesafe_registry, monkeypatch):
        """Test that specs without VibeCoded sentinel raise helpfully."""

        monkeypatch.setattr(
            vibesafe_core,
            "_should_auto_generate",
            lambda exc: False,
        )

        @vibesafe
        def missing_marker(msg: str) -> str:
            """Spec missing the VibeCoded boundary."""
            return msg.upper()

        with pytest.raises(RuntimeError, match="VibeCoded"):
            missing_marker("moo")

    def test_pass_treated_as_boundary(self, clear_vibesafe_registry, monkeypatch):
        """`pass` placeholders are treated like VibeCoded."""

        monkeypatch.setattr(
            vibesafe_core,
            "_should_auto_generate",
            lambda exc: False,
        )

        @vibesafe
        def pass_spec(msg: str) -> str:
            """Placeholder using pass."""
            pass

        with pytest.raises(RuntimeError) as exc_info:
            pass_spec("moo")

        assert "Specs must yield" not in str(exc_info.value)

    def test_ellipsis_treated_as_boundary(self, clear_vibesafe_registry, monkeypatch):
        """`return ...` placeholders are treated like VibeCoded."""

        monkeypatch.setattr(
            vibesafe_core,
            "_should_auto_generate",
            lambda exc: False,
        )

        @vibesafe
        def ellipsis_spec(msg: str) -> str:
            """Placeholder using ellipsis."""
            return ...

        with pytest.raises(RuntimeError) as exc_info:
            ellipsis_spec("moo")

        assert "Specs must yield" not in str(exc_info.value)

    def test_auto_generate_invoked_in_dev_mode(self, clear_vibesafe_registry, monkeypatch):
        """Dev mode triggers auto-generation before raising."""

        calls: dict[str, int] = {"count": 0}

        def fake_auto(unit_id: str, spec_meta: dict[str, Any]):
            calls["count"] += 1

            def impl(msg: str) -> str:
                return f"generated:{msg}"

            return impl

        monkeypatch.setattr(vibesafe_core, "_auto_generate_and_load", fake_auto)
        monkeypatch.setattr(vibesafe_core, "_should_auto_generate", lambda exc: True)

        @vibesafe
        def auto_spec(msg: str) -> str:
            """Docstring with doctest.

            >>> auto_spec("x")
            'X'
            """

            return VibeCoded()

        result = auto_spec("moo")
        assert result == "generated:moo"
        assert calls["count"] == 1

    @pytest.mark.asyncio
    async def test_http_auto_generate_invoked(self, clear_vibesafe_registry, monkeypatch):
        """Auto-generation also applies to async endpoints."""

        async def fake_http_impl(name: str) -> dict[str, str]:
            return {"message": f"hi {name}"}

        def fake_auto(unit_id: str, spec_meta: dict[str, Any]):
            return fake_http_impl

        monkeypatch.setattr(vibesafe_core, "_auto_generate_and_load", fake_auto)
        monkeypatch.setattr(vibesafe_core, "_should_auto_generate", lambda exc: True)

        @vibesafe(kind="http")
        async def http_spec(name: str) -> dict[str, str]:
            """Docstring with doctest.

            >>> import anyio
            >>> anyio.run(lambda: http_spec("d"))
            {'message': 'HI D'}
            """

            return VibeCoded()

        response = await http_spec("moo")
        assert response == {"message": "hi moo"}

    def test_spec_extractor_handles_missing_source(self, clear_vibesafe_registry, monkeypatch):
        """Specs defined in REPL-like contexts fall back to synthesized source."""

        def _raise_getsource(func):  # pragma: no cover - exercised via test
            raise OSError("no source")

        monkeypatch.setattr("vibesafe.ast_parser.inspect.getsource", _raise_getsource)

        @vibesafe
        def interactive_spec(x: int) -> int:
            """Docstring required for REPL specs.

            >>> interactive_spec(1)
            1
            """

            raise VibeCoded()

        from vibesafe.ast_parser import extract_spec

        unit_id = interactive_spec.__vibesafe_unit_id__
        stored_func = get_unit(unit_id)["func"]
        spec = extract_spec(stored_func)
        assert spec["signature"].startswith("def interactive_spec")
        assert spec["docstring"].startswith("Docstring required")
        assert spec["body_before_handled"] == ""

    def test_auto_generate_allows_missing_doctest(self, clear_vibesafe_registry, monkeypatch):
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
        # load_checkpoint logic is mocked via _auto_generate_and_load usually, but here we mock lower levels
        # Actually _auto_generate_and_load calls generate_for_unit, update_index, test_unit, load_checkpoint

        # We need to mock load_checkpoint to fail first then succeed
        def fake_load_checkpoint(unit_id: str, verify_hash: bool = True, **kwargs):
            if not generate_calls:
                raise VibesafeCheckpointMissing("missing")
            return lambda msg: f"generated:{msg}"

        monkeypatch.setattr("vibesafe.runtime.load_checkpoint", fake_load_checkpoint)
        monkeypatch.setattr(
            "vibesafe.testing.test_unit",
            lambda unit_id: TestResult(passed=True, total=0),
        )
        monkeypatch.setattr(vibesafe_core, "_should_auto_generate", lambda exc: True)
        monkeypatch.setattr(vibesafe_core, "_in_interactive_session", lambda: True)

        @vibesafe
        def repl_func(msg: str) -> str:
            return VibeCoded()

        result = repl_func("moo")
        assert result == "generated:moo"
        assert generate_calls == [(False, None), (True, None)]

    def test_auto_generate_on_hash_mismatch(self, clear_vibesafe_registry, monkeypatch):
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

        def fake_load_checkpoint(unit_id: str, verify_hash: bool = True, **kwargs):
            # First call raises mismatch to trigger auto-generate, second returns impl.
            if not generate_calls:
                raise VibesafeHashMismatch("mismatch")
            return lambda msg: f"regen:{msg}"

        monkeypatch.setattr("vibesafe.runtime.load_checkpoint", fake_load_checkpoint)
        monkeypatch.setattr(
            "vibesafe.testing.test_unit",
            lambda unit_id: TestResult(passed=True, total=0),
        )
        monkeypatch.setattr(vibesafe_core, "_should_auto_generate", lambda exc: True)
        monkeypatch.setattr(vibesafe_core, "_in_interactive_session", lambda: True)

        @vibesafe
        def repl_func(msg: str) -> str:
            return VibeCoded()

        result = repl_func("boo")
        assert result == "regen:boo"
        assert generate_calls == [(False, None)]

    def test_auto_generate_retries_with_feedback(self, clear_vibesafe_registry, monkeypatch):
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

        def fake_load_checkpoint(
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
        monkeypatch.setattr("vibesafe.runtime.load_checkpoint", fake_load_checkpoint)
        monkeypatch.setattr("vibesafe.runtime.update_index", lambda *a, **k: None)
        monkeypatch.setattr("vibesafe.testing.test_unit", fake_test_unit)
        monkeypatch.setattr(vibesafe_core, "_should_auto_generate", lambda exc: True)
        monkeypatch.setattr(vibesafe_core, "_in_interactive_session", lambda: True)

        @vibesafe
        def flaky(msg: str) -> str:
            """Has doctest.

            >>> flaky("hi")
            'ok:hi'
            """

            raise VibeCoded()

        assert flaky("hi") == "ok:hi"
        assert generate_log == [
            (False, False, None),
            (True, False, "ruff failed: ARG001 Unused function argument: `msg`"),
        ]
        assert len(test_runs) == 2
        assert len(load_calls) == 2

    def test_cowsay_fallback_without_api_key(self, clear_vibesafe_registry, monkeypatch):
        """Missing API key falls back to inline cowsay implementation."""

        def raise_no_key(*args, **kwargs):
            raise ValueError("API key not found in environment variable: OPENAI_API_KEY")

        monkeypatch.setattr("vibesafe.codegen.generate_for_unit", raise_no_key)
        monkeypatch.setattr("vibesafe.runtime.update_index", lambda *a, **k: None)
        monkeypatch.setattr(
            "vibesafe.testing.test_unit", lambda unit_id: TestResult(passed=True, total=0)
        )
        monkeypatch.setattr(vibesafe_core, "_should_auto_generate", lambda exc: True)
        monkeypatch.setattr(vibesafe_core, "_in_interactive_session", lambda: True)

        @vibesafe
        def cowsayonlyboo(msg: str) -> str:
            """A variant of cowsay that only says boo and ignores the input"""

            return VibeCoded()

        with pytest.raises(RuntimeError) as exc_info:
            cowsayonlyboo("moo")

        assert "API key not found" in str(exc_info.value.__cause__)

    def test_missing_doctest_hint_in_error(self, clear_vibesafe_registry, monkeypatch):
        """Runtime error mentions missing doctest when auto generation fails."""

        monkeypatch.setattr(
            vibesafe_core,
            "_should_auto_generate",
            lambda exc: False,
        )

        @vibesafe
        def missing_doc(msg: str) -> str:
            """No doctest present."""
            return VibeCoded()

        with pytest.raises(RuntimeError) as exc_info:
            missing_doc("moo")

        assert "does not declare any doctests" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_decorator_raises_on_missing_checkpoint(
        self, clear_vibesafe_registry, monkeypatch
    ):
        """Test that calling uncompiled endpoint raises error."""

        monkeypatch.setattr(
            vibesafe_core,
            "_should_auto_generate",
            lambda exc: False,
        )

        @vibesafe(kind="http")
        async def uncompiled_endpoint(x: int) -> dict[str, int]:
            """Not compiled."""
            return VibeCoded()

        with pytest.raises(RuntimeError, match="has not been compiled yet"):
            await uncompiled_endpoint(5)

    def test_get_registry(self, clear_vibesafe_registry):
        """Test get_registry returns copy of registry."""

        @vibesafe
        def func1(x: int) -> int:
            raise VibeCoded()

        @vibesafe
        def func2(y: str) -> str:
            raise VibeCoded()

        registry = get_registry()
        assert len(registry) == 2

        # Modifying returned registry shouldn't affect internal
        registry.clear()
        assert len(get_registry()) == 2

    def test_get_unit(self, clear_vibesafe_registry):
        """Test get_unit retrieves specific unit metadata."""

        @vibesafe
        def specific_func(x: int) -> int:
            """Specific."""
            raise VibeCoded()

        unit_id = specific_func.__vibesafe_unit_id__
        unit_meta = get_unit(unit_id)

        assert unit_meta is not None
        # The registry stores the original function
        assert unit_meta["func"] is specific_func.__wrapped__
        # qualname includes full path for nested functions
        assert unit_meta["qualname"].endswith("specific_func")

    def test_get_unit_nonexistent(self, clear_vibesafe_registry):
        """Test get_unit returns None for nonexistent unit."""
        result = get_unit("nonexistent/unit")
        assert result is None

    def test_func_preserves_function_metadata(self, clear_vibesafe_registry):
        """Test that decorator preserves function name and docstring."""

        @vibesafe
        def my_func(x: int, y: int) -> int:
            """This is my function."""
            raise VibeCoded()

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "This is my function."

    @pytest.mark.asyncio
    async def test_http_preserves_function_metadata(self, clear_vibesafe_registry):
        """Test HTTP decorator preserves function metadata."""

        @vibesafe(kind="http")
        async def my_endpoint(data: str) -> dict[str, str]:
            """Endpoint docstring."""
            return VibeCoded()

        assert my_endpoint.__name__ == "my_endpoint"
        assert my_endpoint.__doc__ == "Endpoint docstring."

    def test_multiple_functions_in_same_module(self, clear_vibesafe_registry):
        """Test multiple functions can be decorated in same module."""

        @vibesafe
        def func_a(x: int) -> int:
            raise VibeCoded()

        @vibesafe
        def func_b(x: str) -> str:
            """Function B."""
            raise VibeCoded()

        @vibesafe
        def func_c(x: float) -> float:
            """Function C."""
            raise VibeCoded()

        registry = get_registry()
        assert len(registry) >= 3
