"""
Integration tests for defless end-to-end workflows.
"""

import pytest

from defless import DeflessHandled, defless


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Integration tests for complete defless workflow."""

    def test_complete_function_workflow(
        self, test_config, temp_dir, monkeypatch, clear_defless_registry, mocker
    ):
        """Test complete workflow: define -> compile -> test -> load."""
        monkeypatch.chdir(temp_dir)
        from defless import config as config_module

        config_module._config = test_config

        # Step 1: Define a function
        @defless.func
        def multiply(a: int, b: int) -> int:
            """
            Multiply two numbers.

            >>> multiply(3, 4)
            12
            >>> multiply(5, 2)
            10
            """
            yield DeflessHandled()

        unit_id = multiply.__defless_unit_id__

        # Mock LLM provider
        mock_provider = mocker.MagicMock()
        mock_provider.complete.return_value = """
def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two numbers.\"\"\"
    return a * b
"""

        # Step 2: Generate code
        from defless.codegen import CodeGenerator

        unit_meta = defless.get_unit(unit_id)
        generator = CodeGenerator(unit_id, unit_meta)
        generator.provider = mock_provider

        checkpoint_info = generator.generate()
        assert checkpoint_info["impl_path"].exists()

        # Step 3: Update index
        from defless.runtime import update_index

        update_index(unit_id, checkpoint_info["spec_hash"])

        # Step 4: Test implementation
        from defless.testing import test_unit

        result = test_unit(unit_id)
        assert result.passed

        # Step 5: Load and use
        from defless.runtime import load_active

        impl = load_active(unit_id, verify_hash=False)
        assert impl(3, 4) == 12
        assert impl(5, 2) == 10

    @pytest.mark.integration
    def test_http_endpoint_workflow(
        self, test_config, temp_dir, monkeypatch, clear_defless_registry, mocker
    ):
        """Test HTTP endpoint workflow."""
        monkeypatch.chdir(temp_dir)
        from defless import config as config_module

        config_module._config = test_config

        # Define endpoint
        @defless.http(method="POST", path="/double")
        async def double_endpoint(value: int) -> dict[str, int]:
            """
            Double a number.

            >>> import anyio
            >>> anyio.run(double_endpoint, 5)
            {'result': 10}
            """
            return DeflessHandled()

        unit_id = double_endpoint.__defless_unit_id__
        assert defless.get_unit(unit_id)["type"] == "http"

    @pytest.mark.integration
    def test_multiple_functions_workflow(
        self, test_config, temp_dir, monkeypatch, clear_defless_registry
    ):
        """Test workflow with multiple functions."""
        monkeypatch.chdir(temp_dir)
        from defless import config as config_module

        config_module._config = test_config

        # Define multiple functions
        @defless.func
        def func_a(x: int) -> int:
            """Function A."""
            yield DeflessHandled()

        @defless.func
        def func_b(x: str) -> str:
            """Function B."""
            yield DeflessHandled()

        @defless.func
        def func_c(x: float) -> float:
            """Function C."""
            yield DeflessHandled()

        registry = defless.get_registry()
        assert len([u for u in registry if "func_a" in u or "func_b" in u or "func_c" in u]) >= 3

    @pytest.mark.integration
    def test_config_loading_workflow(self, temp_dir, monkeypatch):
        """Test configuration loading from file."""
        # Create config file
        config_content = """
[project]
python = ">=3.12"
env = "dev"

[provider.default]
kind = "openai-compatible"
model = "gpt-4"
api_key_env = "OPENAI_API_KEY"

