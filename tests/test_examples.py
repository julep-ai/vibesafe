"""
Tests for the example code in examples/ directory.
"""

import sys
from pathlib import Path

import pytest

# Add examples to path
examples_dir = Path(__file__).parent.parent / "examples"
if str(examples_dir) not in sys.path:
    sys.path.insert(0, str(examples_dir))


@pytest.mark.integration
class TestMathExamples:
    """Tests for examples/math/ops.py."""

    def test_sum_str_definition(self, clear_defless_registry):
        """Test sum_str function is properly defined."""
        from examples.math.ops import sum_str

        assert hasattr(sum_str, "__vibesafe_unit_id__")
        assert hasattr(sum_str, "__vibesafe_type__")
        assert sum_str.__vibesafe_type__ == "function"

    def test_fibonacci_definition(self, clear_defless_registry):
        """Test fibonacci function is properly defined."""
        from examples.math.ops import fibonacci

        assert hasattr(fibonacci, "__vibesafe_unit_id__")
        assert fibonacci.__vibesafe_type__ == "function"

    def test_is_prime_definition(self, clear_defless_registry):
        """Test is_prime function is properly defined."""
        from examples.math.ops import is_prime

        assert hasattr(is_prime, "__vibesafe_unit_id__")
        assert is_prime.__vibesafe_type__ == "function"

    def test_sum_str_spec(self, clear_defless_registry):
        """Test sum_str has correct spec."""
        from examples.math.ops import sum_str
        from vibesafe.ast_parser import extract_spec

        spec = extract_spec(sum_str)
        assert "sum_str" in spec["signature"]
        assert "a: str" in spec["signature"]
        assert "b: str" in spec["signature"]
        assert len(spec["doctests"]) >= 2

    def test_fibonacci_spec(self, clear_defless_registry):
        """Test fibonacci has correct spec."""
        from examples.math.ops import fibonacci
        from vibesafe.ast_parser import extract_spec

        spec = extract_spec(fibonacci)
        assert "fibonacci" in spec["signature"]
        assert "n: int" in spec["signature"]
        assert len(spec["doctests"]) >= 3

    def test_is_prime_spec(self, clear_defless_registry):
        """Test is_prime has correct spec."""
        from examples.math.ops import is_prime
        from vibesafe.ast_parser import extract_spec

        spec = extract_spec(is_prime)
        assert "is_prime" in spec["signature"]
        assert "n: int" in spec["signature"]
        assert "bool" in spec["signature"]
        assert len(spec["doctests"]) >= 3


@pytest.mark.integration
class TestAPIExamples:
    """Tests for examples/api/routes.py."""

    def test_sum_endpoint_definition(self, clear_defless_registry):
        """Test sum_endpoint is properly defined."""
        from examples.api.routes import sum_endpoint

        assert hasattr(sum_endpoint, "__vibesafe_unit_id__")
        assert sum_endpoint.__vibesafe_type__ == "http"
        assert sum_endpoint.__vibesafe_method__ == "POST"
        assert sum_endpoint.__vibesafe_path__ == "/sum"

    def test_hello_endpoint_definition(self, clear_defless_registry):
        """Test hello_endpoint is properly defined."""
        from examples.api.routes import hello_endpoint

        assert hasattr(hello_endpoint, "__vibesafe_unit_id__")
        assert hello_endpoint.__vibesafe_type__ == "http"
        assert hello_endpoint.__vibesafe_method__ == "GET"
        assert hello_endpoint.__vibesafe_path__ == "/hello/{name}"

    def test_sum_endpoint_spec(self, clear_defless_registry):
        """Test sum_endpoint has correct spec."""
        from examples.api.routes import sum_endpoint
        from vibesafe.ast_parser import extract_spec

        spec = extract_spec(sum_endpoint)
        assert "sum_endpoint" in spec["signature"]
        assert "async" in spec["signature"]
        assert "a: int" in spec["signature"]
        assert "b: int" in spec["signature"]

    def test_hello_endpoint_spec(self, clear_defless_registry):
        """Test hello_endpoint has correct spec."""
        from examples.api.routes import hello_endpoint
        from vibesafe.ast_parser import extract_spec

        spec = extract_spec(hello_endpoint)
        assert "hello_endpoint" in spec["signature"]
        assert "async" in spec["signature"]
        assert "name: str" in spec["signature"]


@pytest.mark.integration
class TestExampleRegistry:
    """Test that examples are registered correctly."""

    def test_all_examples_registered(self):
        """Test that all example functions are registered."""
        # Examples are imported at module level, so they should be registered
        from vibesafe.core import vibesafe

        registry = vibesafe.get_registry()

        # Should have at least 5 units (3 math + 2 api)
        assert len(registry) >= 5

        # Check some are present
        unit_ids = list(registry.keys())
        assert any("sum_str" in uid for uid in unit_ids)
        assert any("fibonacci" in uid for uid in unit_ids)
        assert any("is_prime" in uid for uid in unit_ids)

    def test_example_types(self):
        """Test example function types."""
        from vibesafe.core import vibesafe

        registry = vibesafe.get_registry()

        # Count function vs http types
        func_count = sum(1 for meta in registry.values() if meta["type"] == "function")
        http_count = sum(1 for meta in registry.values() if meta["type"] == "http")

        assert func_count >= 3
        assert http_count >= 2
