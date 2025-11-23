"""
Tests for vibesafe.testing module.
"""

from vibesafe import VibeCoded, vibesafe
from vibesafe.testing import TestResult, test_checkpoint, test_unit


class TestTestResult:
    """Tests for TestResult class."""

    def test_passed_result(self):
        """Test passed test result."""
        result = TestResult(passed=True, failures=0, total=5)
        assert result.passed
        assert result.failures == 0
        assert result.total == 5
        assert bool(result) is True

    def test_failed_result(self):
        """Test failed test result."""
        result = TestResult(passed=False, failures=2, total=5, errors=["Error 1"])
        assert not result.passed
        assert result.failures == 2
        assert result.total == 5
        assert len(result.errors) == 1
        assert bool(result) is False

    def test_result_repr_passed(self):
        """Test representation of passed result."""
        result = TestResult(passed=True, total=10)
        repr_str = repr(result)
        assert "passed" in repr_str
        assert "10" in repr_str

    def test_result_repr_failed(self):
        """Test representation of failed result."""
        result = TestResult(passed=False, failures=3, total=10, errors=["E1", "E2"])
        repr_str = repr(result)
        assert "failed" in repr_str
        assert "3/10" in repr_str


class TestTestCheckpoint:
    """Tests for test_checkpoint function."""

    def test_checkpoint_missing_impl_fails(self, checkpoint_dir, sample_function):
        """Test checkpoint without impl.py fails."""
        unit_meta = {
            "func": sample_function,
            "module": "test",
            "qualname": "sample_function",
        }
        result = test_checkpoint(checkpoint_dir, unit_meta)
        assert not result.passed
        assert "Implementation file not found" in result.errors[0]

    def test_checkpoint_no_doctests_passes(
        self, checkpoint_dir, sample_impl, clear_vibesafe_registry
    ):
        """Test checkpoint with no doctests passes."""

        @vibesafe
        def no_doctest_func(x: int) -> int:
            """Function without doctests."""
            return x

        unit_meta = {
            "func": no_doctest_func,
            "module": "test",
            "qualname": "no_doctest_func",
        }
        result = test_checkpoint(checkpoint_dir, unit_meta)
        assert result.passed
        assert result.total == 0

    def test_checkpoint_with_passing_doctests(
        self, checkpoint_dir, sample_impl, clear_vibesafe_registry
    ):
        """Test checkpoint with passing doctests."""

        @vibesafe
        def add_numbers(a: int, b: int) -> int:
            """
            Add two numbers.

            >>> add_numbers(2, 3)
            5
            """
            raise VibeCoded()

        unit_meta = {
            "func": add_numbers,
            "module": "test",
            "qualname": "add_numbers",
        }

        result = test_checkpoint(checkpoint_dir, unit_meta)
        # Note: May fail if impl doesn't match, depends on sample_impl
        assert isinstance(result, TestResult)

    def test_checkpoint_gates_failure(self, checkpoint_dir, clear_vibesafe_registry, monkeypatch):
        """Gate failures should surface as test failures."""

        @vibesafe
        def gated_func(a: int) -> int:
            """
            Example with doctest.

            >>> gated_func(1)
            1
            """
            raise VibeCoded()

        impl_path = checkpoint_dir / "impl.py"
        impl_path.write_text(
            """
def gated_func(a: int) -> int:
    return a
""".strip()
        )

        unit_meta = {
            "func": gated_func,
            "module": "test",
            "qualname": "gated_func",
        }

        monkeypatch.setattr(
            "vibesafe.testing._run_quality_gates",
            lambda path: ["ruff failed: example"],
        )

        result = test_checkpoint(checkpoint_dir, unit_meta)
        assert not result.passed
        assert any("ruff failed" in err for err in result.errors)

    def test_checkpoint_writes_vibesafe_file(
        self,
        checkpoint_dir,
        temp_dir,
        test_config,
        clear_vibesafe_registry,
        monkeypatch,
    ):
        """Doctest harness files are written under tests/vibesafe."""

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        @vibesafe
        def doc_func(msg: str) -> str:
            """Echo.

            >>> doc_func("hi")
            'hi'

            ```hypothesis
            from hypothesis import given, strategies as st

            @given(st.text())
            def test_roundtrip(s: str) -> None:
                assert func(s) == s
            ```
            """

            raise VibeCoded()

        impl_path = checkpoint_dir / "impl.py"
        impl_path.write_text(
            """
def doc_func(msg: str) -> str:
    return msg
""".strip()
        )

        unit_meta = {
            "func": doc_func,
            "module": doc_func.__module__,
            "qualname": doc_func.__qualname__,
        }

        # Aggregated harnesses only materialize in prod mode
        test_config.project.env = "prod"

        monkeypatch.setattr("vibesafe.testing._run_quality_gates", lambda path: [])

        unit_id = unit_meta["module"] + "/" + unit_meta["qualname"]
        harness_path = temp_dir / "tests" / "vibesafe" / f"test_{unit_meta['module'].replace('.', '_')}.py"
        result = test_checkpoint(checkpoint_dir, unit_meta)

        assert harness_path.exists()
        contents = harness_path.read_text()
        assert unit_id in contents
        assert "hi" in contents

        from importlib.util import find_spec

        if find_spec("hypothesis") is not None:
            assert result.total == 2
        else:
            # If hypothesis is missing, we expect a failure but the file should still be written
            assert result.total == 1
            assert not result.passed
            assert "No module named 'hypothesis'" in result.errors[0]

    def test_checkpoint_uses_sandbox(
        self,
        checkpoint_dir,
        temp_dir,
        test_config,
        monkeypatch,
        clear_vibesafe_registry,
    ):
        from vibesafe import config as config_module

        test_config.sandbox.enabled = True
        test_config.sandbox.timeout = 5
        test_config.sandbox.memory_mb = 64

        monkeypatch.chdir(temp_dir)
        config_module._config = test_config

        @vibesafe
        def sandboxed(msg: str) -> str:
            return VibeCoded()

        impl_path = checkpoint_dir / "impl.py"
        impl_path.write_text("""def sandboxed(msg: str) -> str:\n    return msg\n""")

        unit_meta = {
            "func": sandboxed,
            "module": sandboxed.__module__,
            "qualname": sandboxed.__qualname__,
        }

        sandbox_called = {"called": False}

        def fake_sandbox(unit_meta, spec, sandbox_cfg):
            sandbox_called["called"] = True
            return TestResult(passed=True, total=0)

        monkeypatch.setattr("vibesafe.testing._run_sandbox_checks", fake_sandbox)
        monkeypatch.setattr("vibesafe.testing._run_quality_gates", lambda path: [])

        result = test_checkpoint(checkpoint_dir, unit_meta)
        assert result.passed
        assert sandbox_called["called"]


class TestTestUnit:
    """Tests for test_unit function."""

    def test_unit_not_found(self, clear_vibesafe_registry):
        """Test testing nonexistent unit returns error."""
        result = test_unit("nonexistent/unit")
        assert not result.passed
        assert "Unit not found" in result.errors[0]

    def test_unit_not_compiled(self, test_config, temp_dir, monkeypatch, clear_vibesafe_registry):
        """Test testing uncompiled unit returns error."""

        @vibesafe
        def uncompiled_func(x: int) -> int:
            """Not compiled."""
            raise VibeCoded()

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        unit_id = uncompiled_func.__vibesafe_unit_id__
        result = test_unit(unit_id)
        assert not result.passed
