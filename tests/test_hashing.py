"""
Tests for defless.hashing module.
"""

import pytest

from defless.hashing import (
    compute_checkpoint_hash,
    compute_dependency_digest,
    compute_prompt_hash,
    compute_spec_hash,
    hash_code,
    normalize_docstring,
    short_hash,
)


class TestComputeSpecHash:
    """Tests for compute_spec_hash."""

    def test_basic_spec_hash(self):
        """Test basic spec hash computation."""
        hash_val = compute_spec_hash(
            signature="def foo(x: int) -> int",
            docstring="Test function",
            body_before_handled="x = x + 1",
            template_id="function.j2",
            provider_model="gpt-4o-mini",
            dependency_digest="",
        )
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA256 hex digest

    def test_same_inputs_same_hash(self):
        """Test that same inputs produce same hash."""
        params = {
            "signature": "def bar(a: str) -> str",
            "docstring": "Bar function",
            "body_before_handled": "a = a.upper()",
            "template_id": "function.j2",
            "provider_model": "gpt-4o-mini",
            "dependency_digest": "",
        }

        hash1 = compute_spec_hash(**params)
        hash2 = compute_spec_hash(**params)
        assert hash1 == hash2

    def test_different_signature_different_hash(self):
        """Test that different signatures produce different hashes."""
        base_params = {
            "signature": "def foo(x: int) -> int",
            "docstring": "Test",
            "body_before_handled": "",
            "template_id": "function.j2",
            "provider_model": "gpt-4o-mini",
            "dependency_digest": "",
        }

        hash1 = compute_spec_hash(**base_params)

        modified_params = base_params.copy()
        modified_params["signature"] = "def foo(x: int, y: int) -> int"
        hash2 = compute_spec_hash(**modified_params)

        assert hash1 != hash2

    def test_different_docstring_different_hash(self):
        """Test that different docstrings produce different hashes."""
        base_params = {
            "signature": "def foo(x: int) -> int",
            "docstring": "Original docstring",
            "body_before_handled": "",
            "template_id": "function.j2",
            "provider_model": "gpt-4o-mini",
            "dependency_digest": "",
        }

        hash1 = compute_spec_hash(**base_params)

        modified_params = base_params.copy()
        modified_params["docstring"] = "Modified docstring"
        hash2 = compute_spec_hash(**modified_params)

        assert hash1 != hash2

    def test_different_model_different_hash(self):
        """Test that different models produce different hashes."""
        base_params = {
            "signature": "def foo(x: int) -> int",
            "docstring": "Test",
            "body_before_handled": "",
            "template_id": "function.j2",
            "provider_model": "gpt-4o-mini",
            "dependency_digest": "",
        }

        hash1 = compute_spec_hash(**base_params)

        modified_params = base_params.copy()
        modified_params["provider_model"] = "gpt-4"
        hash2 = compute_spec_hash(**modified_params)

        assert hash1 != hash2

    def test_with_dependencies(self):
        """Test spec hash with dependencies."""
        hash_with_deps = compute_spec_hash(
            signature="def foo(x: int) -> int",
            docstring="Test",
            body_before_handled="",
            template_id="function.j2",
            provider_model="gpt-4o-mini",
            dependency_digest="abc123",
        )

        hash_without_deps = compute_spec_hash(
            signature="def foo(x: int) -> int",
            docstring="Test",
            body_before_handled="",
            template_id="function.j2",
            provider_model="gpt-4o-mini",
            dependency_digest="",
        )

        assert hash_with_deps != hash_without_deps


class TestComputeCheckpointHash:
    """Tests for compute_checkpoint_hash."""

    def test_basic_checkpoint_hash(self):
        """Test basic checkpoint hash computation."""
        hash_val = compute_checkpoint_hash(
            spec_hash="abc123",
            prompt_hash="def456",
            generated_code="def foo(): pass",
        )
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64

    def test_same_inputs_same_checkpoint_hash(self):
        """Test deterministic checkpoint hashing."""
        hash1 = compute_checkpoint_hash("spec1", "prompt1", "code1")
        hash2 = compute_checkpoint_hash("spec1", "prompt1", "code1")
        assert hash1 == hash2

    def test_different_code_different_hash(self):
        """Test different code produces different hash."""
        hash1 = compute_checkpoint_hash("spec1", "prompt1", "code1")
        hash2 = compute_checkpoint_hash("spec1", "prompt1", "code2")
        assert hash1 != hash2


