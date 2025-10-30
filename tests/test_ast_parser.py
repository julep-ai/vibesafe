"""Tests for vibesafe.ast_parser module."""

from vibesafe import VibesafeHandled, vibesafe
from vibesafe.ast_parser import SpecExtractor, extract_spec


def helper_dependency(value: int) -> int:
    """Helper function for dependency extraction tests."""
    return value + 1


class TestSpecExtractor:
    """Tests for SpecExtractor class."""

    def test_extract_signature_basic(self, clear_defless_registry):
        """Test extracting basic function signature."""

        def test_func(a: int, b: str) -> int:
            """Test."""
            pass

        extractor = SpecExtractor(test_func)
        signature = extractor.extract_signature()
        assert "def test_func" in signature
        assert "a: int" in signature
        assert "b: str" in signature
        assert "-> int" in signature

    def test_extract_signature_async(self, clear_defless_registry):
        """Test extracting async function signature."""

        async def async_func(x: int) -> str:
            """Async test."""
            pass

        extractor = SpecExtractor(async_func)
        signature = extractor.extract_signature()
        assert "async def async_func" in signature

    def test_extract_docstring(self, clear_defless_registry):
        """Test extracting docstring."""

        def documented_func():
            """This is a docstring with details."""
            pass

        extractor = SpecExtractor(documented_func)
        docstring = extractor.extract_docstring()
        assert docstring == "This is a docstring with details."

    def test_extract_docstring_multiline(self, clear_defless_registry):
        """Test extracting multiline docstring."""

        def multiline_func():
            """
            First line.
            Second line.
            Third line.
            """
            pass

        extractor = SpecExtractor(multiline_func)
        docstring = extractor.extract_docstring()
        assert "First line." in docstring
        assert "Second line." in docstring

    def test_extract_body_before_handled(self, clear_defless_registry):
        """Test extracting body before VibesafeHandled."""

        @vibesafe.func
        def body_func(x: int) -> int:
            """Test."""
            x = x + 1
            y = x * 2
            yield VibesafeHandled()

        extractor = SpecExtractor(body_func)
        body = extractor.extract_body_before_handled()
        assert "x = x + 1" in body or "x+1" in body.replace(" ", "")

    def test_extract_doctests(self, clear_defless_registry):
        """Test extracting doctest examples."""

        def doctest_func(x: int) -> int:
            """
            Add one.

            >>> doctest_func(5)
            6
            >>> doctest_func(10)
            11
            """
            return x + 1

        extractor = SpecExtractor(doctest_func)
        examples = extractor.extract_doctests()
        assert len(examples) == 2
        assert "doctest_func(5)" in examples[0].source
        assert "6" in examples[0].want

    def test_extract_dependencies(self, clear_defless_registry):
        """Test extracting dependencies."""

        @vibesafe.func
        def dep_func(x: int) -> int:
            """Test."""
            helper_dependency(x)
            yield VibesafeHandled()

        extractor = SpecExtractor(dep_func)
        deps = extractor.extract_dependencies()
        assert "helper_dependency" in deps
        assert "return value + 1" in deps["helper_dependency"]

    def test_to_dict(self, clear_defless_registry):
        """Test converting extraction to dictionary."""

        @vibesafe.func
        def complete_func(a: int, b: int) -> int:
            """
            Add two numbers.

            >>> complete_func(2, 3)
            5
            """
            yield VibesafeHandled()

        extractor = SpecExtractor(complete_func)
        spec_dict = extractor.to_dict()

        assert "signature" in spec_dict
        assert "docstring" in spec_dict
        assert "body_before_handled" in spec_dict
        assert "doctests" in spec_dict
        assert "dependencies" in spec_dict
        assert "source" in spec_dict


class TestExtractSpec:
    """Tests for extract_spec convenience function."""

    def test_extract_spec_basic(self, clear_defless_registry):
        """Test extract_spec convenience function."""

        def simple_func(x: int) -> int:
            """Simple."""
            return x

        spec = extract_spec(simple_func)
        assert isinstance(spec, dict)
        assert "signature" in spec
        assert "docstring" in spec

    def test_extract_spec_with_doctests(self, clear_defless_registry):
        """Test extracting spec with doctests."""

        def tested_func(x: int) -> int:
            """
            Multiply by 2.

            >>> tested_func(5)
            10
            """
            return x * 2

        spec = extract_spec(tested_func)
        assert len(spec["doctests"]) == 1