[provider.custom]
kind = "openai-compatible"
model = "custom-model"
api_key_env = "CUSTOM_API_KEY"
"""
        config_path = temp_dir / "defless.toml"
        config_path.write_text(config_content)

        monkeypatch.chdir(temp_dir)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CUSTOM_API_KEY", "custom-key")

        from defless.config import DeflessConfig

        config = DeflessConfig.load()
        assert config.provider["default"].model == "gpt-4"
        assert config.provider["custom"].model == "custom-model"

    @pytest.mark.integration
    def test_spec_extraction_workflow(self, clear_defless_registry):
        """Test spec extraction from decorated function."""

        @defless.func
        def example_func(a: int, b: int, c: str = "default") -> str:
            """
            Example function with parameters.

            >>> example_func(1, 2)
            'result'
            >>> example_func(1, 2, "custom")
            'result'
            """
            result = a + b
            yield DeflessHandled()

        from defless.ast_parser import extract_spec

        spec = extract_spec(example_func)

        assert "def example_func" in spec["signature"]
        assert "a: int" in spec["signature"]
        assert "Example function" in spec["docstring"]
        assert len(spec["doctests"]) == 2

    @pytest.mark.integration
    def test_hash_computation_workflow(self):
        """Test hash computation for spec and checkpoint."""
        from defless.hashing import (
            compute_checkpoint_hash,
            compute_prompt_hash,
            compute_spec_hash,
        )

        # Compute spec hash
        spec_hash = compute_spec_hash(
            signature="def foo(x: int) -> int",
            docstring="Test function",
            body_before_handled="x = x + 1",
            template_id="function.j2",
            provider_model="gpt-4o-mini",
            dependency_digest="",
        )

        # Compute prompt hash
        prompt = "Generate code for foo"
        prompt_hash = compute_prompt_hash(prompt)

        # Compute checkpoint hash
        generated_code = "def foo(x: int) -> int:\n    return x + 1"
        chk_hash = compute_checkpoint_hash(spec_hash, prompt_hash, generated_code)

        assert len(spec_hash) == 64
        assert len(prompt_hash) == 64
        assert len(chk_hash) == 64
        assert spec_hash != prompt_hash != chk_hash

    @pytest.mark.integration
    def test_shim_generation_workflow(self, test_config, temp_dir, monkeypatch):
        """Test shim generation and writing."""
        monkeypatch.chdir(temp_dir)
        from defless import config as config_module

        config_module._config = test_config

        from defless.runtime import build_shim, write_shim

        # Build shim
        shim_code = build_shim("app.math.ops/add_func")
        assert "load_active" in shim_code
        assert "add_func" in shim_code

        # Write shim
        shim_path = write_shim("app.math.ops/add_func")
        assert shim_path.exists()
        assert shim_path.read_text() == shim_code

    @pytest.mark.integration
    def test_index_management_workflow(self, test_config, temp_dir, monkeypatch):
        """Test index creation and updates."""
        monkeypatch.chdir(temp_dir)
        from defless import config as config_module

        config_module._config = test_config

        from defless.runtime import update_index

        # Update multiple units
        update_index("unit1/func1", "hash1")
        update_index("unit2/func2", "hash2")
        update_index("unit3/func3", "hash3")

        # Verify index
        index_path = temp_dir / ".defless" / "index.toml"
        assert index_path.exists()

        content = index_path.read_text()
        assert "unit1/func1" in content
        assert "hash1" in content
        assert "unit2/func2" in content
        assert "hash2" in content

        # Update existing
        update_index("unit1/func1", "new_hash1")
        content = index_path.read_text()
        assert "new_hash1" in content


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling."""

    def test_missing_api_key_error(self, test_config, monkeypatch):
        """Test error when API key is missing."""
        monkeypatch.delenv("TEST_API_KEY", raising=False)

        with pytest.raises(ValueError, match="API key not found"):
            test_config.get_api_key()

    def test_checkpoint_not_found_error(self, test_config, temp_dir, monkeypatch):
        """Test error when checkpoint not found."""
        monkeypatch.chdir(temp_dir)
        from defless import config as config_module

        config_module._config = test_config

        from defless.runtime import CheckpointNotFoundError, load_active

        with pytest.raises(CheckpointNotFoundError):
            load_active("nonexistent/unit")

    def test_uncompiled_function_error(self, clear_defless_registry):
        """Test error when calling uncompiled function."""

        @defless.func
        def uncompiled(x: int) -> int:
            """Not compiled."""
            yield DeflessHandled()

        with pytest.raises(RuntimeError, match="has not been compiled yet"):
            uncompiled(5)