class TestComputePromptHash:
    """Tests for compute_prompt_hash."""

    def test_basic_prompt_hash(self):
        """Test basic prompt hash computation."""
        hash_val = compute_prompt_hash("This is a prompt")
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64

    def test_same_prompt_same_hash(self):
        """Test same prompt produces same hash."""
        prompt = "Generate a function that adds two numbers"
        hash1 = compute_prompt_hash(prompt)
        hash2 = compute_prompt_hash(prompt)
        assert hash1 == hash2

    def test_different_prompt_different_hash(self):
        """Test different prompts produce different hashes."""
        hash1 = compute_prompt_hash("Prompt 1")
        hash2 = compute_prompt_hash("Prompt 2")
        assert hash1 != hash2


class TestComputeDependencyDigest:
    """Tests for compute_dependency_digest."""

    def test_empty_dependencies(self):
        """Test empty dependencies returns empty string."""
        digest = compute_dependency_digest({})
        assert digest == ""

    def test_single_dependency(self):
        """Test single dependency digest."""
        deps = {"helper": "def helper(x): return x + 1"}
        digest = compute_dependency_digest(deps)
        assert isinstance(digest, str)
        assert len(digest) == 64

    def test_multiple_dependencies(self):
        """Test multiple dependencies."""
        deps = {
            "helper1": "def helper1(x): return x + 1",
            "helper2": "def helper2(x): return x * 2",
        }
        digest = compute_dependency_digest(deps)
        assert isinstance(digest, str)
        assert len(digest) == 64

    def test_dependencies_order_independent(self):
        """Test that dependency order doesn't matter."""
        deps1 = {"a": "code_a", "b": "code_b", "c": "code_c"}
        deps2 = {"c": "code_c", "a": "code_a", "b": "code_b"}

        digest1 = compute_dependency_digest(deps1)
        digest2 = compute_dependency_digest(deps2)
        assert digest1 == digest2

    def test_different_dependencies_different_digest(self):
        """Test different dependencies produce different digests."""
        deps1 = {"helper": "def helper(x): return x + 1"}
        deps2 = {"helper": "def helper(x): return x + 2"}

        digest1 = compute_dependency_digest(deps1)
        digest2 = compute_dependency_digest(deps2)
        assert digest1 != digest2


class TestNormalizeDocstring:
    """Tests for normalize_docstring."""

    def test_empty_docstring(self):
        """Test empty docstring."""
        assert normalize_docstring("") == ""
        assert normalize_docstring(None) == ""  # type: ignore

    def test_strip_whitespace(self):
        """Test stripping leading/trailing whitespace."""
        docstring = "   Test docstring   "
        normalized = normalize_docstring(docstring)
        assert normalized == "Test docstring"

    def test_dedent_indentation(self):
        """Test dedenting indented docstring."""
        docstring = """
        This is a docstring.
        With multiple lines.
        """
        normalized = normalize_docstring(docstring)
        assert normalized.startswith("This is a docstring.")
        assert "With multiple lines." in normalized

    def test_same_content_same_normalized(self):
        """Test that similar docstrings normalize to same value."""
        doc1 = "Test function"
        doc2 = "   Test function   "
        assert normalize_docstring(doc1) == normalize_docstring(doc2)


class TestShortHash:
    """Tests for short_hash."""

    def test_default_length(self):
        """Test default short hash length."""
        full_hash = "abcdef1234567890" * 4  # 64 chars
        short = short_hash(full_hash)
        assert len(short) == 8
        assert short == "abcdef12"

    def test_custom_length(self):
        """Test custom short hash length."""
        full_hash = "abcdef1234567890" * 4
        short = short_hash(full_hash, length=16)
        assert len(short) == 16
        assert short == "abcdef1234567890"

    def test_short_hash_preserves_start(self):
        """Test that short hash preserves start of full hash."""
        full_hash = "fedcba9876543210" * 4
        short = short_hash(full_hash, length=10)
        assert short == "fedcba9876"


class TestHashCode:
    """Tests for hash_code."""

    def test_basic_code_hash(self):
        """Test basic code hashing."""
        code = "def foo(): pass"
        hash_val = hash_code(code)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64

    def test_same_code_same_hash(self):
        """Test same code produces same hash."""
        code = "def bar(x): return x + 1"
        hash1 = hash_code(code)
        hash2 = hash_code(code)
        assert hash1 == hash2

    def test_different_code_different_hash(self):
        """Test different code produces different hash."""
        hash1 = hash_code("def foo(): pass")
        hash2 = hash_code("def bar(): pass")
        assert hash1 != hash2

    def test_whitespace_matters(self):
        """Test that whitespace affects hash."""
        hash1 = hash_code("def foo(): pass")
        hash2 = hash_code("def foo():  pass")  # Extra space
        assert hash1 != hash2
