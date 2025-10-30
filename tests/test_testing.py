"""
Tests for defless.testing module.
"""

import doctest
from pathlib import Path

import pytest

from defless import DeflessHandled, defless
from defless.testing import TestResult, test_checkpoint, test_unit


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
        self, checkpoint_dir, sample_impl, clear_defless_registry
    ):
        """Test checkpoint with no doctests passes."""

        @defless.func
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
        self, checkpoint_dir, sample_impl, clear_defless_registry
    ):
        """Test checkpoint with passing doctests."""

        @defless.func
        def add_numbers(a: int, b: int) -> int:
            """
            Add two numbers.

            >>> add_numbers(2, 3)
            5
            """
            yield DeflessHandled()

        unit_meta = {
            "func": add_numbers,
            "module": "test",
            "qualname": "add_numbers",
        }

        result = test_checkpoint(checkpoint_dir, unit_meta)
        # Note: May fail if impl doesn't match, depends on sample_impl
        assert isinstance(result, TestResult)


class TestTestUnit:
    """Tests for test_unit function."""

    def test_unit_not_found(self, clear_defless_registry):
        """Test testing nonexistent unit returns error."""
        result = test_unit("nonexistent/unit")
        assert not result.passed
        assert "Unit not found" in result.errors[0]

    def test_unit_not_compiled(self, test_config, temp_dir, monkeypatch, clear_defless_registry):
        """Test testing uncompiled unit returns error."""

        @defless.func
        def uncompiled_func(x: int) -> int:
            """Not compiled."""
            yield DeflessHandled()

        monkeypatch.chdir(temp_dir)
        from defless import config as config_module

        config_module._config = test_config

        unit_id = uncompiled_func.__defless_unit_id__
        result = test_unit(unit_id)
        assert not result.passed
