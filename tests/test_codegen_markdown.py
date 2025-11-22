"""
Tests for markdown code block stripping in codegen.
"""

from unittest.mock import Mock, patch

import pytest

from vibesafe.codegen import CodeGenerator


class TestMarkdownStripping:
    """Test markdown code block removal from AI-generated code."""

    def test_clean_generated_code_with_markdown_blocks(self):
        """Test that markdown code blocks are stripped correctly."""
        generator = self._create_generator()

        # Test with ```python block
        code_with_python_block = """```python
def test_func():
    return 42
```"""
        cleaned = generator._clean_generated_code(code_with_python_block)
        assert cleaned == "def test_func():\n    return 42"

        # Test with plain ``` block
        code_with_plain_block = """```
def another_func():
    return "hello"
```"""
        cleaned = generator._clean_generated_code(code_with_plain_block)
        assert cleaned == 'def another_func():\n    return "hello"'

    def test_clean_generated_code_without_markdown(self):
        """Test that code without markdown blocks is preserved."""
        generator = self._create_generator()

        clean_code = '''def clean_func():
    """This is already clean."""
    return True'''

        cleaned = generator._clean_generated_code(clean_code)
        assert cleaned == clean_code

    def test_clean_generated_code_with_extra_whitespace(self):
        """Test that extra whitespace is trimmed."""
        generator = self._create_generator()

        code_with_whitespace = """

def whitespace_func():
    return 1

"""
        cleaned = generator._clean_generated_code(code_with_whitespace)
        assert cleaned == "def whitespace_func():\n    return 1"

    def test_clean_generated_code_with_markdown_and_whitespace(self):
        """Test handling of markdown blocks with extra whitespace."""
        generator = self._create_generator()

        messy_code = """

```python

def messy_func():
    return "cleaned"

```

"""
        cleaned = generator._clean_generated_code(messy_code)
        assert cleaned == 'def messy_func():\n    return "cleaned"'

    def test_clean_generated_code_with_nested_backticks(self):
        """Test handling of code that contains backticks in strings."""
        generator = self._create_generator()

        code_with_nested = '''```python
def backtick_func():
    """This has `backticks` in docstring."""
    return "`code`"
```'''
        cleaned = generator._clean_generated_code(code_with_nested)
        assert 'return "`code`"' in cleaned
        assert '"""This has `backticks` in docstring."""' in cleaned

    def test_clean_generated_code_empty_markdown_block(self):
        """Test handling of empty markdown blocks."""
        generator = self._create_generator()

        empty_block = """```python
```"""
        cleaned = generator._clean_generated_code(empty_block)
        assert cleaned == ""

    def test_clean_generated_code_multiline_complex(self):
        """Test complex multiline function with markdown."""
        generator = self._create_generator()

        complex_code = '''```python
def complex_func(a: int, b: str) -> dict:
    """
    A complex function with multiple lines.

    Args:
        a: An integer
        b: A string

    Returns:
        A dictionary
    """
    result = {
        "number": a,
        "text": b,
        "combined": f"{a}: {b}"
    }

    if a > 10:
        result["big"] = True

    return result
```'''
        cleaned = generator._clean_generated_code(complex_code)

        # Check key parts are preserved
        assert "def complex_func(a: int, b: str) -> dict:" in cleaned
        assert '"""' in cleaned
        assert "result = {" in cleaned
        assert 'result["big"] = True' in cleaned
        assert "return result" in cleaned
        # Check markdown is removed
        assert "```" not in cleaned

    def _create_generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance for testing."""
        # Create a mock unit with minimal required attributes
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.__module__ = "test_module"

        unit_meta = {"func": mock_func, "type": "function", "provider": "default"}

        # Mock the config and provider
        with (
            patch("vibesafe.codegen.get_config") as mock_config,
            patch("vibesafe.codegen.get_provider") as mock_provider,
            patch("vibesafe.codegen.extract_spec") as mock_extract,
        ):
            # Setup mock config
            mock_cfg = Mock()
            mock_cfg.get_provider.return_value = Mock(
                model="test-model", seed=42, timeout=60, reasoning_effort=None
            )
            mock_config.return_value = mock_cfg

            # Setup mock spec
            mock_extract.return_value = {
                "signature": "def test_func(): pass",
                "docstring": "Test function",
                "body_before_handled": "",
                "doctests": [">>> test_func()\nNone"],
                "dependencies": {},
            }

            return CodeGenerator("test_module/test_func", unit_meta)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
